"""Monta o vídeo final a partir de brutos/ (gravar.py) e audio/ (narrar.py), e gera a imagem de capa.

Uso: python scripts/montar.py <pasta> <saida.mp4>

Cada bloco vira um trecho com fade e com o áudio de cada frase no instante em que ela começou na gravação.
Se o roteiro tiver "trilha": {"arquivo": "...mp3", "volume": 0.2}, a trilha entra por baixo da voz no vídeo
inteiro, com fade no começo e no fim. Saída 1920x1080, 30 fps, x264 crf 18.
"""
import json
import pathlib
import sys

from comum import AAC, ALTURA, FPS, LARGURA, X264, duracao, ffmpeg, narracao, pasta_arg, roteiro

pasta = pasta_arg()
if len(sys.argv) < 3:
    raise SystemExit(__doc__)
saida = pathlib.Path(sys.argv[2]).resolve()
rot = roteiro(pasta)
narr = narracao(pasta, rot)
fade = 0.2 if rot.get("formato") == "propaganda" else 0.4
A, B = pasta / "audio", pasta / "brutos"
W = pasta / "partes"
W.mkdir(exist_ok=True)
for f in W.glob("*"):
    f.unlink()

def um_quadro_por_slot(quadros):
    """Mantém o último quadro de cada fatia de 1/FPS s, carimbado no início da fatia.

    O screencast manda até ~60 quadros/s e cada quadro abaixo dura no mínimo 1/FPS s;
    sem isso o vídeo estica e atrasa em relação à narração.
    """
    por_slot = {}
    for q in sorted(quadros, key=lambda q: q["t"]):
        por_slot[int(q["t"] * FPS + 1e-6)] = q
    return [{**q, "t": slot / FPS} for slot, q in sorted(por_slot.items())]


partes = []
for i, bloco in enumerate(rot["blocos"]):
    d = B / bloco["id"]
    if not (d / "log.json").exists():
        raise SystemExit(f"falta a gravação do bloco '{bloco['id']}'. Rode: python scripts/gravar.py <pasta> --blocos {bloco['id']}")
    log = json.loads((d / "log.json").read_text(encoding="utf-8"))
    if len(log["frases"]) != len(bloco["frases"]):
        raise SystemExit(f"a gravação do bloco '{bloco['id']}' é de outra versão do roteiro. Regrave esse bloco.")
    fim = log["fim"]
    qs = um_quadro_por_slot(log["quadros"])
    lista = d / "quadros.txt"
    with open(lista, "w", encoding="utf-8") as fh:
        for j, q in enumerate(qs):
            ini = 0.0 if j == 0 else q["t"]
            prox = qs[j + 1]["t"] if j + 1 < len(qs) else fim
            fh.write(f"file 'quadros/{q['arquivo']}'\nduration {max(1 / FPS, prox - ini):.4f}\n")
        fh.write(f"file 'quadros/{qs[-1]['arquivo']}'\n")
    entradas = ["-f", "concat", "-safe", "0", "-i", "quadros.txt"]
    filtros = [f"[0:v]scale={LARGURA}:{ALTURA}:flags=lanczos,fps={FPS},format=yuv420p,"
               f"fade=t=in:st=0:d={fade},fade=t=out:st={fim - fade:.3f}:d={fade}[v]"]
    for k, t in enumerate(log["frases"]):
        entradas += ["-i", str(A / narr[bloco["id"]][k]["arquivo"])]
        ms = int(t * 1000)
        filtros.append(f"[{k + 1}:a]aresample=44100,adelay={ms}|{ms}[a{k}]")
    n = len(log["frases"])
    filtros.append("".join(f"[a{k}]" for k in range(n)) + f"amix=inputs={n}:normalize=0:dropout_transition=0,apad,atrim=0:{fim:.3f}[a]")
    out = W / f"{i:02d}_{bloco['id']}.mp4"
    ffmpeg(entradas + ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]", "-t", f"{fim:.3f}"] + X264 + AAC + [out], cwd=d)
    partes.append(out)
    print(f"{bloco['id']}: {fim:.1f} s")

lst = W / "lista.txt"
lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
saida.parent.mkdir(parents=True, exist_ok=True)
trilha = rot.get("trilha")
if trilha:
    unido = W / "unido.mp4"
    ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", unido])
    total = duracao(unido)
    vol = float(trilha.get("volume", 0.2))
    ffmpeg(["-i", unido, "-stream_loop", "-1", "-i", pasta / trilha["arquivo"], "-filter_complex",
            f"[1:a]aresample=44100,volume={vol},afade=t=in:st=0:d=1,afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5,atrim=0:{total:.3f}[m];"
            f"[0:a][m]amix=inputs=2:normalize=0:duration=first[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy"] + AAC + ["-movflags", "+faststart", saida])
else:
    ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", saida])

capa = saida.with_name(saida.stem + " - capa.jpg")
primeiro = json.loads((B / rot["blocos"][0]["id"] / "log.json").read_text(encoding="utf-8"))["fim"]
ffmpeg(["-ss", f"{min(2.5, primeiro * 0.6):.2f}", "-i", saida, "-frames:v", "1", "-q:v", "2", capa])
print(f"vídeo: {saida} ({duracao(saida):.1f} s)\ncapa: {capa}")
