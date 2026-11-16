# roteiro.json, cenas.html e mock_api.py

## roteiro.json

```json
{
 "titulo": "Produto X - vídeo institucional",
 "formato": "institucional",
 "voz": "pt-BR-FranciscaNeural",
 "velocidade": "+12%",
 "trilha": {"arquivo": "trilha.mp3", "volume": 0.22},
 "demo": {
   "url_base": "http://localhost:5173",
   "interceptar": "**/api/**",
   "mock": "mock_api.py",
   "deixar_passar": false,
   "viewport": [1440, 810],
   "escala": 1.3334,
   "painel_largura": 380,
   "legenda_margem_esquerda": 24,
   "caso": "Caso: <nome do caso> (fictício)"
 },
 "blocos": [
  {"id": "abertura", "tipo": "cena", "frases": ["Frase 1.", "Frase 2."]},
  {"id": "tela_x", "tipo": "demo",
   "card": {"tela": "Nome da tela", "bloco": "Etapa", "entrega": "Disponível", "faz": "...", "motivo": "...", "ganho": "..."},
   "frases": [
     {"texto": "Primeira tela: ...", "antes": [{"ir": "/rota"}],
      "acoes": [{"painel": "faz"}, {"marcar": {"alvo": "css=[data-testid=total]", "tipo": "anel", "etiqueta": "37 casos", "spot": true}}]}
   ]}
 ]
}
```

- `tamanho` (opcional): `[largura, altura]` do vídeo. Padrão `[1920, 1080]`; para celular (Reels, Stories, Shorts, WhatsApp) use `[1080, 1920]` e desenhe o `cenas.html` nessa medida.
- `pronuncia` (opcional): `{"termo": "como se fala"}` para marcas e palavras em inglês que a voz lê errado, por exemplo `{"checklist": "tchéc-list", "WhatsApp": "uótsap"}`. Vale só para a voz; a legenda continua com o texto original. Ouça o resultado e ajuste a grafia.
- `ritmo` (opcional): pausas em segundos que substituem as do formato: `entrada` (antes da 1ª frase do bloco), `gap` (entre frases), `saida` (fim do bloco), `final` (fim do vídeo). Para um vídeo menos corrido, use junto com `"velocidade": "-5%"`, por exemplo `{"gap": 0.6, "saida": 0.5}`.
- `formato` aceita `institucional` ou `propaganda`. A `trilha` é opcional. `demo` só é necessário quando houver blocos `demo`.
- Cada **frase** vira um áudio. Ela pode ser texto simples (nas cenas) ou um objeto `{texto, antes, acoes}`:
  - `antes`: ações que rodam **antes** de a frase começar, como navegar, clicar ou digitar. A frase espera essas ações terminarem.
  - `acoes`: ações que rodam **quando a frase começa**, como marcar, painel ou exportar.
- O sincronismo é automático: a gravação anota o instante em que cada frase começou, e a montagem põe o áudio nesse instante.

### Ações da demo (uma chave por objeto)

| Ação | Exemplo | Efeito |
|---|---|---|
| `ir` | `{"ir": "/casos"}` | Navega para `url_base` + rota (recarrega a página). |
| `clicar` | `{"clicar": "texto=Revisão"}` | Mostra o cursor indo até o alvo e clica. |
| `digitar` | `{"digitar": {"em": "css=#busca", "texto": "PED-0137"}}` | Digita como uma pessoa. |
| `rolar` | `{"rolar": "css=#tabela"}` | Rola suavemente até o alvo. |
| `esperar` | `{"esperar": 800}` | Espera, em milissegundos. |
| `marcar` | `{"marcar": {"alvo": "...", "tipo": "anel" \| "sublinhado", "etiqueta": "...", "spot": true}}` | Desenha a marcação âmbar. As marcações são limpas a cada frase. |
| `painel` | `{"painel": "faz" \| "motivo" \| "ganho"}` | Acende o item do painel lateral. |
| `exportar` | `{"exportar": {"arquivo": "casos.xlsx", "detalhe": "12 linhas"}}` | Mostra um aviso de exportação (não baixa nada). |
| `ocultar` | `{"ocultar": ["Nome real"]}` | Esconde textos exatos da tela. |
| `js` | `{"js": "() => document.title = 'x'"}` | Saída de emergência: roda um JavaScript. |

**Alvo:**
- `css=<seletor>`;
- `texto=<texto exato>`;
- ou um texto simples, que pega o primeiro elemento que contém o texto.

## cenas.html (contrato)

- Página fixa de 1920×1080. Cada cena é `<section class="scene" id="<id do bloco>">`; a classe `dark` deixa o fundo escuro.
- Atributos de animação:
  - `data-at="k"`: o elemento fica oculto até a frase `k` (contando de 0) e então recebe a classe `in`;
  - `data-delay="0.4"`: atraso, em segundos, dentro da frase;
  - `data-out="k"`: tira a classe `in` na frase `k`;
  - `data-grp`: o último elemento revelado recebe a classe `active`.
- `<div class="cap"></div>` é a legenda. É opcional e não costuma ser usada na propaganda.
- As funções `window.__mostrar(id)` e `window.__frase(id, k, texto)` precisam existir. Copie as do modelo.

## mock_api.py

```python
def responder(metodo, caminho, query, corpo):
    return None                        # não tratado (404 ou deixar_passar)
    return 200, "application/json", {"total": 37}   # dict/list viram JSON
```

O mock responde só ao que casar com `demo.interceptar`. Os dados são fictícios e podem mudar com um POST, por exemplo para registrar uma decisão. Para gravar contra o back-end local real, com dados fictícios, use `"deixar_passar": true` e simule só o que faltar.
