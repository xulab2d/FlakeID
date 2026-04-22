param(
    [Parameter(Mandatory = $true)]
    [string]$Port,

    [int]$Baud = 115200,

    [string[]]$Command = @(),

    [int]$StartupDelayMs = 1200,

    [int]$TimeoutMs = 2000,

    [string]$WaitFor = "ok"
)

$serial = $null

try {
    $serial = New-Object System.IO.Ports.SerialPort $Port, $Baud, ([System.IO.Ports.Parity]::None), 8, ([System.IO.Ports.StopBits]::One)
    $serial.NewLine = "`n"
    $serial.ReadTimeout = 250
    $serial.WriteTimeout = 1000
    $serial.DtrEnable = $true
    $serial.RtsEnable = $true
    $serial.Open()

    Start-Sleep -Milliseconds $StartupDelayMs

    $startup = $serial.ReadExisting()

    $responses = New-Object System.Collections.Generic.List[string]
    if ($startup) {
        $responses.Add($startup)
    }

    foreach ($line in $Command) {
        $serial.Write($line + "`r`n")
        Start-Sleep -Milliseconds 40
    }

    if ($WaitFor -eq "__NONE__") {
        Start-Sleep -Milliseconds 100
    }

    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)

    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $chunk = $serial.ReadExisting()
            if ($chunk) {
                $responses.Add($chunk)
                if ($WaitFor -eq "__NONE__") {
                    break
                }
                if ($chunk.Contains($WaitFor)) {
                    break
                }
            }
        }
        catch {
        }

        Start-Sleep -Milliseconds 20
    }

    $text = ($responses.ToArray() -join "")
    Write-Output $text
}
finally {
    if ($serial -and $serial.IsOpen) {
        $serial.Close()
    }
}
