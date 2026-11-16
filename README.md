# video-institucional (plugin do Claude Code)

Skill que gera vídeos narrados em pt-BR (1080p) de um produto de software: tutorial/institucional com demo gravada na ferramenta real, ou propaganda curta. Instruções da skill: [`skills/video-institucional/SKILL.md`](skills/video-institucional/SKILL.md). Guia de uso: [`LEIA-ME.md`](skills/video-institucional/LEIA-ME.md).

## Instalação

No Claude Code:

```
/plugin marketplace add kaicmurilo/video-institucional-skill
/plugin install video-institucional@video-institucional-skill
```

Ou pelo terminal:

```bash
claude plugin marketplace add kaicmurilo/video-institucional-skill
claude plugin install video-institucional@video-institucional-skill
```

O repositório é privado: a máquina precisa de acesso ao GitHub (`gh auth login` ou chave SSH).

Depois, confira o ambiente (Python 3.10+, playwright, edge-tts, ffmpeg):

```bash
python3 ~/.claude/plugins/cache/video-institucional-skill/video-institucional/*/skills/video-institucional/scripts/verificar_ambiente.py
```

## Atualizar

```bash
claude plugin marketplace update video-institucional-skill
claude plugin update video-institucional@video-institucional-skill
```

## Melhorias

Problemas encontrados em uso viram issues neste repositório. Cada correção sobe a `version` em `.claude-plugin/plugin.json` (o Claude Code só atualiza o plugin quando a versão muda).

## Estrutura

```
.claude-plugin/
  plugin.json        # manifesto do plugin
  marketplace.json   # marketplace com este único plugin
skills/video-institucional/
  SKILL.md           # instruções da skill
  scripts/           # pipeline: verificar, gravar, narrar, montar
  modelo/, modelo-propaganda/, references/
```
