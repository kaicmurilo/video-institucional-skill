"""Gera uma trilha de fundo PROVISÓRIA, suave e sem direitos autorais, só com ffmpeg.

Uso: python scripts/trilha_provisoria.py <saida.mp3> <segundos>

O que sai: um "pad" calmo (progressão lenta Cmaj7 - Am7 - Fmaj7 - G6, vozes senoidais com um pouco de
harmônico para aquecer), um baixo macio e um arpejo leve tipo sino, com tremolo discreto, passa-baixa,
eco curto que imita reverb, fade de entrada e de saída e normalização perto de -20 LUFS.
Tudo é sintetizado na hora (aevalsrc), então não há direito autoral de terceiros.

Serve para testar o ritmo do vídeo. Na versão final, troque por uma trilha LICENCIADA
(banco de músicas com licença para uso comercial em site e redes sociais) e guarde o comprovante da licença.
No roteiro.json: "trilha": {"arquivo": "trilha.mp3", "volume": 0.22}.
"""
import pathlib
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Acordes: (baixo, [vozes do pad], [notas do arpejo]) em Hz
ACORDES = [
    (65.41, [261.63, 329.63, 392.00, 493.88], [523.25, 659.25, 783.99, 987.77]),   # Cmaj7
    (55.00, [220.00, 261.63, 329.63, 392.00], [440.00, 523.25, 659.25, 783.99]),   # Am7
    (43.65, [174.61, 220.00, 261.63, 329.63], [349.23, 440.00, 523.25, 659.25]),   # Fmaj7
    (49.00, [196.00, 246.94, 293.66, 329.63], [392.00, 493.88, 587.33, 659.25]),   # G6
]
D = 2.4                 # segundos entre acordes (cada acorde soa 2*D, com crossfade sin² constante)
CICLO = D * len(ACORDES)
PASSO = D / 4           # arpejo: 4 notas por acorde


def voz(f: float, det: float) -> str:
    """Senoide com 2º e 3º harmônicos fracos (timbre quente, entre seno e triângulo)."""
    w = f"2*PI*{f * det:.4f}*t"
    return f"(sin({w})+0.18*sin(2*{w})+0.06*sin(3*{w}))"


def expressao(det: float) -> str:
    termos = []
    for i, (baixo, pad, arp) in enumerate(ACORDES):
        u = f"mod(t-{i * D:.4f}+{CICLO * 4:.4f},{CICLO:.4f})"
        env = f"if(lt({u},{2 * D:.4f}),pow(sin(PI*{u}/{2 * D:.4f}),2),0)"
        soma = "+".join(voz(f, det) for f in pad)
        termos.append(f"{env}*(0.10*({soma})+0.16*sin(2*PI*{baixo * 2 * det:.4f}*t))")
        # arpejo: notas no trecho em que este acorde domina (centro da janela = (i+1)*D)
        for j, f in enumerate(arp):
            ini = (i + 0.5) * D + j * PASSO
            un = f"mod(t-{ini:.4f}+{CICLO * 4:.4f},{CICLO:.4f})"
            env_n = f"if(lt({un},1.6),(1-exp(-90*{un}))*exp(-3.2*{un}),0)"
            termos.append(f"0.07*{env_n}*sin(2*PI*{f * det:.4f}*t)")
    return "+".join(termos)


def main():
    if len(sys.argv) < 3:
        raise SystemExit("uso: python scripts/trilha_provisoria.py <saida.mp3> <segundos>")
    saida = pathlib.Path(sys.argv[1]).resolve()
    seg = float(sys.argv[2].replace(",", "."))
    if seg < 3:
        raise SystemExit("duração mínima: 3 segundos")
    ff = shutil.which("ffmpeg")
    if not ff:
        raise SystemExit("ffmpeg não encontrado no PATH. Rode: python scripts/verificar_ambiente.py")
    saida.parent.mkdir(parents=True, exist_ok=True)

    fade_in, fade_out = min(1.5, seg / 6), min(2.5, seg / 5)
    src = f"aevalsrc=exprs='{expressao(1.0)}|{expressao(1.0025)}':s=44100:d={seg:.3f}"
    filtros = ",".join([
        "tremolo=f=0.25:d=0.12",
        "lowpass=f=2600",
        "highpass=f=40",
        "aecho=0.8:0.75:90|170|260:0.22|0.14|0.08",
        "loudnorm=I=-20:TP=-3:LRA=7",
        "aresample=44100",
        f"afade=t=in:st=0:d={fade_in:.2f}",
        f"afade=t=out:st={seg - fade_out:.2f}:d={fade_out:.2f}",
    ])
    cmd = [ff, "-v", "error", "-y", "-f", "lavfi", "-i", src, "-af", filtros,
           "-c:a", "libmp3lame", "-b:a", "160k", "-ac", "2", str(saida)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"ffmpeg falhou:\n{r.stderr[-2000:]}")

    # conferência rápida de nível (volumedetect)
    r = subprocess.run([ff, "-hide_banner", "-i", str(saida), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    niveis = [l.split("]")[-1].strip() for l in r.stderr.splitlines() if "mean_volume" in l or "max_volume" in l]
    print(f"trilha provisória: {saida} ({seg:.1f} s) | " + " | ".join(niveis))
    print("lembrete: na versão final, use uma trilha licenciada.")


if __name__ == "__main__":
    main()
