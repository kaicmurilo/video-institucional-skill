# Skill "video-institucional"

Esta skill cria, no Claude Code, vídeos narrados em 1080p do seu produto, em dois formatos:
- **Institucional** (4 a 6 min): a dor, a proposta, o mapa das telas e um estudo de caso fictício gravado na sua ferramenta, com painel "O que faz / Por que existe / Ganho".
- **Propaganda** (15 a 60 s): vídeo de venda para site e marketing, com tipografia animada e trilha.

## Instalar (1 minuto)

Salve o zip em qualquer pasta, por exemplo Downloads, e escreva no Claude Code:

> instala a skill deste zip: C:\Users\<seu usuario>\Downloads\video-institucional.zip

O Claude descompacta o zip em `C:\Users\<seu usuario>\.claude\skills\video-institucional\`. Se preferir fazer à mão, basta descompactar nessa pasta, de modo que o `SKILL.md` fique em `...\.claude\skills\video-institucional\SKILL.md`. Depois, abra uma sessão nova do Claude Code.

## Usar

Dentro do projeto, peça:

> cria um vídeo institucional do meu projeto

ou

> cria uma propaganda de 30 segundos do produto

Também dá para chamar direto com `/video-institucional`.

O Claude confere o ambiente e pergunta o que faltar (público, caso fictício, telas). Antes de gravar, ele mostra o roteiro e uma prévia em imagens para você aprovar.

## Pré-requisitos

O próprio Claude confere com `scripts/verificar_ambiente.py` e mostra os comandos para instalar o que faltar:
- Python 3.10 ou mais novo;
- `pip install playwright edge-tts requests`;
- `python -m playwright install chromium` (ou o Edge, que já vem no Windows);
- ffmpeg (no Windows: `winget install Gyan.FFmpeg`).

## Bom saber

- **Só dados fictícios.** A demo grava a ferramenta com respostas de API simuladas e não grava nada em banco.
- **Voz:** a padrão é grátis (edge-tts, voz Francisca). Para uma voz paga pelo OpenRouter (Microsoft MAI, ElevenLabs, Gemini), defina `OPENROUTER_API_KEY` e peça "narra com o OpenRouter". A ElevenLabs direta também funciona, com `ELEVENLABS_API_KEY` e `ELEVEN_VOICE_ID`.
- **Trilha:** a da propaganda é sintetizada e provisória. Antes de publicar, troque por uma trilha licenciada.
