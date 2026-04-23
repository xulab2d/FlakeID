param(
    [string]$Config = "",
    [switch]$SelfTest
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Config) {
    $Config = Join-Path $repoRoot "configs\lab.example.toml"
}
elseif (-not [System.IO.Path]::IsPathRooted($Config)) {
    $Config = Join-Path $repoRoot $Config
}

function ConvertFrom-TomlScalar {
    param([string]$Value)
    $trimmed = $Value.Trim()
    if ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) {
        return $trimmed.Substring(1, $trimmed.Length - 2)
    }
    if ($trimmed -eq "true") { return $true }
    if ($trimmed -eq "false") { return $false }
    if ($trimmed -match '^-?\d+$') { return [int]$trimmed }
    if ($trimmed -match '^-?\d+(\.\d+)?$') { return [double]$trimmed }
    return $trimmed
}

function Format-TomlValue {
    param($Value)
    if ($Value -is [bool]) { return $(if ($Value) { "true" } else { "false" }) }
    if ($Value -is [int] -or $Value -is [long]) { return [string]$Value }
    if ($Value -is [double] -or $Value -is [float] -or $Value -is [decimal]) {
        return ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0:0.###}", $Value))
    }
    $escaped = [string]$Value -replace '\\', '\\' -replace '"', '\"'
    return '"' + $escaped + '"'
}

function Get-ConfigValue {
    param(
        [string]$Path,
        [string]$Section,
        [string]$Key,
        $Default
    )
    $lines = Get-Content -LiteralPath $Path -ErrorAction Stop
    $inSection = $false
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^\[(.+)\]$') {
            $inSection = ($Matches[1] -eq $Section)
            continue
        }
        if (-not $inSection -or -not $trimmed -or $trimmed.StartsWith('#')) {
            continue
        }
        if ($trimmed -match "^$Key\s*=\s*(.+)$") {
            return ConvertFrom-TomlScalar $Matches[1]
        }
    }
    return $Default
}

function Set-ConfigValues {
    param(
        [string]$Path,
        [string]$Section,
        [hashtable]$Updates
    )

    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.AddRange([string[]](Get-Content -LiteralPath $Path -ErrorAction Stop))

    $sectionStart = -1
    $sectionEnd = $lines.Count
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $trimmed = $lines[$i].Trim()
        if ($trimmed -match '^\[(.+)\]$') {
            if ($Matches[1] -eq $Section) {
                $sectionStart = $i
                continue
            }
            if ($sectionStart -ge 0) {
                $sectionEnd = $i
                break
            }
        }
    }

    if ($sectionStart -lt 0) {
        if ($lines.Count -gt 0 -and $lines[$lines.Count - 1].Trim()) {
            $lines.Add("")
        }
        $lines.Add("[$Section]")
        $sectionStart = $lines.Count - 1
        $sectionEnd = $lines.Count
    }

    $remaining = @{}
    foreach ($entry in $Updates.GetEnumerator()) {
        $remaining[$entry.Key] = $entry.Value
    }

    for ($i = $sectionStart + 1; $i -lt $sectionEnd; $i++) {
        $trimmed = $lines[$i].Trim()
        if ($trimmed -match '^([A-Za-z0-9_]+)\s*=') {
            $key = $Matches[1]
            if ($remaining.ContainsKey($key)) {
                $lines[$i] = "$key = $(Format-TomlValue $remaining[$key])"
                $remaining.Remove($key)
            }
        }
    }

    $insertAt = $sectionEnd
    foreach ($key in $remaining.Keys) {
        $lines.Insert($insertAt, "$key = $(Format-TomlValue $remaining[$key])")
        $insertAt++
    }

    [System.IO.File]::WriteAllText($Path, (($lines -join "`n") + "`n"))
}

