2# dev.ps1 - Inicia Backend (FastAPI) y Frontend (Vite) en Windows
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$python = "python"
if (Test-Path ".\reddit-env\Scripts\python.exe") {
    $python = ".\reddit-env\Scripts\python.exe"
}

Write-Host "🚀 Iniciando API Backend local (http://127.0.0.1:8000)..." -ForegroundColor Cyan
$backend = Start-Process -FilePath $python -ArgumentList "-m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload" -PassThru

Write-Host "🖥️  Iniciando Frontend Web (http://localhost:5173)..." -ForegroundColor Green
$frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd frontend && npm run dev" -PassThru

Write-Host "`n✔ Ambos servidores están en ejecución." -ForegroundColor Yellow
Write-Host "👉 Abre tu navegador en: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Presiona Ctrl+C para detener ambos servidores.`n" -ForegroundColor Gray

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
    if (-not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force }
}
