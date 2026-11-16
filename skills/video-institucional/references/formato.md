# Estrutura dos vídeos

## Institucional (de 4 a 6 min)

São dois tipos de bloco, intercalados:
- **cena**: um slide animado em `cenas.html`;
- **demo**: a gravação da ferramenta real.

| # | Bloco | Tipo | Conteúdo |
|---|---|---|---|
| 1 | Abertura | cena escura | Nome do produto, uma frase de promessa e a ideia-chave (por exemplo, "a IA aponta, o especialista decide"). |
| 2 | A dor | cena | O fluxo de hoje em cartões com setas (quem faz o quê) e 2 cartões em laranja com os problemas. |
| 3 | A proposta | cena | De 2 a 4 pilares numerados, com o principal em destaque, e uma nota de rodapé. |
| 4 | O que vem (opcional) | cena | Um roadmap em pílulas: agora, em seguida e depois. Sem datas, se ainda não houver. |
| 5 | Mapa das telas | cena com diagrama | Entrada → telas → saída, com uma seta de retorno (o ciclo de melhoria). Cada caixa aparece com a frase que fala dela. Termina com "Agora, um caso fictício". |
| 6 | Estudo de caso, parte 1 | demo | As primeiras telas, com o caso entrando na ferramenta. |
| 7 | Por trás da tela | cena com diagrama | De 5 a 7 passos numerados do que acontece nos bastidores, em linguagem de negócio. |
| 8 | Estudo de caso, parte 2 | demo | O teste ou a análise, com o resultado e a 1ª saída (exportação). |
| 9 | Vinheta | cena escura | A virada de fase, por exemplo "até aqui, a análise; daqui em diante, a decisão". |
| 10 | Estudo de caso, parte 3 | demo | A decisão humana e a saída final (exportação para o cliente). |
| 11 | Fechamento | cena escura | De 3 a 4 ganhos e a frase-princípio do produto. |

**Demo, tela a tela:**
- Cada bloco `demo` tem um `card` com `tela`, `bloco`, `entrega`, `faz`, `motivo` e `ganho`, que aparece no painel lateral.
- O item que a narração está falando acende (ação `painel`).
- O dado citado na frase leva uma marcação âmbar (ação `marcar`).
- A legenda mostra a frase falada.
- A navegação é feita clicando no menu, como um usuário faria.

**Fórmula da fala na demo:**
> "Primeira tela: <nome>. <o que faz, citando o dado do caso>. A motivação: <dor>. O ganho: <ganho>."

**Ritmo:** de 2 a 4 frases por bloco, cada frase com até cerca de 25 palavras. A voz edge-tts a +12% fala cerca de 2,6 palavras por segundo.

## Propaganda (de 15 a 60 s)

| Momento | Duração | Conteúdo |
|---|---|---|
| Gancho | 2–3 s | Uma frase forte sobre a dor ou o resultado, em tipografia enorme. |
| Problema | 3–4 s | O custo de não ter a ferramenta. |
| Solução | 3–5 s | O produto, com um mockup estilizado da tela principal. |
| Prova / diferencial | 4–8 s | 2 ou 3 diferenciais com animação (motores, score, rastreabilidade). |
| Princípio | 2–3 s | A frase-assinatura. |
| CTA | 3 s | A logo, o nome do produto e a chamada ("Fale com a gente"). |

**Regras da propaganda:**
- Para celular: `"tamanho": [1080, 1920]` no roteiro e `html,body` com 1080×1920 no `cenas.html`. Empilhe o conteúdo na vertical, deixe ~250 px livres no topo e ~350 px embaixo (interface do Reels/Stories) e use texto de 110 a 150 px.
- Uma ideia por cena e texto grande, de 90 a 140 px.
- Movimento em toda cena, com `data-delay` para escalonar.
- Sem legenda: o próprio texto carrega a mensagem e funciona sem som.
- Números nos mockups só fictícios.
- Trilha baixa (volume de 0,18 a 0,25) por baixo da voz.

## Identidade visual

| Elemento | Valor |
|---|---|
| Navy | `#14213D` |
| Azul | `#1F6FD1` |
| Azul claro | `#7FB2F0` |
| Laranja | `#E07A1F` |
| Verde | `#2E7D4F` |
| Fundo | `#F7F8F6` |
| Destaque | âmbar `#F59E0B` |
| Fonte | Plus Jakarta Sans |
| Logos | `marca/logo-branca.png` em cenas escuras, `marca/logo-azul.png` em cenas claras (marcadores "SUA MARCA": troque pela logo do cliente) |