function Invoke-GrblLines {
    param(
        [string]$Port,
        [int]$Baud,
        [int]$StartupDelayMs,
        [string[]]$Lines,
        [string]$WaitFor = "ok",
        [int]$TimeoutMs = 5000
    )

    $serial = $null
    try {
        $serial = New-Object System.IO.Ports.SerialPort $Port, $Baud, ([System.IO.Ports.Parity]::None), 8, ([System.IO.Ports.StopBits]::One)
        $serial.ReadTimeout = 250
        $serial.WriteTimeout = 1000
        $serial.DtrEnable = $false
        $serial.RtsEnable = $false
        $serial.Open()
        Start-Sleep -Milliseconds $StartupDelayMs

        $flushDeadline = [DateTime]::UtcNow.AddMilliseconds(200)
        while ([DateTime]::UtcNow -lt $flushDeadline) {
            $null = $serial.ReadExisting()
            Start-Sleep -Milliseconds 20
        }

        $responses = New-Object System.Collections.Generic.List[string]
        foreach ($line in $Lines) {
            if ($line -eq "?") {
                $serial.Write("?")
            }
            elseif ($line -eq "!") {
                $serial.Write("!")
            }
            elseif ($line -eq "~") {
                $serial.Write("~")
            }
            elseif ($line -eq "__CTRL_X__") {
                $serial.Write([char]24)
            }
            else {
                $serial.Write($line + "`r`n")
            }
            Start-Sleep -Milliseconds 80
        }

        $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
        while ([DateTime]::UtcNow -lt $deadline) {
            $chunk = $serial.ReadExisting()
            if ($chunk) {
                $responses.Add($chunk)
                $text = ($responses.ToArray() -join "")
                if ($WaitFor -eq "__NONE__") { break }
                if ($text.Contains($WaitFor)) { break }
            }
            Start-Sleep -Milliseconds 20
        }

        return ($responses.ToArray() -join "")
    }
    finally {
        if ($serial -and $serial.IsOpen) {
            $serial.Close()
        }
    }
}

function Get-GrblStatus {
    param(
        [string]$Port,
        [int]$Baud,
        [int]$StartupDelayMs
    )
    $raw = Invoke-GrblLines -Port $Port -Baud $Baud -StartupDelayMs $StartupDelayMs -Lines @("?") -WaitFor "<" -TimeoutMs 3000
    if ($raw -match '<([^,>]+),MPos:([-\d.]+),([-\d.]+),([-\d.]+),WPos:([-\d.]+),([-\d.]+),([-\d.]+)>') {
        return [pscustomobject]@{
            State = $Matches[1]
            MachineX = [double]$Matches[2]
            MachineY = [double]$Matches[3]
            MachineZ = [double]$Matches[4]
            WorkX = [double]$Matches[5]
            WorkY = [double]$Matches[6]
            WorkZ = [double]$Matches[7]
            Raw = $raw.Trim()
        }
    }
    throw "Could not parse GRBL status: $raw"
}

$port = [string](Get-ConfigValue -Path $Config -Section "motion" -Key "port" -Default "COM3")
$baud = [int](Get-ConfigValue -Path $Config -Section "motion" -Key "baud" -Default 115200)
$startupDelayMs = [int](Get-ConfigValue -Path $Config -Section "motion" -Key "startup_delay_ms" -Default 500)
$jogFeed = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "jog_feed_mm_min" -Default 30.0)
$xRate = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "x_max_rate_mm_min" -Default 60.0)
$yRate = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "y_max_rate_mm_min" -Default 60.0)
$xAccel = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "x_accel_mm_s2" -Default 2.0)
$yAccel = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "y_accel_mm_s2" -Default 2.0)
$minXUm = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "min_x_um" -Default 0.0)
$minYUm = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "min_y_um" -Default 0.0)
$maxXUm = Get-ConfigValue -Path $Config -Section "motion" -Key "max_x_um" -Default $null
$maxYUm = Get-ConfigValue -Path $Config -Section "motion" -Key "max_y_um" -Default $null
$safetyMarginUm = [double](Get-ConfigValue -Path $Config -Section "motion" -Key "safety_margin_um" -Default 1000.0)

$script:CurrentStatus = $null
$script:MinXUm = if ($null -eq $minXUm) { $null } else { [double]$minXUm }
$script:MinYUm = if ($null -eq $minYUm) { $null } else { [double]$minYUm }
$script:MaxXUm = if ($null -eq $maxXUm) { $null } else { [double]$maxXUm }
$script:MaxYUm = if ($null -eq $maxYUm) { $null } else { [double]$maxYUm }

