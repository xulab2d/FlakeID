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
$scanFovWidthUm = [double](Get-ConfigValue -Path $Config -Section "scan" -Key "fov_width_um" -Default 260.0)
$scanFovHeightUm = [double](Get-ConfigValue -Path $Config -Section "scan" -Key "fov_height_um" -Default 195.0)
$scanOverlapFraction = [double](Get-ConfigValue -Path $Config -Section "scan" -Key "overlap_fraction" -Default 0.12)
$scanPhotoRootDir = [string](Get-ConfigValue -Path $Config -Section "scan" -Key "photo_root_dir" -Default "photos/scans")
$scanAllowOutOfBounds = [bool](Get-ConfigValue -Path $Config -Section "scan" -Key "allow_out_of_bounds" -Default $false)
$scanRoiMinX = Get-ConfigValue -Path $Config -Section "scan" -Key "roi_min_x_um" -Default $null
$scanRoiMaxX = Get-ConfigValue -Path $Config -Section "scan" -Key "roi_max_x_um" -Default $null
$scanRoiMinY = Get-ConfigValue -Path $Config -Section "scan" -Key "roi_min_y_um" -Default $null
$scanRoiMaxY = Get-ConfigValue -Path $Config -Section "scan" -Key "roi_max_y_um" -Default $null
$cameraDriver = [string](Get-ConfigValue -Path $Config -Section "camera" -Key "driver" -Default "watched_folder")
$incomingDir = [string](Get-ConfigValue -Path $Config -Section "camera" -Key "incoming_dir" -Default "photos/incoming")
if (-not [System.IO.Path]::IsPathRooted($incomingDir)) {
    $incomingDir = Join-Path $repoRoot $incomingDir
}

$script:CurrentStatus = $null
$script:MinXUm = if ($null -eq $minXUm) { $null } else { [double]$minXUm }
$script:MinYUm = if ($null -eq $minYUm) { $null } else { [double]$minYUm }
$script:MaxXUm = if ($null -eq $maxXUm) { $null } else { [double]$maxXUm }
$script:MaxYUm = if ($null -eq $maxYUm) { $null } else { [double]$maxYUm }
$script:ScanMinXUm = if ($null -eq $scanRoiMinX) { $null } else { [double]$scanRoiMinX }
$script:ScanMaxXUm = if ($null -eq $scanRoiMaxX) { $null } else { [double]$scanRoiMaxX }
$script:ScanMinYUm = if ($null -eq $scanRoiMinY) { $null } else { [double]$scanRoiMinY }
$script:ScanMaxYUm = if ($null -eq $scanRoiMaxY) { $null } else { [double]$scanRoiMaxY }

$form = New-Object System.Windows.Forms.Form
$form.Text = "FlakeID Stage Control and Scan"
$form.Size = New-Object System.Drawing.Size(1040, 1125)
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
$boundsLabel = New-Label "" 20 540 980 24
$rawLabel = New-Label "Raw controller text:" 20 905 200 24
$rawBox = New-Object System.Windows.Forms.TextBox
$rawBox.Multiline = $true
$rawBox.ScrollBars = "Vertical"
$rawBox.Location = New-Object System.Drawing.Point(20, 930)
$rawBox.Size = New-Object System.Drawing.Size(980, 145)
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

$scanHeader = New-Label "Scan Setup" 20 585 200 24
New-Label "Sample ID" 20 620 80 24 | Out-Null
$sampleIdBox = New-TextBox "flake_grid_001" 105 618 170 24
New-Label "Material" 300 620 60 24 | Out-Null
$materialBox = New-TextBox "graphene" 365 618 120 24
New-Label "Substrate" 505 620 70 24 | Out-Null
$substrateBox = New-TextBox "graphene_285_wet" 580 618 170 24
New-Label "Objective" 770 620 60 24 | Out-Null
$objectiveBox = New-TextBox "10x" 835 618 70 24

