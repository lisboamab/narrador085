#!/usr/bin/env bash
# Instala o narrador085 no Linux/WSL2: uv, Python 3.12 isolado em .venv e dependências.
# Uso: ./instalar.sh   (pode rodar de novo quando quiser; só completa o que falta)
set -euo pipefail
cd "$(dirname "$0")"

if command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null 2>&1; then
    echo "GPU: $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader)"
else
    echo "AVISO: nvidia-smi não encontrou GPU NVIDIA. A instalação continua, mas a narração precisa de GPU."
    echo "       Ubuntu: sudo ubuntu-drivers install && reinicie. WSL2: atualize o driver no Windows."
fi

if ! command -v uv >/dev/null; then
    echo "Instalando o uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Criando o ambiente Python 3.12 em .venv..."
[ -x .venv/bin/python ] || uv venv --python 3.12 .venv

echo "Instalando as dependências (na primeira vez baixa uns 3 GB)..."
uv pip install --python .venv/bin/python -r requirements.txt

chmod +x narrar
.venv/bin/python - <<'EOF'
import torch
if torch.cuda.is_available():
    print(f"\nPronto! torch {torch.__version__} usando {torch.cuda.get_device_name(0)}.")
else:
    print(f"\nInstalado, mas o torch {torch.__version__} não está vendo a GPU: confira o driver NVIDIA.")
EOF
echo "Próximo passo: ./narrar voz sua_gravacao.m4a   (veja o README)"
