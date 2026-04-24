param(
    [Parameter(Mandatory = $true, ParameterSetName = "session")]
    [string]$SessionDir,

    [Parameter(Mandatory = $true, ParameterSetName = "images")]
    [string]$ImageDir,

    [string]$Output = ""
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot ".venv-napari\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Napari runtime was not found at $pythonExe"
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
Set-Location $repoRoot

$args = @(
    "-m", "flake_ml.cli", "review-images",
    "--tool", "napari"
)

if ($PSCmdlet.ParameterSetName -eq "session") {
    $resolvedSessionDir = if ([System.IO.Path]::IsPathRooted($SessionDir)) { $SessionDir } else { Join-Path $repoRoot $SessionDir }
    $args += @("--session-dir", $resolvedSessionDir)
}
else {
    $resolvedImageDir = if ([System.IO.Path]::IsPathRooted($ImageDir)) { $ImageDir } else { Join-Path $repoRoot $ImageDir }
    $args += @("--image-dir", $resolvedImageDir)
}

if (-not [string]::IsNullOrWhiteSpace($Output)) {
    $resolvedOutput = if ([System.IO.Path]::IsPathRooted($Output)) { $Output } else { Join-Path $repoRoot $Output }
    $args += @("--output", $resolvedOutput)
}

& $pythonExe @args

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
