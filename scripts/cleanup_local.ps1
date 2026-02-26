[CmdletBinding(SupportsShouldProcess = $true)]
param()

$ErrorActionPreference = "Stop"

function Remove-LocalTarget {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    return
  }

  if ($PSCmdlet.ShouldProcess($Path, "Remove local generated artifact")) {
    Remove-Item -LiteralPath $Path -Recurse -Force
    Write-Host "Removed: $Path"
  }
}

$staticTargets = @(
  ".venv-build",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  "__pycache__",
  "dist",
  "_smoke_hub",
  "_smoke_tiny_analyze_hub",
  "benchmarks/_tmp_synth_corpus",
  "benchmarks/latest_engine_extract.json"
)

foreach ($target in $staticTargets) {
  Remove-LocalTarget -Path $target
}

# Remove top-level Nuitka temp/output folders without touching unrelated tracked files.
Get-ChildItem -Force -Path "." -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like ".nuitka*" } |
  ForEach-Object { Remove-LocalTarget -Path $_.FullName }

# Keep the tracked Inno Setup sources under build/installer.
if (Test-Path -LiteralPath "build") {
  Get-ChildItem -Force -Path "build" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne "installer" } |
    ForEach-Object { Remove-LocalTarget -Path $_.FullName }
}
