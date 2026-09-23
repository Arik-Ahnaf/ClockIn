$ErrorActionPreference = 'Stop'
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot '../..')
Push-Location $ProjectRoot
try {
    uv sync --locked --group build
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
    uv run --no-sync python build.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
    uv run --no-sync python scripts/verify_distribution.py
    if ($LASTEXITCODE -ne 0) { throw 'Distribution verification failed' }
} finally {
    Pop-Location
}
