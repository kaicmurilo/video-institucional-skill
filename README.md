# video-institucional (skill do Claude Code)

Skill que gera vídeos narrados em pt-BR (1080p) de um produto de software: tutorial/institucional com demo gravada na ferramenta real, ou propaganda curta. Instruções da skill: [`SKILL.md`](SKILL.md). Guia de uso: [`LEIA-ME.md`](LEIA-ME.md).

## Instalação

A skill fica em `~/.claude/skills/video-institucional/`. No myvault ela é um submódulo:

```bash
git -C ~/.claude submodule update --init skills/video-institucional
```

Fora do myvault:

```bash
git clone https://github.com/kaicmurilo/video-institucional-skill.git ~/.claude/skills/video-institucional
```

Pré-requisitos: `python3 scripts/verificar_ambiente.py` (Python 3.10+, playwright, edge-tts, ffmpeg).

## Melhorias

Problemas encontrados em uso viram issues neste repositório. Correção → commit aqui (`fix: ...`) → no myvault, `git -C ~/.claude add skills/video-institucional && git commit -m "chore: atualiza skill video-institucional"` para fixar a nova versão.
