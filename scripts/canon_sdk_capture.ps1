param(
    [string]$Output = "",
    [double]$TimeoutSeconds = 45.0,
    [switch]$Probe,
    [string]$CanonDllDir = "C:\Program Files (x86)\Canon\EOS Utility\EU3"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $repoRoot "tools\canon_sdk_capture\CanonEdsdkCapture.cs"
$buildDir = Join-Path $repoRoot "tools\canon_sdk_capture\bin"
$exePath = Join-Path $buildDir "CanonEdsdkCapture.exe"
$compiler = "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"

if (-not (Test-Path $sourcePath)) {
    throw "Canon SDK helper source was not found at $sourcePath"
}
if (-not (Test-Path $compiler)) {
    throw "C# compiler was not found at $compiler"
}
if (-not (Test-Path $CanonDllDir)) {
    throw "Canon EOS Utility SDK directory was not found at $CanonDllDir"
}

New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

$needsBuild = -not (Test-Path $exePath)
if (-not $needsBuild) {
    $sourceWrite = (Get-Item $sourcePath).LastWriteTimeUtc
    $exeWrite = (Get-Item $exePath).LastWriteTimeUtc
    if ($sourceWrite -gt $exeWrite) {
        $needsBuild = $true
    }
}

if ($needsBuild) {
    & $compiler /nologo /target:exe /platform:x86 /optimize+ /out:$exePath $sourcePath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to compile the Canon SDK helper."
    }
}

$env:PATH = "$CanonDllDir;$env:PATH"
$arguments = @("--dll-dir", $CanonDllDir)
if ($Probe) {
    $arguments += @("--probe")
}
else {
    if ([string]::IsNullOrWhiteSpace($Output)) {
        throw "Provide -Output unless you are using -Probe."
    }
    $arguments += @(
        "--output", $Output,
        "--timeout-s", ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0:0.###}", $TimeoutSeconds))
    )
}

& $exePath @arguments
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