New-Label "Operator" 20 655 80 24 | Out-Null
$operatorBox = New-TextBox "" 105 653 170 24
New-Label "FOV W (um)" 300 655 75 24 | Out-Null
$fovWidthBox = New-TextBox ([string]$scanFovWidthUm) 380 653 85 24
New-Label "FOV H (um)" 485 655 75 24 | Out-Null
$fovHeightBox = New-TextBox ([string]$scanFovHeightUm) 565 653 85 24
New-Label "Overlap" 670 655 55 24 | Out-Null
$overlapBox = New-TextBox ([string]$scanOverlapFraction) 730 653 70 24
$allowOutOfBoundsCheck = New-Object System.Windows.Forms.CheckBox
$allowOutOfBoundsCheck.Text = "Allow out-of-bounds scan"
$allowOutOfBoundsCheck.Checked = $scanAllowOutOfBounds
$allowOutOfBoundsCheck.Location = New-Object System.Drawing.Point(815, 653)
$allowOutOfBoundsCheck.Size = New-Object System.Drawing.Size(190, 24)
$form.Controls.Add($allowOutOfBoundsCheck)

New-Label "Photo root" 20 690 70 24 | Out-Null
$photoRootBox = New-TextBox $scanPhotoRootDir 105 688 800 24
New-Label "Incoming hot folder" 20 725 120 24 | Out-Null
$incomingBox = New-TextBox $incomingDir 145 723 760 24
$incomingBox.ReadOnly = $true

$markLeftEdgeButton = New-Button "Mark Left Edge" 20 765 120 36
$markRightEdgeButton = New-Button "Mark Right Edge" 150 765 120 36
$markTopEdgeButton = New-Button "Mark Top Edge" 280 765 120 36
$markBottomEdgeButton = New-Button "Mark Bottom Edge" 410 765 120 36
$saveScanButton = New-Button "Save Scan ROI" 540 765 120 36
$startScanButton = New-Button "Start Scan" 670 765 120 36
$scanLabel = New-Label "" 20 815 980 40
$scanLabel.AutoSize = $false
$scanStepLabel = New-Label "" 20 850 980 24
$scanStepLabel.AutoSize = $false
$scanNotes = New-Label "" 20 875 980 28
$scanNotes.AutoSize = $false

function Update-BoundsLabel {
    $minXText = if ($null -eq $script:MinXUm) { "--" } else { "{0:N0} um" -f $script:MinXUm }
    $maxXText = if ($null -eq $script:MaxXUm) { "--" } else { "{0:N0} um" -f $script:MaxXUm }
    $minYText = if ($null -eq $script:MinYUm) { "--" } else { "{0:N0} um" -f $script:MinYUm }
    $maxYText = if ($null -eq $script:MaxYUm) { "--" } else { "{0:N0} um" -f $script:MaxYUm }
    $boundsLabel.Text = "Pending bounds: min_x=$minXText, max_x=$maxXText, min_y=$minYText, max_y=$maxYText"
}

function Get-TileCount {
    param(
        [double]$ExtentUm,
        [double]$FovUm,
        [double]$OverlapFraction
    )
    if ($ExtentUm -le $FovUm) {
        return 1
    }
    $stepUm = $FovUm * (1.0 - $OverlapFraction)
    if ($stepUm -le 0.0) {
        throw "Overlap fraction must be less than 1.0."
    }
    return [int]([math]::Ceiling(($ExtentUm - $FovUm) / $stepUm) + 1)
}

function Get-ScanRoiSummary {
    if ($null -eq $script:ScanMinXUm -or $null -eq $script:ScanMaxXUm -or $null -eq $script:ScanMinYUm -or $null -eq $script:ScanMaxYUm) {
        return $null
    }

    return [pscustomobject]@{
        MinX = [double][math]::Min([double]$script:ScanMinXUm, [double]$script:ScanMaxXUm)
        MaxX = [double][math]::Max([double]$script:ScanMinXUm, [double]$script:ScanMaxXUm)
        MinY = [double][math]::Min([double]$script:ScanMinYUm, [double]$script:ScanMaxYUm)
        MaxY = [double][math]::Max([double]$script:ScanMinYUm, [double]$script:ScanMaxYUm)
    }
}

function Get-TextBoxDouble {
    param(
        [System.Windows.Forms.TextBox]$TextBox,
        [double]$Default
    )
    try {
        return [double]$TextBox.Text
    }
    catch {
        return $Default
    }
}

