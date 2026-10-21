"""Narrador 085Tec — transforma textos de postagens em áudio com a voz clonada via OmniVoice.

Uso:
    python narrar.py voz gravacao.m4a [--texto "o que foi dito na gravação"]
    python narrar.py gerar posts/            # todos os .txt/.md da pasta
    python narrar.py gerar post.txt --forcar # regera mesmo se já existir
"""

import argparse
import os
import re
import sys
import unicodedata
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
# O ffmpeg estático fica em .venv/bin; pydub e librosa o procuram no PATH.
os.environ["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"
warnings.filterwarnings("ignore")

VOZ_PADRAO = RAIZ / "voz" / "minha_voz.pt"
SAIDA_PADRAO = RAIZ / "saida"
PRONUNCIA = RAIZ / "pronuncia.txt"
EXTENSOES = {".txt", ".md"}


def carregar_modelo():
    import torch
    from omnivoice import OmniVoice

    return OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cuda:0", dtype=torch.float16)


# ---------------------------------------------------------------- texto


def carregar_pronuncia():
    """Lê pronuncia.txt: uma regra por linha, `termo = como falar`. Linhas com # são comentário."""
    regras = []
    if PRONUNCIA.exists():
        for linha in PRONUNCIA.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            termo, fala = (parte.strip() for parte in linha.split("=", 1))
            regras.append((re.compile(rf"(?<!\w){re.escape(termo)}(?!\w)", re.IGNORECASE), fala))
    return regras


def sem_emoji(texto):
    return "".join(
        c for c in texto
        if unicodedata.category(c) not in ("So", "Cs", "Co") and c not in "‍️"
    )


def numero_por_extenso(m):
    from num2words import num2words

    return num2words(int(m.group()), lang="pt_BR")


def preparar_texto(bruto, regras):
    """Converte o texto de uma postagem (markdown, emojis, hashtags) em algo bom de ler em voz alta."""
    linhas = []
    for linha in bruto.splitlines():
        s = linha.strip()
        # Bloco de hashtags no fim do post não se lê.
        if s and all(p.startswith("#") and not p.startswith("##") for p in s.split()) and not s.startswith("# "):
            continue
        s = re.sub(r"^#{1,6}\s+", "", s)            # títulos markdown
        s = re.sub(r"^>\s+", "", s)                 # citações
        item = re.sub(r"^([\-*•]|\d+[.)])\s+", "", s)  # itens de lista ganham pausa
        if item != s and item and item[-1] not in ".!?…:;,":
            item += ","
        linhas.append(item)
    texto = "\n".join(linhas)

    texto = re.sub(r"```.*?```", " ", texto, flags=re.S)           # blocos de código
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", texto)            # imagens
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)         # links: fica o texto
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)           # URLs soltas
    texto = re.sub(r"[*_`~]+", "", texto)                          # ênfases
    texto = re.sub(r"(?<!\w)#(\w+)", r"\1", texto)                 # hashtag no meio da frase
    texto = re.sub(r"(?<!\w)@(\w+)", r"\1", texto)                 # menções
    texto = sem_emoji(texto)

    for padrao, fala in regras:                                    # antes dos números: "085Tec" etc.
        texto = padrao.sub(fala, texto)

    texto = re.sub(r"R\$\s*(\d+)", r"\1 reais", texto)
    texto = re.sub(r"(\d+)\s*%", r"\1 por cento", texto)
    texto = re.sub(r"\d+", numero_por_extenso, texto)

    # Parágrafos viram pausas; linhas sem pontuação final ganham ponto para o modelo respirar.
    paragrafos = []
    for p in re.split(r"\n\s*\n", texto):
        p = " ".join(l.strip() for l in p.splitlines() if l.strip())
        p = re.sub(r"\s+", " ", p).strip()
        p = p.rstrip(",:;").strip()
        if p and p[-1] not in ".!?…":
            p += "."
        if p:
            paragrafos.append(p)
    return "\n".join(paragrafos)


# ---------------------------------------------------------------- comandos


