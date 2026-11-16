---
name: video-institucional
description: Cria vídeos narrados em pt-BR, em 1080p, de um produto de software. Há dois formatos. O "institucional" (4 a 6 min) explica a dor, a proposta e o mapa das telas e faz um estudo de caso fictício gravado na ferramenta real, com painel "O que faz / Por que existe / Ganho". A "propaganda" (15 a 60 s) é um vídeo de venda para site e marketing, com tipografia animada e trilha. Use quando pedirem vídeo institucional, vídeo de apresentação, demo narrada, vídeo de venda, propaganda ou vídeo de marketing do produto.
---

# Vídeo institucional e propaganda

Esta skill produz o vídeo inteiro com um pipeline pronto. Não reescreva os scripts: preencha a pasta do vídeo e rode os comandos.

`<SKILL>` é a pasta desta skill (onde está este arquivo). Rode os scripts com `python "<SKILL>/scripts/<script>.py"`.

## Regras que não mudam

1. **Só dados fictícios.** Nada de dados reais, nomes de clientes ou de outras empresas, totais reais ou pessoas reais. Identificadores como `PED-0137` e nomes com "(fictício)". A única marca é a da empresa dona do produto.
2. **Nada é gravado em banco real.** A demo responde a API com `mock_api.py` (dados fictícios) ou roda contra um ambiente local com dados fictícios.
3. **Entrega em arquivos locais:** o `.mp4`, a capa `.jpg` e a pasta do vídeo, que permite regerar tudo. Não publique online.
4. **Chaves só por variável de ambiente** (`OPENROUTER_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVEN_VOICE_ID`). Nunca em arquivo.
5. **Narração em linguagem de negócio:** o que a tela faz e o ganho. Sem "endpoint", "SQL" ou "hash", a menos que o público seja técnico.
6. **Aprovação antes de gravar:** mostre ao usuário o roteiro e a prévia (`--previa`) e só grave e monte depois do ok.

## Passo a passo

1. **Ambiente:** `python "<SKILL>/scripts/verificar_ambiente.py"`. Instale o que faltar, seguindo os comandos que ele mostra.
2. **Entenda o produto.** Leia o README e as telas e rotas do front do projeto. Pergunte ao usuário, numa única mensagem, só o que não der para descobrir:
   - formato: institucional ou propaganda;
   - público;
   - estudo de caso fictício;
   - telas que entram;
   - como subir a aplicação localmente.
3. **Crie a pasta do vídeo** dentro do projeto, por exemplo `docs/video-institucional/`:
   - institucional: `python "<SKILL>/scripts/novo_video.py" <pasta>`;
   - propaganda: copie `<SKILL>/modelo-propaganda/*` e `<SKILL>/modelo/marca/` para a pasta.
4. **Escreva o roteiro** (`roteiro.json`) e adapte os slides (`cenas.html`). A estrutura dos blocos está em `references/formato.md`. O esquema do roteiro e as ações da demo estão em `references/roteiro.md`.
5. **Demo na ferramenta (só no institucional):**
   1. Suba o front do projeto e descubra as chamadas que ele faz à API, pela aba Network ou pelo código.
   2. Escreva em `mock_api.py` respostas fictícias para essas chamadas.
   3. Aponte `demo.url_base` para o dev server e `demo.interceptar` para o padrão da API, por exemplo `**/api/**`.
   4. Prefira alvos estáveis (`css=[data-testid=...]`, `texto=...`).
   5. Ensaie o fluxo com o app de exemplo (`app-exemplo/`), que já vem funcionando.
6. **Prévia:** `python "<SKILL>/scripts/gravar.py" <pasta> --previa`. Abra `previa/index.html`, confira cada print (alvos certos, nada cortado ou sobreposto à legenda) e mostre ao usuário junto com o roteiro.
7. **Narração:** `python "<SKILL>/scripts/narrar.py" <pasta>`. O padrão é a voz Francisca (edge-tts), grátis, a mesma dos vídeos didáticos já feitos. Para uma voz paga, há duas opções:
   - `... openrouter`, com `OPENROUTER_API_KEY` e `"openrouter": {"modelo", "voz", "instrucoes", "velocidade"}` no roteiro. Vozes em pt-BR testadas: `microsoft/mai-voice-2.1` (Rafael, Caio, Pedro, Luana), `elevenlabs/eleven-multilingual-v2` e `google/gemini-3.8-flash-tts`.
   - `... eleven`, para a ElevenLabs direta.

   Use a mesma voz no vídeo inteiro. Só as frases alteradas são geradas de novo.
8. **Gravação:** `python "<SKILL>/scripts/gravar.py" <pasta>`. Para regravar só um bloco, use `--blocos id1,id2`.
9. **Montagem:** `python "<SKILL>/scripts/montar.py" <pasta> "<pasta>/saida/<Nome do vídeo>.mp4"`. Gera também `<Nome> - capa.jpg`.
10. **Confira o resultado de verdade.** Extraia uns 6 quadros (`ffmpeg -ss <t> -i video.mp4 -frames:v 1 q.jpg`), olhe cada um e confira a duração. Ajuste o que estiver estranho e remonte.
11. **Deixe na pasta** um `LEIA-ME.md` curto, com os comandos para regerar o vídeo.

## Formatos

- **Institucional** (`"formato": "institucional"`): de 4 a 6 min, com cenas e demo intercaladas, legenda em toda frase e painel lateral na demo. Os blocos estão em `references/formato.md`.
- **Propaganda** (`"formato": "propaganda"`): de 15 a 60 s, só cenas. Tem gancho nos primeiros 2 s, tipografia grande e animada, mockups estilizados da interface em HTML, CTA final com a logo e trilha (`"trilha": {"arquivo": "trilha.mp3", "volume": 0.22}`). A trilha provisória sai de `python "<SKILL>/scripts/trilha_provisoria.py" trilha.mp3 <segundos>`; para publicar, troque por uma trilha licenciada. As transições são mais curtas, e as pausas entre frases também.

## Problemas comuns

- **"alvo sem posição" ou timeout na demo:** o texto ou o seletor não existe naquela tela. Rode `--previa` e ajuste o alvo.
- **"sem resposta fictícia para GET /api/...":** falta essa rota em `mock_api.py`. Outra opção é usar `"deixar_passar": true` para ir ao back-end local.
- **"narração desatualizada":** o texto mudou. Rode `narrar.py` de novo.
- **"gravação de outra versão do roteiro":** o número de frases do bloco mudou. Regrave o bloco com `--blocos`.
