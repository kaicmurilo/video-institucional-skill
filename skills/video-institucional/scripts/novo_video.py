"""Cria a pasta de trabalho de um vídeo novo a partir do modelo.

Uso: python scripts/novo_video.py <pasta-do-video> [--forcar]

Copia roteiro.json, cenas.html, mock_api.py, as logos e o app de exemplo. Sem --forcar, não sobrescreve
arquivos que já existam (para não perder um roteiro em edição).
"""
import pathlib
import shutil
import sys

from comum import MODELO

if len(sys.argv) < 2:
    raise SystemExit(__doc__)
destino = pathlib.Path(sys.argv[1]).resolve()
forcar = "--forcar" in sys.argv
destino.mkdir(parents=True, exist_ok=True)
copiados, mantidos = [], []
for origem in MODELO.rglob("*"):
    if origem.is_dir() or "__pycache__" in origem.parts:
        continue
    alvo = destino / origem.relative_to(MODELO)
    if alvo.exists() and not forcar:
        mantidos.append(alvo.name)
        continue
    alvo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, alvo)
    copiados.append(str(alvo.relative_to(destino)))
print(f"Pasta do vídeo: {destino}")
print("copiados:", ", ".join(copiados) or "nenhum")
if mantidos:
    print("mantidos (já existiam):", ", ".join(mantidos))
print("""
Próximos passos:
  1. Edite roteiro.json (blocos e falas), cenas.html (slides) e mock_api.py (dados fictícios da demo).
  2. python scripts/gravar.py <pasta> --previa      -> prints de cada cena e frase, para aprovação
  3. python scripts/narrar.py <pasta>               -> narração (edge ou eleven)
  4. python scripts/gravar.py <pasta>               -> gravação 1080p
  5. python scripts/montar.py <pasta> <video.mp4>   -> vídeo final e capa""")