def cmd_voz(args):
    origem = Path(args.gravacao)
    if not origem.exists():
        sys.exit(f"Gravação não encontrada: {origem}")
    modelo = carregar_modelo()
    if not args.texto:
        print("Sem --texto: transcrevendo a gravação com Whisper (baixa o modelo na primeira vez)…")
        modelo.load_asr_model()
    prompt = modelo.create_voice_clone_prompt(ref_audio=str(origem), ref_text=args.texto)
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    prompt.save(str(destino))
    print(f"Voz salva em {destino}")
    print(f"Transcrição usada: {prompt.ref_text!r}")
    print("Confira se a transcrição bate com o que foi dito; se não, refaça com --texto.")


def listar_entradas(caminhos):
    arquivos = []
    for c in map(Path, caminhos):
        if c.is_dir():
            arquivos += sorted(p for p in c.iterdir() if p.suffix.lower() in EXTENSOES)
        elif c.exists():
            arquivos.append(c)
        else:
            print(f"Ignorando (não existe): {c}")
    return arquivos


def salvar(audio, taxa, destino):
    import soundfile as sf

    if destino.suffix == ".wav":
        sf.write(destino, audio, taxa)
        return
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, audio, taxa)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-codec:a", "libmp3lame", "-q:a", "2", str(destino)],
            check=True,
        )


def cmd_gerar(args):
    from omnivoice.models.omnivoice import VoiceClonePrompt

    entradas = listar_entradas(args.entradas)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    regras = carregar_pronuncia()

    pendentes = []
    for arq in entradas:
        destino = saida / f"{arq.stem}.{args.formato}"
        if destino.exists() and destino.stat().st_mtime >= arq.stat().st_mtime and not args.forcar:
            print(f"✓ {arq.name} (já narrado)")
            continue
        texto = preparar_texto(arq.read_text(encoding="utf-8"), regras)
        if not texto:
            print(f"Ignorando (vazio depois da limpeza): {arq.name}")
            continue
        if args.mostrar_texto:
            print(f"--- {arq.name} ---\n{texto}\n")
        pendentes.append((arq, destino, texto))

    if not pendentes or args.mostrar_texto:
        return

    voz = Path(args.voz)
    if not voz.exists():
        sys.exit(f"Perfil de voz não encontrado em {voz}. Rode primeiro: python narrar.py voz sua_gravacao.m4a")

    modelo = carregar_modelo()
    prompt = VoiceClonePrompt.load(str(voz))
    for arq, destino, texto in pendentes:
        print(f"▶ {arq.name}…", end=" ", flush=True)
        audio = modelo.generate(
            text=texto,
            language="pt",
            voice_clone_prompt=prompt,
            speed=args.velocidade,
            num_step=args.passos,
        )[0]
        salvar(audio, modelo.sampling_rate, destino)
        print(f"{len(audio) / modelo.sampling_rate:.0f}s → {destino}")


def main():
    ap = argparse.ArgumentParser(description="Narra postagens da 085Tec com a sua voz (OmniVoice).")
    sub = ap.add_subparsers(dest="comando", required=True)

    v = sub.add_parser("voz", help="cria o perfil de voz a partir de uma gravação sua (5–20 s)")
    v.add_argument("gravacao")
    v.add_argument("--texto", help="o que foi dito na gravação (sem isso, transcreve com Whisper)")
    v.add_argument("--saida", default=str(VOZ_PADRAO))
    v.set_defaults(func=cmd_voz)

    g = sub.add_parser("gerar", help="gera o áudio de cada postagem")
    g.add_argument("entradas", nargs="+", help="arquivos .txt/.md ou pastas")
    g.add_argument("--voz", default=str(VOZ_PADRAO))
    g.add_argument("--saida", default=str(SAIDA_PADRAO))
    g.add_argument("--formato", choices=["mp3", "wav"], default="mp3")
    g.add_argument("--velocidade", type=float, default=None, help="1.1 = 10%% mais rápido")
    g.add_argument("--passos", type=int, default=32, help="passos de decodificação (mais = melhor e mais lento)")
    g.add_argument("--forcar", action="store_true", help="regera mesmo os que já têm áudio")
    g.add_argument("--mostrar-texto", action="store_true", help="só mostra o texto que seria lido, sem gerar")
    g.set_defaults(func=cmd_gerar)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
