param(
    [string]$Config = "configs/lab.example.toml"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = if ([System.IO.Path]::IsPathRooted($Config)) { $Config } else { Join-Path $repoRoot $Config }
$uiScript = Join-Path $repoRoot "scripts\stage_calibration_ui.ps1"

if (-not (Test-Path $configPath)) {
    throw "Config file not found at $configPath"
}

if (-not (Test-Path $uiScript)) {
    throw "UI script not found at $uiScript"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $uiScript -Config $configPath