$form = New-Object System.Windows.Forms.Form
$form.Text = "FlakeID Stage Calibration"
$form.Size = New-Object System.Drawing.Size(940, 760)
$form.StartPosition = "CenterScreen"

function New-Label {
    param([string]$Text, [int]$X, [int]$Y, [int]$W = 200, [int]$H = 24)
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Text
    $label.Location = New-Object System.Drawing.Point($X, $Y)
    $label.Size = New-Object System.Drawing.Size($W, $H)
    $form.Controls.Add($label)
    return $label
}

function New-TextBox {
    param([string]$Text, [int]$X, [int]$Y, [int]$W = 100, [int]$H = 24)
    $tb = New-Object System.Windows.Forms.TextBox
    $tb.Text = $Text
    $tb.Location = New-Object System.Drawing.Point($X, $Y)
    $tb.Size = New-Object System.Drawing.Size($W, $H)
    $form.Controls.Add($tb)
    return $tb
}

function New-Button {
    param([string]$Text, [int]$X, [int]$Y, [int]$W = 110, [int]$H = 32)
    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.Location = New-Object System.Drawing.Point($X, $Y)
    $button.Size = New-Object System.Drawing.Size($W, $H)
    $form.Controls.Add($button)
    return $button
}

$connectionLabel = New-Label "Config: $Config" 20 20 860 24
$portLabel = New-Label "Port: $port" 20 50 180 24
$baudLabel = New-Label "Baud: $baud" 220 50 180 24
$stateLabel = New-Label "State: --" 420 50 180 24
$machineLabel = New-Label "MPos: --" 20 80 280 24
$workLabel = New-Label "WPos: --" 320 80 280 24
$boundsLabel = New-Label "" 20 540 860 24
$rawLabel = New-Label "Raw controller text:" 20 580 200 24
$rawBox = New-Object System.Windows.Forms.TextBox
$rawBox.Multiline = $true
$rawBox.ScrollBars = "Vertical"
$rawBox.Location = New-Object System.Drawing.Point(20, 605)
$rawBox.Size = New-Object System.Drawing.Size(880, 110)
$form.Controls.Add($rawBox)

New-Label "Jog step (um)" 20 130 120 24 | Out-Null
$stepBox = New-TextBox "500" 150 128 100 24
New-Label "Jog feed (mm/min)" 280 130 130 24 | Out-Null
$feedBox = New-TextBox ([string]$jogFeed) 420 128 100 24

$refreshButton = New-Button "Refresh Status" 650 45 120 32
$unlockButton = New-Button "Unlock" 780 45 120 32

$plusYButton = New-Button "+Y" 150 185 120 36
$minusXButton = New-Button "-X" 20 230 120 36
$plusXButton = New-Button "+X" 280 230 120 36
$minusYButton = New-Button "-Y" 150 275 120 36

$feedHoldButton = New-Button "Feed Hold" 470 185 120 36
$resumeButton = New-Button "Resume" 600 185 120 36
$softResetButton = New-Button "Soft Reset" 730 185 120 36
$zeroButton = New-Button "Set Work Zero" 470 230 120 36

New-Label "X max rate (mm/min)" 20 350 140 24 | Out-Null
$xRateBox = New-TextBox ([string]$xRate) 170 348 100 24
New-Label "Y max rate (mm/min)" 300 350 140 24 | Out-Null
$yRateBox = New-TextBox ([string]$yRate) 450 348 100 24
New-Label "X accel (mm/s^2)" 20 385 140 24 | Out-Null
$xAccelBox = New-TextBox ([string]$xAccel) 170 383 100 24
New-Label "Y accel (mm/s^2)" 300 385 140 24 | Out-Null
$yAccelBox = New-TextBox ([string]$yAccel) 450 383 100 24
$applySettingsButton = New-Button "Apply Rates/Accel" 600 360 150 36

