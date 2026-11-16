"""Gera a narração frase a frase e grava audio/narracao.json com a duração de cada frase.

Uso: python scripts/narrar.py <pasta> [edge|openrouter|eleven]

- edge (padrão): voz provisória grátis (edge-tts). Voz e velocidade vêm de "voz" e "velocidade" do roteiro.
- openrouter: vozes do OpenRouter (Microsoft MAI, ElevenLabs, Gemini...), com a chave em OPENROUTER_API_KEY.
  Modelo e voz vêm de "openrouter" no roteiro: {"modelo": "microsoft/mai-voice-2.1", "voz": "pt-BR-Rafael:MAI-Voice-2.1",
  "instrucoes": "tom confiante", "velocidade": 1.1}. OPENROUTER_MODELO e OPENROUTER_VOZ sobrepõem (para comparar vozes).
  Lista de modelos e vozes: https://openrouter.ai/api/v1/models?output_modalities=speech
- eleven: ElevenLabs direto, com as variáveis de ambiente ELEVENLABS_API_KEY e ELEVEN_VOICE_ID (nunca no arquivo).
Frases que não mudaram (mesmo texto, motor e voz) não são geradas de novo.
"""
import asyncio
import json
import os
import re
import sys

from comum import duracao, ffmpeg, pasta_arg, roteiro

pasta = pasta_arg()
motor = sys.argv[2] if len(sys.argv) > 2 else "edge"
if motor not in ("edge", "openrouter", "eleven"):
    raise SystemExit("motor deve ser 'edge', 'openrouter' ou 'eleven'")
rot = roteiro(pasta)
voz = rot.get("voz", "pt-BR-FranciscaNeural")
vel = rot.get("velocidade", "+12%")
if motor == "eleven":
    for v in ("ELEVENLABS_API_KEY", "ELEVEN_VOICE_ID"):
        if not os.environ.get(v):
            raise SystemExit(f"defina a variável de ambiente {v}")
    voz = os.environ["ELEVEN_VOICE_ID"]
OR = dict(rot.get("openrouter") or {})
if motor == "openrouter":
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("defina a variável de ambiente OPENROUTER_API_KEY")
    OR["modelo"] = os.environ.get("OPENROUTER_MODELO") or OR.get("modelo") or "microsoft/mai-voice-2.1"
    OR["voz"] = os.environ.get("OPENROUTER_VOZ") or OR.get("voz") or "pt-BR-Rafael:MAI-Voice-2.1"
    voz = f"{OR['modelo']}|{OR['voz']}|{OR.get('instrucoes', '')}|{OR.get('velocidade', '')}"

A = pasta / "audio"
A.mkdir(exist_ok=True)
idx = A / "narracao.json"
antigo = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else {}


async def edge(texto, out):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=vel).save(str(out))


def eleven(texto, out):
    import requests
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
        json={"text": texto, "model_id": "eleven_multilingual_v2", "language_code": "pt",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True}},
        timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def openrouter(texto, out):
    import requests
    corpo = {"model": OR["modelo"], "input": texto, "voice": OR["voz"], "response_format": "mp3"}
    if OR.get("instrucoes"):
        corpo["instructions"] = OR["instrucoes"]
    if OR.get("velocidade"):
        corpo["speed"] = float(OR["velocidade"])
    h = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}

    def post():
        import time
        for tentativa in range(5):   # 429/5xx: espera e tenta de novo
            r = requests.post("https://openrouter.ai/api/v1/audio/speech", headers=h, json=corpo, timeout=180)
            if r.status_code != 429 and r.status_code < 500:
                return r
            time.sleep(float(r.headers.get("Retry-After") or 0) or 5 * (tentativa + 1))
        return r
    r = post()
    if r.status_code == 400 and "speed" in corpo and "speed" in r.text.lower():
        corpo.pop("speed")   # modelo não aceita velocidade
        r = post()
    if r.status_code == 400:  # alguns modelos (ex.: Gemini) só devolvem PCM 24 kHz
        corpo["response_format"] = "pcm"
        r = post()
        if r.ok:
            pcm = out.with_suffix(".pcm")
            pcm.write_bytes(r.content)
            ffmpeg(["-f", "s16le", "-ar", "24000", "-ac", "1", "-i", pcm, "-c:a", "libmp3lame", "-b:a", "128k", out])
            pcm.unlink()
            return
    if not r.ok:
        raise SystemExit(f"OpenRouter {r.status_code}: {r.text[:400]}")
    out.write_bytes(r.content)


PRONUNCIA = rot.get("pronuncia", {})


def falado(texto: str) -> str:
    """Texto enviado à voz: troca termos (marcas, palavras em inglês) pela grafia de como se falam."""
    for termo in sorted(PRONUNCIA, key=len, reverse=True):
        texto = re.sub(rf"(?<!\w){re.escape(termo)}(?!\w)", PRONUNCIA[termo], texto, flags=re.IGNORECASE)
    return texto


novo, total, geradas = {}, 0.0, 0
for b in rot["blocos"]:
    novo[b["id"]] = []
    velhas = {(x.get("falado", x["texto"]), x.get("motor"), x.get("voz")): x for x in antigo.get(b["id"], [])}
    for k, f in enumerate(b["frases"]):
        arq = A / f"{b['id']}_{k:02d}.mp3"
        fala = falado(f["texto"])
        chave = (fala, motor, voz)
        v = velhas.get(chave)
        if v and (A / v["arquivo"]).exists():
            if v["arquivo"] != arq.name:
                (A / v["arquivo"]).replace(arq)
            d = v["d"]
        else:
            bruto = arq.with_suffix(".bruto.mp3")
            if motor == "edge":
                asyncio.run(edge(fala, bruto))
            elif motor == "openrouter":
                openrouter(fala, bruto)
            else:
                eleven(fala, bruto)
            # tira o silêncio do começo e do fim, para o sincronismo ficar exato
            ffmpeg(["-i", bruto, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.05",
                    "-c:a", "libmp3lame", "-b:a", "128k", arq])
            bruto.unlink()
            d = round(duracao(arq), 3)
            geradas += 1
        novo[b["id"]].append({"texto": f["texto"], "falado": fala, "d": d, "arquivo": arq.name, "motor": motor, "voz": voz})
        total += d
    print(f"{b['id']}: {len(b['frases'])} frases")
idx.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{geradas} frases geradas; narração total ~{total + 0.4 * sum(len(v) for v in novo.values()):.0f} s")
