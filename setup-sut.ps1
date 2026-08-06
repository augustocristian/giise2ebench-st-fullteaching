<#
.SYNOPSIS
    Fetch the SUT and the Selenium test suite for this benchmark.

.DESCRIPTION
    Clones https://github.com/giis-uniovi/retorch-st-fullteaching and splits it into:
      ./sut            - the FullTeaching application (System Under Test)
      ./selenium-java   - everything else (Selenium/Java E2E test suite, RETORCH
                           config, pom.xml, docker-compose files, etc.)

    Both folders are gitignored: they are fetched on demand, never committed.
    Re-run this script any time to refresh them to the latest upstream state.

.EXAMPLE
    .\setup-sut.ps1
#>

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/giis-uniovi/retorch-st-fullteaching.git"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SutDir = Join-Path $RootDir "sut"
$TestDir = Join-Path $RootDir "selenium-java"

$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null
$CloneDir = Join-Path $TmpDir "repo"

try {
    Write-Host "==> Cloning $RepoUrl"
    # core.longpaths avoids "Filename too long" checkout failures on Windows
    git -c core.longpaths=true clone --depth 1 --single-branch $RepoUrl $CloneDir
    if ($LASTEXITCODE -ne 0) { throw "git clone failed" }

    $ClonedSut = Join-Path $CloneDir "sut"
    if (-not (Test-Path $ClonedSut)) {
        throw "Expected 'sut' folder not found in cloned repo."
    }

    Write-Host "==> Refreshing $SutDir"
    if (Test-Path $SutDir) { Remove-Item -Recurse -Force $SutDir }
    Move-Item -Path $ClonedSut -Destination $SutDir

    Write-Host "==> Refreshing $TestDir"
    if (Test-Path $TestDir) { Remove-Item -Recurse -Force $TestDir }
    Remove-Item -Recurse -Force (Join-Path $CloneDir ".git")
    New-Item -ItemType Directory -Path $TestDir -Force | Out-Null
    Get-ChildItem -Force -Path $CloneDir | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $TestDir
    }

    Write-Host "==> Done"
    Write-Host "    sut/           -> $SutDir"
    Write-Host "    selenium-java/ -> $TestDir"
}
finally {
    Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
}