$markMinXButton = New-Button "Mark Min X" 20 465 120 36
$markMaxXButton = New-Button "Mark Max X" 150 465 120 36
$markMinYButton = New-Button "Mark Min Y" 280 465 120 36
$markMaxYButton = New-Button "Mark Max Y" 410 465 120 36
New-Label "Safety margin (um)" 560 470 120 24 | Out-Null
$marginBox = New-TextBox ([string]$safetyMarginUm) 690 468 90 24
$saveBoundsButton = New-Button "Save Bounds" 790 465 110 36

$notes = New-Label "Suggested start: feed 20-40 mm/min, max rate 40-80 mm/min, accel 1-3 mm/s^2. Mark bounds at backed-off safe points, not hard stops." 20 510 880 24
$notes.AutoSize = $false

function Update-BoundsLabel {
    $minXText = if ($null -eq $script:MinXUm) { "--" } else { "{0:N0} um" -f $script:MinXUm }
    $maxXText = if ($null -eq $script:MaxXUm) { "--" } else { "{0:N0} um" -f $script:MaxXUm }
    $minYText = if ($null -eq $script:MinYUm) { "--" } else { "{0:N0} um" -f $script:MinYUm }
    $maxYText = if ($null -eq $script:MaxYUm) { "--" } else { "{0:N0} um" -f $script:MaxYUm }
    $boundsLabel.Text = "Pending bounds: min_x=$minXText, max_x=$maxXText, min_y=$minYText, max_y=$maxYText"
}

function Refresh-Status {
    try {
        $status = Get-GrblStatus -Port $port -Baud $baud -StartupDelayMs $startupDelayMs
        $script:CurrentStatus = $status
        $stateLabel.Text = "State: $($status.State)"
        $machineLabel.Text = "MPos: {0:N3}, {1:N3} mm" -f $status.MachineX, $status.MachineY
        $workLabel.Text = "WPos: {0:N3}, {1:N3} mm" -f $status.WorkX, $status.WorkY
        $rawBox.Text = $status.Raw
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Status read failed: $($_.Exception.Message)")
    }
}

function Invoke-Jog {
    param([double]$XDirection, [double]$YDirection)
    try {
        $stepUm = [double]$stepBox.Text
        $feed = [double]$feedBox.Text
        $dxMm = ($XDirection * $stepUm) / 1000.0
        $dyMm = ($YDirection * $stepUm) / 1000.0
        $line = [string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "G1 X{0:0.####} Y{1:0.####} F{2:0.##}", $dxMm, $dyMm, $feed)
        $response = Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @("G21", "G91", $line) -WaitFor "ok" -TimeoutMs 6000
        if ($response) {
            if ($response -match "error: Expected command letter" -and $response -match "ok") {
                $rawBox.Text = "Controller accepted the jog, but also emitted a stray parse warning:`r`n$($response.Trim())"
            }
            else {
                $rawBox.Text = $response.Trim()
            }
        }
        Refresh-Status
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Jog failed: $($_.Exception.Message)")
    }
}

function Apply-ControllerSettings {
    try {
        $xRateValue = [double]$xRateBox.Text
        $yRateValue = [double]$yRateBox.Text
        $xAccelValue = [double]$xAccelBox.Text
        $yAccelValue = [double]$yAccelBox.Text

        $responses = @()
        $responses += Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @(('$110={0:0.###}' -f $xRateValue)) -WaitFor "ok" -TimeoutMs 4000
        $responses += Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @(('$111={0:0.###}' -f $yRateValue)) -WaitFor "ok" -TimeoutMs 4000
        $responses += Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @(('$120={0:0.###}' -f $xAccelValue)) -WaitFor "ok" -TimeoutMs 4000
        $responses += Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @(('$121={0:0.###}' -f $yAccelValue)) -WaitFor "ok" -TimeoutMs 4000
        $rawBox.Text = ($responses -join "`r`n").Trim()
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Applying settings failed: $($_.Exception.Message)")
    }
}

