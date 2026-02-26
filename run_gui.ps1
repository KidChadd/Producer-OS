param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSCommandPath
Set-Location $repoRoot

$srcPath = Join-Path $repoRoot "src"
if (Test-Path $srcPath) {
    $env:PYTHONPATH = (Resolve-Path $srcPath).Path
}

$venvPython = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
$pythonCmd = if (Test-Path $venvPython) { $venvPython } else { "python" }

& $pythonCmd -m producer_os gui @AppArgs
exit $LASTEXITCODE
