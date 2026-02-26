[CmdletBinding()]
param(
  [string]$Extras = "dev",
  [string]$ConstraintsFile = ".github/constraints/ci-tools.txt"
)

$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip

$pipArgs = @("-m", "pip", "install")
$constraintsInUse = $false
if ($ConstraintsFile -and (Test-Path $ConstraintsFile)) {
  $pipArgs += @("-c", $ConstraintsFile)
  $constraintsInUse = $true
}

if ([string]::IsNullOrWhiteSpace($Extras)) {
  $pipArgs += @("-e", ".")
  $extrasLabel = "<none>"
} else {
  $pipArgs += @("-e", (".[${Extras}]"))
  $extrasLabel = $Extras
}

$constraintLabel = if ($constraintsInUse) { " using constraints '$ConstraintsFile'" } else { "" }
Write-Host "Installing editable package with extras '$extrasLabel'$constraintLabel"

& python @pipArgs