function Capture-Bound {
    param([string]$FieldName)
    if ($null -eq $script:CurrentStatus) {
        Refresh-Status
    }
    if ($null -eq $script:CurrentStatus) {
        return
    }
    switch ($FieldName) {
        "min_x_um" { $script:MinXUm = $script:CurrentStatus.MachineX * 1000.0 }
        "max_x_um" { $script:MaxXUm = $script:CurrentStatus.MachineX * 1000.0 }
        "min_y_um" { $script:MinYUm = $script:CurrentStatus.MachineY * 1000.0 }
        "max_y_um" { $script:MaxYUm = $script:CurrentStatus.MachineY * 1000.0 }
    }
    Update-BoundsLabel
}

function Save-BoundsAndSettings {
    if ($null -eq $script:MaxXUm -or $null -eq $script:MaxYUm) {
        [System.Windows.Forms.MessageBox]::Show("Capture both max bounds before saving.")
        return
    }
    try {
        $updates = @{
            jog_feed_mm_min = [double]$feedBox.Text
            travel_rate_um_s = [double]$feedBox.Text * (1000.0 / 60.0)
            x_max_rate_mm_min = [double]$xRateBox.Text
            y_max_rate_mm_min = [double]$yRateBox.Text
            x_accel_mm_s2 = [double]$xAccelBox.Text
            y_accel_mm_s2 = [double]$yAccelBox.Text
            min_x_um = [double]$script:MinXUm
            min_y_um = [double]$script:MinYUm
            max_x_um = [double]$script:MaxXUm
            max_y_um = [double]$script:MaxYUm
            safety_margin_um = [double]$marginBox.Text
            startup_delay_ms = $startupDelayMs
        }
        Set-ConfigValues -Path $Config -Section "motion" -Updates $updates
        [System.Windows.Forms.MessageBox]::Show("Saved bounds and motion values to $Config")
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Saving config failed: $($_.Exception.Message)")
    }
}

$refreshButton.Add_Click({ Refresh-Status })
$unlockButton.Add_Click({
    try {
        $rawBox.Text = (Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @('$X') -WaitFor "ok" -TimeoutMs 4000).Trim()
        Refresh-Status
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Unlock failed: $($_.Exception.Message)")
    }
})
$plusYButton.Add_Click({ Invoke-Jog -XDirection 0 -YDirection 1 })
$minusXButton.Add_Click({ Invoke-Jog -XDirection -1 -YDirection 0 })
$plusXButton.Add_Click({ Invoke-Jog -XDirection 1 -YDirection 0 })
$minusYButton.Add_Click({ Invoke-Jog -XDirection 0 -YDirection -1 })
$feedHoldButton.Add_Click({ [void](Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @('!') -WaitFor "__NONE__" -TimeoutMs 1000) })
$resumeButton.Add_Click({ [void](Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @('~') -WaitFor "__NONE__" -TimeoutMs 1000) })
$softResetButton.Add_Click({
    try {
        $rawBox.Text = (Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @('__CTRL_X__') -WaitFor "Grbl" -TimeoutMs 4000).Trim()
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Soft reset failed: $($_.Exception.Message)")
    }
})
$zeroButton.Add_Click({
    try {
        $rawBox.Text = (Invoke-GrblLines -Port $port -Baud $baud -StartupDelayMs $startupDelayMs -Lines @('G92 X0 Y0') -WaitFor "ok" -TimeoutMs 4000).Trim()
        Refresh-Status
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Setting work zero failed: $($_.Exception.Message)")
    }
})
$applySettingsButton.Add_Click({ Apply-ControllerSettings })
$markMinXButton.Add_Click({ Capture-Bound -FieldName "min_x_um" })
$markMaxXButton.Add_Click({ Capture-Bound -FieldName "max_x_um" })
$markMinYButton.Add_Click({ Capture-Bound -FieldName "min_y_um" })
$markMaxYButton.Add_Click({ Capture-Bound -FieldName "max_y_um" })
$saveBoundsButton.Add_Click({ Save-BoundsAndSettings })

Update-BoundsLabel

if ($SelfTest) {
    Write-Output "stage-calibration-ui-ok"
    return
}

[void]$form.ShowDialog()