function Get-ScanRoiViolations {
    $roi = Get-ScanRoiSummary
    if ($null -eq $roi) {
        return @()
    }

    $marginUm = Get-TextBoxDouble -TextBox $marginBox -Default $safetyMarginUm
    $violations = @()

    if ($null -ne $script:MinXUm) {
        $safeMinX = [double]$script:MinXUm + $marginUm
        if ($roi.MinX -lt $safeMinX) {
            $violations += ("minimum X {0:N0} um is below safe minimum {1:N0} um" -f $roi.MinX, $safeMinX)
        }
    }
    if ($null -ne $script:MaxXUm) {
        $safeMaxX = [double]$script:MaxXUm - $marginUm
        if ($roi.MaxX -gt $safeMaxX) {
            $violations += ("maximum X {0:N0} um exceeds safe maximum {1:N0} um" -f $roi.MaxX, $safeMaxX)
        }
    }
    if ($null -ne $script:MinYUm) {
        $safeMinY = [double]$script:MinYUm + $marginUm
        if ($roi.MinY -lt $safeMinY) {
            $violations += ("minimum Y {0:N0} um is below safe minimum {1:N0} um" -f $roi.MinY, $safeMinY)
        }
    }
    if ($null -ne $script:MaxYUm) {
        $safeMaxY = [double]$script:MaxYUm - $marginUm
        if ($roi.MaxY -gt $safeMaxY) {
            $violations += ("maximum Y {0:N0} um exceeds safe maximum {1:N0} um" -f $roi.MaxY, $safeMaxY)
        }
    }

    return $violations
}

function Quote-ProcessArgument {
    param([string]$Value)
    if ($null -eq $Value) {
        return '""'
    }
    return '"' + ($Value -replace '"', '""') + '"'
}

