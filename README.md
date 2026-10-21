# narrador085

Narra as postagens da 085Tec com a sua voz, usando o [OmniVoice](https://github.com/k2-fsa/OmniVoice)
localmente na GPU.

## Instalação

### Requisitos

- **GPU NVIDIA** com pelo menos 6 GB de memória (testado numa RTX 3050 de 8 GB). Não roda só na CPU.
- **Driver NVIDIA** atualizado (versão 570 ou mais nova, para CUDA 12.8). O CUDA Toolkit não precisa ser instalado: ele vem junto com o torch.
- **Git**, para baixar o projeto.
- **uv**, que instala o Python 3.12 e as dependências. O torch 2.8 não funciona no Python 3.13+, e o uv baixa
  o 3.12 sozinho, sem mexer no Python do sistema.
- Cerca de **10 GB livres**: uns 7 GB do ambiente Python, mais os modelos baixados na primeira execução.

O ffmpeg não precisa ser instalado: o projeto usa o executável que vem no pacote `imageio-ffmpeg`.

### Linux (Ubuntu/Debian; vale também para o WSL2 no Windows)

**1. Confira se a GPU aparece.** Deve mostrar o nome da placa e a versão do driver:
```bash
nvidia-smi
```
Se o comando não existir, instale o driver: `sudo ubuntu-drivers install` e reinicie.
No WSL2, o driver é o do Windows; não instale driver dentro do Linux.

**2. Instale o git e o uv:**
```bash
sudo apt update && sudo apt install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc        # ou feche e abra o terminal, para o comando uv aparecer
```

**3. Baixe o projeto:**
```bash
git clone https://github.com/lisboamab/narrador085.git
cd narrador085
```

**4. Crie o ambiente Python 3.12 e instale as dependências** (demora alguns minutos, baixa uns 3 GB):
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

**5. Coloque o ffmpeg dentro da venv** (o `narrar.py` procura ele lá):
```bash
ln -s "$(.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" .venv/bin/ffmpeg
```

**6. Teste.** Deve imprimir `2.8.0+cu128 True NVIDIA GeForce ...`:
```bash
.venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
.venv/bin/python narrar.py gerar posts/ --mostrar-texto
```
Se aparecer `False`, o torch não está vendo a GPU: confira o passo 1.

### Windows (PowerShell)

Abra o **PowerShell** (não precisa ser como administrador).

**1. Confira se a GPU aparece:**
```powershell
nvidia-smi
```
Se der erro, instale o driver mais recente em https://www.nvidia.com/pt-br/drivers/ e reinicie.

**2. Instale o git e o uv:**
```powershell
winget install --id Git.Git -e
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Feche e abra o PowerShell, para os comandos `git` e `uv` aparecerem.

**3. Baixe o projeto:**
```powershell
git clone https://github.com/lisboamab/narrador085.git
cd narrador085
```

**4. Crie o ambiente Python 3.12 e instale as dependências:**
```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

**5. Copie o ffmpeg para dentro da venv** (no Windows usamos cópia em vez de atalho, que exigiria administrador):
```powershell
Copy-Item (.venv\Scripts\python.exe -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())") .venv\Scripts\ffmpeg.exe
```

**6. Teste:**
```powershell
.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
.venv\Scripts\python.exe narrar.py gerar posts\ --mostrar-texto
```

> **No Windows, em todos os comandos abaixo** troque `.venv/bin/python` por `.venv\Scripts\python.exe`
> e use `\` nos caminhos (`posts\`, `voz\fulano.pt`).

### Primeira execução

Na primeira vez que você rodar `narrar.py voz` ou `narrar.py gerar`, os modelos `k2-fsa/OmniVoice` e
`openai/whisper-large-v3-turbo` são baixados do Hugging Face (alguns GB, só uma vez). Eles ficam em
`~/.cache/huggingface` (Linux) ou `%USERPROFILE%\.cache\huggingface` (Windows).

### Problemas comuns

- **`torch.cuda.is_available()` dá `False`**: driver ausente ou antigo; atualize e reinicie.
- **`CUDA out of memory`**: feche jogos ou programas que usam a GPU; posts muito longos podem ser divididos em arquivos menores.
- **`Couldn't find ffmpeg`**: o passo 5 não foi feito, ou foi feito antes do passo 4.
- **`uv: command not found`**: feche e abra o terminal depois de instalar o uv.

## 1. Gravar a voz (uma vez)

Grave de 5 a 20 s, num lugar silencioso, lendo um texto com o tom que você quer na narração. Por exemplo:

> Olá, aqui é da 085Tec. Hoje eu quero falar com você sobre tecnologia, sites e sistemas feitos sob medida para a sua empresa.

Pode ser .m4a/.ogg do celular ou WhatsApp, .mp3 ou .wav.

```bash
.venv/bin/python narrar.py voz ~/gravacao.m4a --texto "Olá, aqui é da 085Tec. Hoje eu quero ..."
```

Isso cria `voz/minha_voz.pt`, reaproveitado em toda geração. Sem `--texto`, o Whisper transcreve.

## 2. Gerar os áudios

Coloque cada postagem como `.txt` ou `.md` em `posts/` e rode:

```bash
.venv/bin/python narrar.py gerar posts/               # MP3 em saida/
.venv/bin/python narrar.py gerar posts/ --mostrar-texto  # só confere o que será lido
.venv/bin/python narrar.py gerar posts/novo.txt --velocidade 1.1 --forcar
```

Só gera o que mudou: um post com MP3 mais novo que o texto é pulado (`--forcar` regera).

Antes de narrar, o texto é limpo: emojis, URLs e blocos de hashtags somem; `#tag` no meio da frase vira
palavra; números, `%` e `R$` vão por extenso; listas ganham pausas.

## Outras vozes

Cada voz é um arquivo `.pt` em `voz/`; não há treino, o modelo clona a voz direto da gravação.
Para adicionar uma (ex.: Fulano), coloque a gravação em `voz/` e crie o perfil com `--saida`:

```bash
.venv/bin/python narrar.py voz voz/fulano.ogg --saida voz/fulano.pt
```

Confira a transcrição que aparece no final; se o Whisper errou, refaça passando `--texto "o que foi dito"`.
Depois gere com `--voz`, de preferência numa pasta própria para não sobrescrever os outros áudios:

```bash
.venv/bin/python narrar.py gerar posts/ --voz voz/fulano.pt --saida saida/fulano
```

Áudio de WhatsApp funciona, mas a voz clonada herda a qualidade e o tom da gravação: o ideal é 10–15 s
lendo um texto com calma, sem ruído. Só clone a voz de quem autorizou.

## Emoção (raiva, empolgação…)

Não existe opção "fale com raiva": na clonagem, a emoção vem da gravação de referência. Em ordem de efeito:

1. **Grave a voz já com a emoção** (10–15 s, sem ruído) e crie um perfil separado:
   ```bash
   .venv/bin/python narrar.py voz voz/fulano_raiva.ogg --saida voz/fulano_raiva.pt
   ```
2. **Escreva para ser falado**: frases curtas ("Não. Chega."), `?!` e `!`, reticências para pausa tensa.
3. **Acelere um pouco**: raiva costuma ser mais rápida, teste `--velocidade 1.15`.
4. **Marcações de som** no meio do texto: `[sigh]` (suspiro), `[dissatisfaction-hnn]` (muxoxo),
   `[surprise-ah]`. Foram feitas para inglês/chinês, então teste antes; `--mostrar-texto` confirma que chegam ao modelo.

```bash
.venv/bin/python narrar.py gerar posts/bronca.txt --voz voz/fulano_raiva.pt --saida saida/fulano --velocidade 1.15
```

## Pronúncia

`pronuncia.txt` corrige termos que o modelo leria errado (`085Tec = zero oito cinco Tec`, siglas, inglês).
Uma regra por linha; vale para a palavra inteira.

## O que fica fora do git

Gravações e perfis de voz (`voz/`), áudios gerados (`saida/`) e posts (`posts/`, exceto `exemplo.md`)
ficam só na sua máquina: são dados pessoais de quem teve a voz clonada.
