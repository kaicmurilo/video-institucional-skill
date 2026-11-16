"""API fictícia da demonstração (modelo).

O gravador intercepta as requisições do navegador que casam com "demo.interceptar" do roteiro.json
e chama responder(...) deste módulo para cada uma:

    responder(metodo, caminho, query, corpo) -> None | (status, content_type, corpo)

- Devolver None significa "não tratei": o gravador deixa a requisição seguir para a rede se
  "demo.deixar_passar" for true; se for false, responde 404.
- corpo pode ser str, bytes, dict ou list (dict/list viram JSON automaticamente).
- O estado fica em memória (variável ESTADO) e é recriado sempre que o módulo é carregado, ou seja,
  a cada gravação. Por isso a decisão tomada na tela de Decisão "flui" até o fim do vídeo.

Como adaptar ao seu projeto
---------------------------
1. Produto só de demonstração (como este exemplo): troque app-exemplo/index.html pelo seu protótipo
   estático e escreva aqui as rotas /api/... com dados fictícios.
2. Front e back-end reais rodando na sua máquina: aponte "demo.url_base" para o servidor de
   desenvolvimento (ex.: http://localhost:5173) e:
     - use "deixar_passar": true e trate aqui só o que precisa ser forçado (um caso fictício,
       uma resposta lenta da IA, uma exportação), devolvendo None para todo o resto; ou
     - apague o "mock" do roteiro e grave direto contra o seu ambiente local, com banco de dados fictício.
   Nunca grave com dados reais de clientes ou pessoas: o vídeo é institucional.
3. Para acrescentar uma rota: escreva uma função def minha_rota(m, query, corpo) e inclua uma linha em
   ROTAS com (MÉTODO, expressão regular do caminho, função). Grupos da expressão chegam em m.group(1)...
"""
from __future__ import annotations

import copy
import json
import pathlib
import re

PASTA = pathlib.Path(__file__).parent

# ---------------------------------------------------------------------------
# Dados fictícios. Pessoas marcadas "(fictício)"; IDs e valores inventados.
# ---------------------------------------------------------------------------
PEDIDOS = [
    {"id": "PED-0137", "colaborador": "Marcos Lima (fictício)", "area": "Comercial", "categoria": "Hospedagem",
     "data": "14/10/2026", "estabelecimento": "Hotel Exemplo Centro", "valor": 1890.00, "limite": 600.00,
     "limite_obs": "por noite (1 noite)", "recibo": "55821", "risco": "Alto", "status": "aguardando",
     "sinal": "Recibo repetido e valor 3x acima do limite",
     "apontamento": "O valor de R$ 1.890,00 é 3,1 vezes o limite da política para uma noite de hospedagem. "
                    "O recibo nº 55821 já foi anexado ao PED-0112, de outro colaborador, no mês anterior.",
     "confianca": "apontamento apoiado em 2 evidências",
     "evidencias": ["Recibo nº 55821 também consta no PED-0112 (set/2026, Paula Dias, fictício)",
                    "Média de hospedagem da área Comercial: R$ 540,00 por noite",
                    "Sem viagem registrada na agenda para 14/10/2026"]},
    {"id": "PED-0129", "colaborador": "Ana Ribeiro (fictício)", "area": "Marketing", "categoria": "Alimentação",
     "data": "11/10/2026", "valor": 412.50, "risco": "Médio", "status": "aguardando",
     "sinal": "Despesa de fim de semana sem viagem associada"},
    {"id": "PED-0141", "colaborador": "Carlos Prado (fictício)", "area": "Operações", "categoria": "Transporte",
     "data": "17/10/2026", "valor": 386.00, "risco": "Médio", "status": "aguardando",
     "sinal": "Quilometragem acima da rota informada"},
    {"id": "PED-0118", "colaborador": "Beatriz Nunes (fictício)", "area": "Comercial", "categoria": "Hospedagem",
     "data": "06/10/2026", "valor": 980.00, "risco": "Médio", "status": "aguardando",
     "sinal": "Diária acima da média da cidade"},
    {"id": "PED-0144", "colaborador": "Rafael Costa (fictício)", "area": "TI", "categoria": "Material",
     "data": "20/10/2026", "valor": 254.90, "risco": "Baixo", "status": "aguardando",
     "sinal": "Item fora da lista de materiais reembolsáveis"},
]

