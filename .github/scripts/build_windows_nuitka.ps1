param(
    [string]$ZipOutput = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
Push-Location $repoRoot
try {
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build_gui_entry.build") { Remove-Item -Recurse -Force "build_gui_entry.build" }

    $nuitkaArgs = @(
        "--standalone",
        "--enable-plugin=pyside6",
        "--windows-console-mode=disable",
        "--assume-yes-for-downloads",
        "--output-dir=dist",
        "--output-filename=ProducerOS",
        "--include-package=producer_os",
        "--include-package=librosa",
        "--include-package=scipy",
        "--include-package=numba",
        "--include-package=llvmlite",
        "--include-module=soundfile",
        "--include-package-data=librosa",
        "--include-package-data=scipy",
        "--include-package-data=numba",
        "--include-package-data=llvmlite",
        "--include-module=sklearn",
        "--include-module=packaging",
        "--include-module=joblib",
        "--include-package=qdarktheme",
        "--include-package-data=qdarktheme",
        "--module-parameter=numba-disable-jit=yes"
    )
    if (Test-Path "assets\app_icon.ico") {
        $nuitkaArgs += "--windows-icon-from-ico=assets/app_icon.ico"
    }
    $nuitkaArgs += "build_gui_entry.py"

    python -m nuitka @nuitkaArgs

    $distBundle = "dist\build_gui_entry.dist"
    $qwindows = Get-ChildItem -Path $distBundle -Recurse -Filter "qwindows.dll" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $qwindows) {
        throw "Qt platform plugin qwindows.dll not found in standalone build output."
    }
    Write-Host "Found qwindows.dll at $($qwindows.FullName)"

    if (-not [string]::IsNullOrWhiteSpace($ZipOutput)) {
        if (Test-Path $ZipOutput) { Remove-Item $ZipOutput -Force }
        Compress-Archive -Path "$distBundle\*" -DestinationPath $ZipOutput
        Write-Host "Created ZIP: $ZipOutput"
    }
}
finally {
    Pop-Location
}
