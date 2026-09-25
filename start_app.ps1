$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python environment not found. Run: python -m venv .venv and pip install -r backend\requirements.txt"
}

try {
    $postgres = Get-Service -Name "postgresql-x64-17" -ErrorAction Stop
    if ($postgres.Status -ne "Running") {
        Start-Service -Name "postgresql-x64-17"
    }
} catch {
    Write-Warning "PostgreSQL could not be started automatically. Start the PostgreSQL service, then run this launcher again."
}

$flaskCommand = "Set-Location '$projectRoot'; & '$python' run.py"
Start-Process powershell.exe -WorkingDirectory $projectRoot -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $flaskCommand
)

if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $tunnelCommand = "Set-Location '$projectRoot'; cloudflared tunnel --url http://127.0.0.1:5000"
    Start-Process powershell.exe -WorkingDirectory $projectRoot -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $tunnelCommand
    )
} else {
    Write-Warning "cloudflared was not found. The local app will still start at http://127.0.0.1:5000."
}

Write-Host "Flask and the tunnel are starting in separate windows."
Write-Host "Keep those windows open while using the application."
