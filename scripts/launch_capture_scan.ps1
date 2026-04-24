param(
    [Parameter(Mandatory = $true)]
    [string]$Config,

    [Parameter(Mandatory = $true)]
    [string]$SampleId,

    [Parameter(Mandatory = $true)]
    [string]$Material,

    [Parameter(Mandatory = $true)]
    [string]$Substrate,

    [Parameter(Mandatory = $true)]
    [string]$Objective,

    [string]$Operator = "",

    [string]$OutputRoot = "photos/scans",

    [Parameter(Mandatory = $true)]
    [double]$RoiMinXUm,

    [Parameter(Mandatory = $true)]
    [double]$RoiMaxXUm,

    [Parameter(Mandatory = $true)]
    [double]$RoiMinYUm,

    [Parameter(Mandatory = $true)]
    [double]$RoiMaxYUm
)

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not [System.IO.Path]::IsPathRooted($Config)) {
    $Config = Join-Path $repoRoot $Config
}

$pythonExe = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Bundled Python runtime was not found at $pythonExe"
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
Set-Location $repoRoot

& $pythonExe -m flake_ml.cli run-scan `
    --config $Config `
    --sample-id $SampleId `
    --material $Material `
    --substrate $Substrate `
    --objective $Objective `
    --output-root $OutputRoot `
    --roi-min-x-um $RoiMinXUm `
    --roi-max-x-um $RoiMaxXUm `
    --roi-min-y-um $RoiMinYUm `
    --roi-max-y-um $RoiMaxYUm `
    --operator $Operator

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
