# Instala o narrador085 no Windows: uv, Python 3.12 isolado em .venv e dependências.
# Uso (PowerShell, na pasta do projeto):
#   powershell -ExecutionPolicy Bypass -File instalar.ps1
# Pode rodar de novo quando quiser; só completa o que falta.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "GPU: $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader)"
} else {
    Write-Host "AVISO: nvidia-smi nao encontrou GPU NVIDIA. A instalacao continua, mas a narracao precisa de GPU." -ForegroundColor Yellow
    Write-Host "       Instale o driver em https://www.nvidia.com/pt-br/drivers/ e reinicie." -ForegroundColor Yellow
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando o uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

Write-Host "Criando o ambiente Python 3.12 em .venv..."
if (-not (Test-Path .venv\Scripts\python.exe)) { uv venv --python 3.12 .venv }
if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "Instalando as dependencias (na primeira vez baixa uns 3 GB)..."
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
if ($LASTEXITCODE) { exit $LASTEXITCODE }

.venv\Scripts\python.exe -c @"
import torch
if torch.cuda.is_available():
    print(f'\nPronto! torch {torch.__version__} usando {torch.cuda.get_device_name(0)}.')
else:
    print(f'\nInstalado, mas o torch {torch.__version__} nao esta vendo a GPU: confira o driver NVIDIA.')
"@
Write-Host "Proximo passo: .\narrar voz sua_gravacao.m4a   (veja o README)"
