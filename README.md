# narrador085

Narra as postagens da 085Tec com a sua voz, usando o [OmniVoice](https://github.com/k2-fsa/OmniVoice)
localmente na GPU.

## Instalação

Precisa de GPU NVIDIA com CUDA (testado numa RTX 3050 de 8 GB, Linux/WSL2), [uv](https://docs.astral.sh/uv/)
e Python 3.12 (o torch 2.8 não roda no 3.14).

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
# ffmpeg estático do imageio-ffmpeg, no PATH da venv (pydub e librosa o procuram lá)
ln -s "$(.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" .venv/bin/ffmpeg
```

Na primeira execução são baixados os modelos `k2-fsa/OmniVoice` e `openai/whisper-large-v3-turbo` do Hugging Face.

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
