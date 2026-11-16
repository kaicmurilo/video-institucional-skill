"""Confere se a máquina tem o necessário para o pipeline e diz como instalar o que faltar.

Uso: python scripts/verificar_ambiente.py
"""
import asyncio
import importlib.util
import platform
import shutil
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ok = True


def item(nome, passou, como=""):
    global ok
    print(("  [ok]    " if passou else "  [falta] ") + nome + ("" if passou else f"\n          instale com: {como}"))
    ok = ok and passou


so = platform.system()
ff = {"Windows": "winget install Gyan.FFmpeg", "Darwin": "brew install ffmpeg"}.get(so, "sudo apt install ffmpeg")
print("Verificando o ambiente do vídeo institucional:")
item(f"Python 3.10+ (atual {platform.python_version()})", sys.version_info >= (3, 10), "https://www.python.org/downloads/")
item("pacote playwright", importlib.util.find_spec("playwright") is not None, "pip install playwright")
item("pacote edge-tts (voz provisória)", importlib.util.find_spec("edge_tts") is not None, "pip install edge-tts")
item("pacote requests (voz ElevenLabs, opcional)", importlib.util.find_spec("requests") is not None, "pip install requests")
item("ffmpeg", shutil.which("ffmpeg") is not None, ff + "  (depois abra um terminal novo)")
item("ffprobe", shutil.which("ffprobe") is not None, ff)

if importlib.util.find_spec("playwright"):
    async def navegador():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            for kw in ({}, {"channel": "msedge"}, {"channel": "chrome"}):
                try:
                    b = await p.chromium.launch(**kw)
                    await b.close()
                    return kw.get("channel", "chromium")
                except Exception:
                    pass
        return None
    canal = asyncio.run(navegador())
    item(f"navegador para gravar ({canal or 'nenhum'})", canal is not None, "python -m playwright install chromium")

print("\nTudo pronto." if ok else "\nInstale o que falta e rode de novo.")
sys.exit(0 if ok else 1)
