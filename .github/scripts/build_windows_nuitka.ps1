param(
    [string]$ZipOutput = "",
    [int]$SmokeTestTimeoutSeconds = 20,
    [ValidateSet("dev", "release")]
    [string]$BuildProfile = "release",
    [string]$RepoRoot = "",
    [string]$BuildInfoOutput = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
} else {
    (Resolve-Path $RepoRoot).Path
}
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
        "--include-module=packaging",
        "--include-package=qdarktheme",
        "--include-package-data=qdarktheme",
        "--module-parameter=numba-disable-jit=yes",
        # Avoid recursively compiling large upstream test suites in standalone builds.
        "--nofollow-import-to=numba.tests",
        "--nofollow-import-to=llvmlite.tests",
        "--nofollow-import-to=scipy.tests",
        "--nofollow-import-to=sklearn.tests",
        "--nofollow-import-to=joblib.test",
        "--nofollow-import-to=joblib.testing"
    )
    switch ($BuildProfile) {
        "release" {
            # Conservative release profile keeps explicit includes for known optional imports.
            $nuitkaArgs += @(
                "--include-module=sklearn",
                "--include-module=joblib"
            )
        }
        "dev" {
            # Faster local/CI dev builds: omit explicit sklearn/joblib force-includes.
            # Smoke tests still validate packaged startup, but runtime coverage is narrower.
        }
        default {
            throw "Unsupported BuildProfile: $BuildProfile"
        }
    }
    if (Test-Path "assets\app_icon.ico") {
        $nuitkaArgs += "--windows-icon-from-ico=assets/app_icon.ico"
    }
    $nuitkaArgs += "build_gui_entry.py"

    $gitSha = ""
    $gitRef = ""
    try { $gitSha = (git rev-parse HEAD 2>$null).Trim() } catch {}
    try { $gitRef = (git describe --tags --always --dirty 2>$null).Trim() } catch {}

    $scriptSource = (Resolve-Path $PSCommandPath).Path
    Write-Host "Build profile: $BuildProfile"
    if ($gitSha) { Write-Host "Source commit: $gitSha" }
    if ($gitRef) { Write-Host "Source ref: $gitRef" }
    Write-Host "Build script source: $scriptSource"
    Write-Host "Repo root: $repoRoot"
    Write-Host "Nuitka args count: $($nuitkaArgs.Count)"

    if (-not [string]::IsNullOrWhiteSpace($BuildInfoOutput)) {
        $buildInfoPath = if ([System.IO.Path]::IsPathRooted($BuildInfoOutput)) {
            $BuildInfoOutput
        } else {
            Join-Path $repoRoot $BuildInfoOutput
        }
        $buildInfoDir = Split-Path -Parent $buildInfoPath
        if ($buildInfoDir -and -not (Test-Path $buildInfoDir)) {
            New-Item -ItemType Directory -Force -Path $buildInfoDir | Out-Null
        }
        $buildInfoLines = @(
            "producer_os_build_context",
            "profile`t$BuildProfile",
            "repo_root`t$repoRoot",
            "script_source`t$scriptSource",
            "git_sha`t$gitSha",
            "git_ref`t$gitRef",
            "timestamp_utc`t$([DateTime]::UtcNow.ToString('o'))",
            "nuitka_args`t$($nuitkaArgs -join ' ')"
        )
        Set-Content -Path $buildInfoPath -Value $buildInfoLines -Encoding ascii
        Write-Host "Wrote build info: $buildInfoPath"
    }

    python -m nuitka @nuitkaArgs

    $distBundle = "dist\build_gui_entry.dist"
    $qwindows = Get-ChildItem -Path $distBundle -Recurse -Filter "qwindows.dll" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $qwindows) {
        throw "Qt platform plugin qwindows.dll not found in standalone build output."
    }
    Write-Host "Found qwindows.dll at $($qwindows.FullName)"

    $exePath = Join-Path $distBundle "ProducerOS.exe"
    if (!(Test-Path $exePath)) {
        throw "Standalone executable missing: $exePath"
    }
    Write-Host "Running packaged GUI smoke test..."
    $env:PRODUCER_OS_SMOKE_TEST = "1"
    $env:PRODUCER_OS_SMOKE_TEST_MS = "250"
    $proc = Start-Process -FilePath $exePath -PassThru
    try {
        Wait-Process -Id $proc.Id -Timeout $SmokeTestTimeoutSeconds
        $proc.Refresh()
        if ($proc.ExitCode -ne 0) {
            throw "Smoke test failed with exit code $($proc.ExitCode)"
        }
    }
    catch {
        try {
            if (-not $proc.HasExited) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
        catch {}
        throw
    }
    finally {
        Remove-Item Env:PRODUCER_OS_SMOKE_TEST -ErrorAction SilentlyContinue
        Remove-Item Env:PRODUCER_OS_SMOKE_TEST_MS -ErrorAction SilentlyContinue
    }
    Write-Host "Smoke test passed."

    $signScript = Join-Path $PSScriptRoot "sign_windows_artifacts.ps1"
    if (Test-Path $signScript) {
        & $signScript -Paths @($exePath)
    }

    if (-not [string]::IsNullOrWhiteSpace($ZipOutput)) {
        if (Test-Path $ZipOutput) { Remove-Item $ZipOutput -Force }
        Compress-Archive -Path "$distBundle\*" -DestinationPath $ZipOutput
        Write-Host "Created ZIP: $ZipOutput"
    }
}
finally {
    Pop-Location
}
