<#
.SYNOPSIS
    Deploy the FullTeaching SUT stack (Windows), from the repo root.

.DESCRIPTION
    Thin wrapper around selenium-java\deploy-sut.ps1: it just makes sure the
    fetched folders exist and that local.env is in place, then delegates.
    Requires Docker Desktop running. Run setup-sut.ps1 first.

.PARAMETER Down
    Stop the SUT stack instead of building/starting it.

.EXAMPLE
    .\deploy.ps1            # build + start the SUT, uses TJOB_NAME=local
.EXAMPLE
    .\deploy.ps1 -Down      # stop the SUT
#>

param(
    [switch]$Down
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TestDir = Join-Path $RootDir "selenium-java"
$DeployScript = Join-Path $TestDir "deploy-sut.ps1"
$EnvFile = Join-Path $TestDir "local.env"
$SourceEnvFile = Join-Path $TestDir ".retorch\envfiles\local.env"

if (-not (Test-Path $DeployScript)) {
    Write-Error "$DeployScript not found. Run .\setup-sut.ps1 first to fetch sut\ and selenium-java\."
    exit 1
}

# deploy-sut.ps1 expects local.env next to itself, but it only ships under
# .retorch\envfiles\local.env - copy it into place if missing.
if (-not (Test-Path $EnvFile) -and (Test-Path $SourceEnvFile)) {
    Copy-Item -Path $SourceEnvFile -Destination $EnvFile
}

& $DeployScript @PSBoundParameters
exit $LASTEXITCODE