VALIDADOS = [  # 12 casos já decididos no mês (fictícios)
    {"id": f"PED-{n:04d}", "decisao": d, "motivo": mt, "autor": "Júlia Souza (fictício)"}
    for n, d, mt in [
        (101, "confirmado", "Nota fiscal com data rasurada"), (103, "descartado", "Viagem aprovada pelo gestor"),
        (104, "confirmado", "Pedido em duplicidade"), (106, "descartado", "Valor dentro da exceção da área"),
        (107, "confirmado", "Recibo sem CNPJ"), (108, "descartado", "Evento corporativo autorizado"),
        (109, "confirmado", "Despesa pessoal"), (110, "descartado", "Erro de categoria corrigido"),
        (111, "confirmado", "Quilometragem incompatível"), (113, "descartado", "Hospedagem em alta temporada"),
        (114, "confirmado", "Nota emitida para outra empresa"), (116, "descartado", "Reembolso parcial já ajustado"),
    ]
]

RESUMO = {"competencia": "10/2026", "atualizado": "hoje, 08:00", "pedidos": 248, "valor_total": 96410.35,
          "conferidos_pct": 100, "sinalizados": 19, "valor_sinalizado": 23740.00}


def _novo_estado():
    return {"pedidos": copy.deepcopy(PEDIDOS), "validados": copy.deepcopy(VALIDADOS)}


ESTADO = _novo_estado()


def reiniciar():
    """Volta os dados ao estado inicial (útil para gravar de novo sem recarregar o módulo)."""
    global ESTADO
    ESTADO = _novo_estado()


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
def pagina_inicial(m, query, corpo):
    return 200, "text/html; charset=utf-8", (PASTA / "app-exemplo" / "index.html").read_text(encoding="utf-8")


def resumo(m, query, corpo):
    return 200, "application/json", RESUMO


def listar_pedidos(m, query, corpo):
    itens = ESTADO["pedidos"]
    status = _primeiro(query.get("status"))
    if status:
        itens = [p for p in itens if p["status"] == status]
    return 200, "application/json", itens


def detalhe_pedido(m, query, corpo):
    pedido = next((p for p in ESTADO["pedidos"] if p["id"] == m.group(1)), None)
    if pedido is None:
        return 404, "application/json", {"code": "nao_encontrado", "message": f"Pedido {m.group(1)} não existe"}
    return 200, "application/json", pedido


def decidir(m, query, corpo):
    dados = json.loads(corpo or "{}")
    pedido = next((p for p in ESTADO["pedidos"] if p["id"] == m.group(1)), None)
    if pedido is None or dados.get("decisao") not in ("confirmado", "descartado") or not dados.get("motivo"):
        return 400, "application/json", {"code": "decisao_invalida", "message": "Informe decisão e motivo"}
    pedido["status"] = dados["decisao"]
    caso = {"id": pedido["id"], "decisao": dados["decisao"], "motivo": dados["motivo"], "autor": "Júlia Souza (fictício)"}
    ESTADO["validados"].insert(0, caso)  # o mais recente aparece primeiro na tabela
    return 201, "application/json", caso


def listar_validados(m, query, corpo):
    return 200, "application/json", ESTADO["validados"]


def exportar(m, query, corpo):
    # Na demo não geramos o arquivo de verdade: o gravador mostra um aviso de download com a ação "exportar".
    return 201, "application/json", {"arquivo": "casos-validados.xlsx", "linhas": len(ESTADO["validados"])}


# (MÉTODO, expressão regular do caminho, função). A primeira que casar responde.
ROTAS = [
    ("GET", r"/(index\.html)?", pagina_inicial),
    ("GET", r"/api/resumo", resumo),
    ("GET", r"/api/pedidos", listar_pedidos),
    ("GET", r"/api/pedidos/([A-Z]+-\d+)", detalhe_pedido),
    ("POST", r"/api/pedidos/([A-Z]+-\d+)/decisao", decidir),
    ("GET", r"/api/validados", listar_validados),
    ("POST", r"/api/exportacoes", exportar),
]


def _primeiro(valor):
    """query pode chegar como {"k": "v"} ou {"k": ["v"]} (parse_qs); aceita os dois."""
    if isinstance(valor, list):
        return valor[0] if valor else None
    return valor


def responder(metodo: str, caminho: str, query: dict, corpo: str | None):
    """Return None (not handled) or (status:int, content_type:str, corpo: str|bytes|dict|list). dict/list -> JSON."""
    caminho = caminho.split("?", 1)[0] or "/"
    for met, padrao, funcao in ROTAS:
        if met == metodo.upper():
            m = re.fullmatch(padrao, caminho)
            if m:
                return funcao(m, query or {}, corpo)
    return None  # não tratado: o gravador decide (deixar passar ou 404)


if __name__ == "__main__":
    # Teste rápido: python mock_api.py
    print(responder("GET", "/api/resumo", {}, None))
    print(responder("POST", "/api/pedidos/PED-0137/decisao", {}, json.dumps({"decisao": "confirmado", "motivo": "teste"})))
    print(len(responder("GET", "/api/validados", {}, None)[2]), "validados")
