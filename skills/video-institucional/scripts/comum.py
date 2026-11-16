"""Funções comuns do pipeline do vídeo institucional (narrar, gravar, montar)."""
import json
import pathlib
import shutil
import subprocess
import sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
MODELO = SKILL / "modelo"
GAP = 0.4            # pausa entre frases (s)
LARGURA, ALTURA, FPS = 1920, 1080, 30   # padrão; o roteiro pode trocar com "tamanho"
X264 = ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
AAC = ["-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def binario(nome: str) -> str:
    p = shutil.which(nome)
    if not p:
        raise SystemExit(f"{nome} não encontrado no PATH. Rode: python scripts/verificar_ambiente.py")
    return p


def rodar(args: list, cwd=None) -> str:
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"falhou: {' '.join(map(str, args[:6]))} ...\n{r.stderr[-2000:]}")
    return r.stdout


def ffmpeg(args: list, cwd=None):
    rodar([binario("ffmpeg"), "-v", "error", "-y"] + [str(a) for a in args], cwd=cwd)


def duracao(arquivo) -> float:
    out = rodar([binario("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arquivo)])
    return float(out.strip())


def pasta_arg(i: int = 1) -> pathlib.Path:
    if len(sys.argv) <= i:
        raise SystemExit("informe a pasta do vídeo (a que tem o roteiro.json)")
    p = pathlib.Path(sys.argv[i]).resolve()
    if not (p / "roteiro.json").exists():
        raise SystemExit(f"não achei {p / 'roteiro.json'}. Crie a pasta com: python scripts/novo_video.py <pasta>")
    return p


def roteiro(pasta: pathlib.Path) -> dict:
    """Lê o roteiro.json e normaliza cada frase para {texto, antes, acoes}."""
    r = json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))
    ids = set()
    for b in r.get("blocos", []):
        if b.get("id") in ids:
            raise SystemExit(f"id de bloco repetido: {b.get('id')}")
        ids.add(b["id"])
        if b.get("tipo") not in ("cena", "demo"):
            raise SystemExit(f"bloco {b['id']}: tipo deve ser 'cena' ou 'demo'")
        frases = []
        for f in b.get("frases", []):
            if isinstance(f, str):
                f = {"texto": f}
            f.setdefault("antes", [])
            f.setdefault("acoes", [])
            if not f.get("texto", "").strip():
                raise SystemExit(f"bloco {b['id']}: frase sem texto")
            frases.append(f)
        if not frases:
            raise SystemExit(f"bloco {b['id']}: sem frases")
        b["frases"] = frases
    if not r.get("blocos"):
        raise SystemExit("roteiro sem blocos")
    return r


def narracao(pasta: pathlib.Path, rot: dict) -> dict:
    p = pasta / "audio" / "narracao.json"
    if not p.exists():
        raise SystemExit("falta a narração. Rode antes: python scripts/narrar.py <pasta>")
    n = json.loads(p.read_text(encoding="utf-8"))
    for b in rot["blocos"]:
        fs = n.get(b["id"])
        if not fs or [x["texto"] for x in fs] != [f["texto"] for f in b["frases"]]:
            raise SystemExit(f"a narração do bloco '{b['id']}' está desatualizada. Rode de novo: python scripts/narrar.py <pasta>")
    return n


def tamanho(rot: dict) -> tuple:
    """(largura, altura) do vídeo: "tamanho": [1080, 1920] no roteiro para vertical (celular)."""
    largura, altura = rot.get("tamanho", [LARGURA, ALTURA])
    return int(largura), int(altura)