function Update-ScanLabel {
    $fovWidthUm = [math]::Max((Get-TextBoxDouble -TextBox $fovWidthBox -Default $scanFovWidthUm), 1.0)
    $fovHeightUm = [math]::Max((Get-TextBoxDouble -TextBox $fovHeightBox -Default $scanFovHeightUm), 1.0)
    $overlap = Get-TextBoxDouble -TextBox $overlapBox -Default $scanOverlapFraction
    if ($overlap -lt 0.0) { $overlap = 0.0 }
    if ($overlap -ge 1.0) { $overlap = 0.95 }
    $stepXUm = [math]::Max($fovWidthUm * (1.0 - $overlap), 1.0)
    $stepYUm = [math]::Max($fovHeightUm * (1.0 - $overlap), 1.0)

    $scanStepLabel.Text = "Step size: X={0:N1} um, Y={1:N1} um from FOV {2:N1} x {3:N1} um and overlap {4:P0}. Increase overlap if backlash or registration uncertainty could leave gaps." -f $stepXUm, $stepYUm, $fovWidthUm, $fovHeightUm, $overlap

    if ($null -eq $script:ScanMinXUm -or $null -eq $script:ScanMaxXUm -or $null -eq $script:ScanMinYUm -or $null -eq $script:ScanMaxYUm) {
        $scanLabel.Text = "Pending scan ROI: mark left, right, top, and bottom edges, then start the scan."
    }
    else {
        $leftEdge = [double]$script:ScanMaxXUm
        $rightEdge = [double]$script:ScanMinXUm
        $topEdge = [double]$script:ScanMinYUm
        $bottomEdge = [double]$script:ScanMaxYUm
        $widthUm = [math]::Abs($leftEdge - $rightEdge)
        $heightUm = [math]::Abs($bottomEdge - $topEdge)
        $cols = Get-TileCount -ExtentUm $widthUm -FovUm $fovWidthUm -OverlapFraction $overlap
        $rows = Get-TileCount -ExtentUm $heightUm -FovUm $fovHeightUm -OverlapFraction $overlap
        $scanLabel.Text = "Scan ROI: left={0:N0} um, right={1:N0} um, top={2:N0} um, bottom={3:N0} um. Size={4:N0} x {5:N0} um. Estimated raster={6} x {7} ({8} tiles)." -f $leftEdge, $rightEdge, $topEdge, $bottomEdge, $widthUm, $heightUm, $cols, $rows, ($cols * $rows)
    }

    $violations = Get-ScanRoiViolations
    $marginUm = Get-TextBoxDouble -TextBox $marginBox -Default $safetyMarginUm
    $safeParts = @()
    if ($null -ne $script:MinXUm -and $null -ne $script:MaxXUm) {
        $safeParts += ("X={0:N0}..{1:N0} um" -f ([double]$script:MinXUm + $marginUm), ([double]$script:MaxXUm - $marginUm))
    }
    if ($null -ne $script:MinYUm -and $null -ne $script:MaxYUm) {
        $safeParts += ("Y={0:N0}..{1:N0} um" -f ([double]$script:MinYUm + $marginUm), ([double]$script:MaxYUm - $marginUm))
    }

    if ($violations.Count -gt 0 -and $allowOutOfBoundsCheck.Checked) {
        $scanNotes.Text = "Safe-window bypass enabled. ROI would normally be blocked: " + (($violations | Select-Object -First 2) -join "; ")
    }
    elseif ($violations.Count -gt 0) {
        $scanNotes.Text = "ROI is outside the current safe window. " + (($violations | Select-Object -First 2) -join "; ")
    }
    elseif ($safeParts.Count -gt 0) {
        $scanNotes.Text = "Safe scan window with current margin: " + ($safeParts -join ", ")
    }
    elseif ($cameraDriver -eq "watched_folder") {
        $scanNotes.Text = "Camera driver: watched_folder. Set EOS Utility once to save into $incomingDir. With your current belt slack, start around 20-30% overlap if you want safer coverage."
    }
    else {
        $scanNotes.Text = "Camera driver: $cameraDriver. Start Scan will use the configured capture path for each tile."
    }
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

function Capture-ScanEdge {
    param([string]$FieldName)
    if ($null -eq $script:CurrentStatus) {
        Refresh-Status
    }
    if ($null -eq $script:CurrentStatus) {
        return
    }
    switch ($FieldName) {
        "left_edge" { $script:ScanMaxXUm = $script:CurrentStatus.MachineX * 1000.0 }
        "right_edge" { $script:ScanMinXUm = $script:CurrentStatus.MachineX * 1000.0 }
        "top_edge" { $script:ScanMinYUm = $script:CurrentStatus.MachineY * 1000.0 }
        "bottom_edge" { $script:ScanMaxYUm = $script:CurrentStatus.MachineY * 1000.0 }
    }
    Update-ScanLabel
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

function Save-ScanSettings {
    param([bool]$ShowMessage = $true)
    if ($null -eq $script:ScanMinXUm -or $null -eq $script:ScanMaxXUm -or $null -eq $script:ScanMinYUm -or $null -eq $script:ScanMaxYUm) {
        [System.Windows.Forms.MessageBox]::Show("Capture all four scan edges before saving the scan ROI.")
        return $false
    }
    $violations = Get-ScanRoiViolations
    if ($violations.Count -gt 0 -and -not $allowOutOfBoundsCheck.Checked) {
        [System.Windows.Forms.MessageBox]::Show("The scan ROI is outside the current safe motion bounds:`r`n`r`n" + ($violations -join "`r`n") + "`r`n`r`nRemark the scan edges farther from the stage limits or reduce the safety margin if you intentionally want to scan closer.")
        return $false
    }
    try {
        $updates = @{
            fov_width_um = [double]$fovWidthBox.Text
            fov_height_um = [double]$fovHeightBox.Text
            overlap_fraction = [double]$overlapBox.Text
            photo_root_dir = [string]$photoRootBox.Text
            allow_out_of_bounds = [bool]$allowOutOfBoundsCheck.Checked
            roi_min_x_um = [double]$script:ScanMinXUm
            roi_max_x_um = [double]$script:ScanMaxXUm
            roi_min_y_um = [double]$script:ScanMinYUm
            roi_max_y_um = [double]$script:ScanMaxYUm
        }
        Set-ConfigValues -Path $Config -Section "scan" -Updates $updates
        if ($ShowMessage) {
            [System.Windows.Forms.MessageBox]::Show("Saved scan ROI and scan settings to $Config")
        }
        return $true
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Saving scan settings failed: $($_.Exception.Message)")
        return $false
    }
}

function Start-Scan {
    if (-not (Save-ScanSettings -ShowMessage:$false)) {
        return
    }

    $sampleId = $sampleIdBox.Text.Trim()
    $material = $materialBox.Text.Trim()
    $substrate = $substrateBox.Text.Trim()
    $objective = $objectiveBox.Text.Trim()
    $operator = $operatorBox.Text.Trim()
    $photoRoot = $photoRootBox.Text.Trim()

    if ([string]::IsNullOrWhiteSpace($sampleId) -or [string]::IsNullOrWhiteSpace($material) -or [string]::IsNullOrWhiteSpace($substrate) -or [string]::IsNullOrWhiteSpace($objective)) {
        [System.Windows.Forms.MessageBox]::Show("Sample ID, material, substrate, and objective are required before starting a scan.")
        return
    }

    $pythonExe = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    $launchScript = Join-Path $repoRoot "scripts\launch_capture_scan.ps1"
    if (-not (Test-Path $pythonExe)) {
        [System.Windows.Forms.MessageBox]::Show("Bundled Python runtime was not found at $pythonExe")
        return
    }
    if (-not (Test-Path $launchScript)) {
        [System.Windows.Forms.MessageBox]::Show("Scan launcher script was not found at $launchScript")
        return
    }

    if (-not [System.IO.Path]::IsPathRooted($photoRoot)) {
        $resolvedPhotoRoot = Join-Path $repoRoot $photoRoot
    }
    else {
        $resolvedPhotoRoot = $photoRoot
    }
    if (-not (Test-Path $resolvedPhotoRoot)) {
        New-Item -ItemType Directory -Path $resolvedPhotoRoot -Force | Out-Null
    }
    if (-not (Test-Path $incomingDir)) {
        New-Item -ItemType Directory -Path $incomingDir -Force | Out-Null
    }

    $argList = @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", (Quote-ProcessArgument $launchScript),
        "-Config", (Quote-ProcessArgument $Config),
        "-SampleId", (Quote-ProcessArgument $sampleId),
        "-Material", (Quote-ProcessArgument $material),
        "-Substrate", (Quote-ProcessArgument $substrate),
        "-Objective", (Quote-ProcessArgument $objective),
        "-OutputRoot", (Quote-ProcessArgument $photoRoot),
        "-RoiMinXUm", (Quote-ProcessArgument ('{0:0.###}' -f $script:ScanMinXUm)),
        "-RoiMaxXUm", (Quote-ProcessArgument ('{0:0.###}' -f $script:ScanMaxXUm)),
        "-RoiMinYUm", (Quote-ProcessArgument ('{0:0.###}' -f $script:ScanMinYUm)),
        "-RoiMaxYUm", (Quote-ProcessArgument ('{0:0.###}' -f $script:ScanMaxYUm))
    )
    if (-not [string]::IsNullOrWhiteSpace($operator)) {
        $argList += @("-Operator", (Quote-ProcessArgument $operator))
    }
    if ($allowOutOfBoundsCheck.Checked) {
        $argList += @("-AllowOutOfBounds")
    }

    $argumentString = $argList -join " "
    $process = Start-Process -FilePath "powershell.exe" -ArgumentList $argumentString -WorkingDirectory $repoRoot -PassThru
    $rawBox.Text = "Started scan in a separate PowerShell window (PID $($process.Id)).`r`nPhoto root: $resolvedPhotoRoot`r`nIncoming hot folder: $incomingDir`r`nIf anything fails, the scan console will stay open and show the error."
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
$markLeftEdgeButton.Add_Click({ Capture-ScanEdge -FieldName "left_edge" })
$markRightEdgeButton.Add_Click({ Capture-ScanEdge -FieldName "right_edge" })
$markTopEdgeButton.Add_Click({ Capture-ScanEdge -FieldName "top_edge" })
$markBottomEdgeButton.Add_Click({ Capture-ScanEdge -FieldName "bottom_edge" })
$saveScanButton.Add_Click({ [void](Save-ScanSettings) })
$startScanButton.Add_Click({ Start-Scan })
$fovWidthBox.Add_TextChanged({ Update-ScanLabel })
$fovHeightBox.Add_TextChanged({ Update-ScanLabel })
$overlapBox.Add_TextChanged({ Update-ScanLabel })
$allowOutOfBoundsCheck.Add_CheckedChanged({ Update-ScanLabel })

Update-BoundsLabel
Update-ScanLabel

if ($SelfTest) {
    Write-Output "stage-calibration-ui-ok"
    return
}

[void]$form.ShowDialog()
