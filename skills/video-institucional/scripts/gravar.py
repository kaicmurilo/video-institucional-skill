"""Grava os blocos do roteiro em 1080p: cenas (cenas.html) e demonstração na ferramenta real (blocos "demo").

Uso:
  python scripts/gravar.py <pasta>                    grava tudo (precisa da narração: scripts/narrar.py)
  python scripts/gravar.py <pasta> --blocos a,b       regrava só esses blocos (os demo são sempre gravados juntos,
                                                      porque o estado da ferramenta passa de um para o outro)
  python scripts/gravar.py <pasta> --previa           sem narração: tira um print por frase em previa/ e gera
                                                      previa/index.html, para aprovar o roteiro e conferir os alvos

Como funciona:
- Cada bloco tem a sua pasta em brutos/<id>/ com os quadros (screencast do Chrome via CDP, 1920x1080) e o log.json
  com o instante real em que cada frase começou. A montagem coloca o áudio de cada frase nesse instante, então
  mesmo que uma navegação demore, voz, legenda e marcações continuam em sincronia.
- Demo: as ações "antes" rodam antes da frase (navegar, clicar); as "acoes" rodam quando a frase começa (marcar,
  painel, exportar). As chamadas de rede que casam com demo.interceptar são respondidas por mock_api.py
  (dados fictícios); nada é gravado em banco real.
"""
import argparse
import asyncio
import base64
import html
import importlib.util
import json
import pathlib
import shutil
import sys
import time
from urllib.parse import parse_qsl, urljoin, urlparse

from comum import GAP, narracao, roteiro, tamanho

ap = argparse.ArgumentParser()
ap.add_argument("pasta")
ap.add_argument("--blocos", default="")
ap.add_argument("--previa", action="store_true")
args = ap.parse_args()
PASTA = pathlib.Path(args.pasta).resolve()
if not (PASTA / "roteiro.json").exists():
    raise SystemExit(f"não achei {PASTA / 'roteiro.json'}")
ROT = roteiro(PASTA)
FORMATO = ROT.get("formato", "institucional")
W, H = tamanho(ROT)
RITMO = {"institucional": {"entrada": 0.4, "saida": 0.6, "gap": GAP, "final": 1.2},
         "propaganda": {"entrada": 0.1, "saida": 0.05, "gap": 0.25, "final": 1.0}}[FORMATO]
NARR = None if args.previa else narracao(PASTA, ROT)
DEMO = ROT.get("demo", {})
PAINEL_W = int(DEMO.get("painel_largura", 380))
TIMEOUT = int(DEMO.get("timeout_ms", 10000))

# ---------------------------------------------------------------- camadas sobre a ferramenta (demo)
SETUP = """(cfg) => {
 if (document.getElementById('vd-pn')) return;
 document.documentElement.style.paddingRight = cfg.w + 'px';
 const st = document.createElement('style'); st.id = 'vd-st'; st.textContent = `
  @keyframes vdIn{from{opacity:0;transform:scale(1.12)}to{opacity:1;transform:scale(1)}}
  @keyframes vdUl{from{width:0}to{width:var(--w)}}
  .vd-mk{position:fixed;z-index:2147483000;pointer-events:none;border:4px solid #F59E0B;border-radius:14px;animation:vdIn .45s ease-out both}
  .vd-mk.spot{box-shadow:0 0 0 9999px rgba(15,23,42,.35)}
  .vd-ul{position:fixed;z-index:2147483000;height:6px;border-radius:4px;background:#F59E0B;animation:vdUl .6s ease-out both;pointer-events:none}
  .vd-lb{position:fixed;z-index:2147483001;background:#F59E0B;color:#14213D;font:700 16px 'Plus Jakarta Sans',Segoe UI,Arial,sans-serif;padding:6px 12px;border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,.25);animation:vdIn .45s .15s ease-out both;white-space:nowrap;pointer-events:none}
  .vd-lb::after{content:'';position:absolute;left:20px;top:100%;border:8px solid transparent;border-top-color:#F59E0B}
  .vd-lb.below::after{top:auto;bottom:100%;border-top-color:transparent;border-bottom-color:#F59E0B}
  #vd-pn{position:fixed;right:0;top:0;bottom:0;width:${cfg.w}px;z-index:2147483002;background:#14213D;color:#E6ECF5;font-family:'Plus Jakarta Sans',Segoe UI,Arial,sans-serif;padding:24px;display:flex;flex-direction:column;gap:12px;box-shadow:-10px 0 30px rgba(0,0,0,.2);box-sizing:border-box}
  #vd-pn .tag{font:600 12px 'Plus Jakarta Sans',Segoe UI,Arial;letter-spacing:1.5px;text-transform:uppercase;color:#7FB2F0}
  #vd-pn .tela{font:700 28px/1.15 'Plus Jakarta Sans',Segoe UI,Arial;color:#fff}
  #vd-pn .blk{display:inline-block;background:#1F6FD1;color:#fff;font:600 13px 'Plus Jakarta Sans',Segoe UI,Arial;padding:4px 12px;border-radius:999px}
  #vd-pn .it{border-radius:12px;padding:11px 13px;background:rgba(255,255,255,.06);border-left:5px solid transparent;transition:all .35s}
  #vd-pn .it b{display:block;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:#9FB3CF;margin-bottom:4px}
  #vd-pn .it span{font-size:16px;line-height:1.4}
  #vd-pn .it.on{background:rgba(245,158,11,.16);border-left-color:#F59E0B}
  #vd-pn .it.on b{color:#F59E0B}
  #vd-pn .foot{margin-top:auto;font-size:12px;color:#8FA3C0}
  #vd-cap{position:fixed;left:${cfg.esq}px;right:${cfg.w + 20}px;bottom:16px;z-index:2147483003;background:rgba(20,33,61,.94);color:#F4F6F8;font:500 18px/1.35 'Plus Jakarta Sans',Segoe UI,Arial,sans-serif;padding:11px 18px;border-radius:14px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,.25);min-height:50px;display:flex;align-items:center;justify-content:center}
  #vd-cap:empty{display:none}
  #vd-cur{position:fixed;z-index:2147483004;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;background:rgba(245,158,11,.85);border:3px solid #fff;box-shadow:0 4px 14px rgba(0,0,0,.35);pointer-events:none;transition:left .55s ease,top .55s ease,transform .15s;left:40%;top:40%;opacity:0}
  #vd-cur.on{opacity:1} #vd-cur.press{transform:scale(.7)}
  .vd-toast{position:fixed;left:calc((100% - ${cfg.w}px)/2);top:70px;transform:translateX(-50%);z-index:2147483005;background:#14213D;color:#fff;font:15px 'Plus Jakarta Sans',Segoe UI,Arial;padding:12px 18px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.3)}
  [data-sonner-toaster]{display:none !important}`;
 document.head.appendChild(st);
 for (const [id, tag] of [['vd-pn','div'],['vd-cap','div'],['vd-cur','div']]) { const e = document.createElement(tag); e.id = id; document.body.appendChild(e); }
 window.dispatchEvent(new Event('resize'));
}"""
PAINEL = """([n, total, card, caso]) => { const pn = document.getElementById('vd-pn'); if (!pn) return;
 const esc = s => String(s ?? '').replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
 pn.innerHTML = `<div class="tag">Estudo de caso · tela ${n} de ${total} · dados fictícios</div><div class="tela">${esc(card.tela)}</div>
 <div style="display:flex;gap:8px;flex-wrap:wrap">${card.bloco ? `<span class="blk">${esc(card.bloco)}</span>` : ''}${card.entrega ? `<span class="blk" style="background:#2E7D4F">${esc(card.entrega)}</span>` : ''}</div>
 <div class="it" id="vd-it-faz"><b>O que a tela faz</b><span>${esc(card.faz)}</span></div>
 <div class="it" id="vd-it-motivo"><b>Por que existe</b><span>${esc(card.motivo)}</span></div>
 <div class="it" id="vd-it-ganho"><b>Ganho</b><span>${esc(card.ganho)}</span></div>
 <div class="foot">${esc(caso)}</div>`; }"""
FOCO = "(k) => document.querySelectorAll('#vd-pn .it').forEach(e => e.classList.toggle('on', e.id === 'vd-it-' + k))"
LEGENDA = "(t) => { const c = document.getElementById('vd-cap'); if (c) c.textContent = t; }"
LIMPAR = "() => document.querySelectorAll('.vd-mk,.vd-ul,.vd-lb').forEach(e => e.remove())"
MARCA = """([b, tipo, etiqueta, spot]) => {
 const add = (cls, css) => { const e = document.createElement('div'); e.className = cls; Object.assign(e.style, css); document.body.appendChild(e); return e; };
 const p = 8;
 if (tipo === 'sublinhado') add('vd-ul', {left: b.x + 'px', top: (b.y + b.height + 3) + 'px', '--w': b.width + 'px', width: b.width + 'px'});
 else add('vd-mk' + (spot ? ' spot' : ''), {left: (b.x - p) + 'px', top: (b.y - p) + 'px', width: (b.width + 2*p) + 'px', height: (b.height + 2*p) + 'px'});
 if (etiqueta) { const below = b.y < 70; const l = add('vd-lb' + (below ? ' below' : ''), {left: Math.max(8, b.x - p) + 'px'});
   l.textContent = etiqueta; l.style.top = below ? (b.y + b.height + p + 14) + 'px' : (b.y - p - 14 - 34) + 'px'; }
}"""
CURSOR = "([x, y, press]) => { const c = document.getElementById('vd-cur'); if (!c) return; c.classList.add('on'); c.style.left = x + 'px'; c.style.top = y + 'px'; c.classList.toggle('press', !!press); }"
TOAST = "([a, d]) => { const t = document.createElement('div'); t.className = 'vd-toast'; t.innerHTML = '<b></b><br><span></span>'; t.querySelector('b').textContent = '⬇ ' + a; t.querySelector('span').textContent = d || ''; document.body.appendChild(t); setTimeout(() => t.remove(), 4500); }"
OCULTAR = """(txts) => { for (const t of txts) for (const el of document.querySelectorAll('body *')) { if (el.closest('#vd-pn,#vd-cap')) continue;
 if (el.childElementCount === 0 && el.textContent.trim() === t) el.style.visibility = 'hidden'; } }"""


class Tela:
    """Uma aba gravada por screencast. Os quadros vão para a pasta do bloco atual, com o tempo desde o início dele."""

    def __init__(self, page, viewport, escala):
        self.page, self.dir, self.t0, self.quadros, self.n = page, None, 0.0, [], 0
        self.w, self.h, self.escala = viewport[0], viewport[1], escala

    async def iniciar(self):
        self.cdp = await self.page.context.new_cdp_session(self.page)
        self.cdp.on("Page.screencastFrame", self._quadro)
        self.page.on("framenavigated", lambda fr: asyncio.ensure_future(self.ligar()) if fr == self.page.main_frame else None)

    def _quadro(self, f):
        asyncio.ensure_future(self.cdp.send("Page.screencastFrameAck", {"sessionId": f["sessionId"]}))
        if self.dir is None:
            return
        t = float(f.get("metadata", {}).get("timestamp") or time.time()) - self.t0
        if t < 0:
            return
        nome = f"{self.n:06d}.jpg"
        self.n += 1
        (self.dir / "quadros" / nome).write_bytes(base64.b64decode(f["data"]))
        self.quadros.append({"arquivo": nome, "t": round(t, 4)})

    async def ligar(self):
        if self.dir is None:
            return
        try:
            await self.cdp.send("Page.stopScreencast")
        except Exception:
            pass
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": max(W, H), "maxHeight": max(W, H), "everyNthFrame": 1})

    async def comecar(self, d: pathlib.Path):
        shutil.rmtree(d, ignore_errors=True)
        (d / "quadros").mkdir(parents=True)
        self.dir, self.quadros, self.n = d, [], 1
        self.t0 = time.time()
        # primeiro quadro garantido (o screencast só manda quadro quando a tela muda)
        (d / "quadros" / "000000.jpg").write_bytes(await self.page.screenshot(type="jpeg", quality=92))
        self.quadros.append({"arquivo": "000000.jpg", "t": 0.0})
        await self.ligar()

    def agora(self):
        return time.time() - self.t0

    async def terminar(self, frases):
        await asyncio.sleep(0.2)
        try:
            await self.cdp.send("Page.stopScreencast")
        except Exception:
            pass
        fim = self.agora()
        log = {"fim": round(fim, 3), "frases": frases, "quadros": sorted(self.quadros, key=lambda q: q["t"])}
        (self.dir / "log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
        self.dir = None
        return fim


def carregar_mock():
    nome = DEMO.get("mock")
    if not nome:
        return None
    spec = importlib.util.spec_from_file_location("mock_api", PASTA / nome)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "responder"):
        raise SystemExit(f"{nome} precisa definir responder(metodo, caminho, query, corpo)")
    return mod


async def main():
    from playwright.async_api import async_playwright

    sel = {x for x in args.blocos.split(",") if x}
    blocos = ROT["blocos"]
    demos = [b for b in blocos if b["tipo"] == "demo"]
    if sel:
        desconhecidos = sel - {b["id"] for b in blocos}
        if desconhecidos:
            raise SystemExit(f"blocos não encontrados no roteiro: {', '.join(desconhecidos)}")
        if any(b["id"] in sel for b in demos):
            sel |= {b["id"] for b in demos}
        blocos = [b for b in blocos if b["id"] in sel]
    cenas_html = PASTA / ROT.get("cenas", "cenas.html")
    if any(b["tipo"] == "cena" for b in blocos):
        txt = cenas_html.read_text(encoding="utf-8")
        for b in blocos:
            if b["tipo"] == "cena" and f'id="{b["id"]}"' not in txt:
                raise SystemExit(f"a cena '{b['id']}' não existe em {cenas_html.name} (<section class=\"scene\" id=\"{b['id']}\">)")
    if any(b["tipo"] == "demo" for b in blocos) and not DEMO.get("url_base"):
        raise SystemExit("roteiro com bloco demo precisa de demo.url_base")

    saida = PASTA / ("previa" if args.previa else "brutos")
    saida.mkdir(exist_ok=True)
    if args.previa:
        for f in saida.glob("*.png"):
            f.unlink()
    previa = []

    async with async_playwright() as p:
        b = None
        for kw in ({}, {"channel": "msedge"}, {"channel": "chrome"}):
            try:
                b = await p.chromium.launch(**kw)
                break
            except Exception:
                continue
        if not b:
            raise SystemExit("nenhum navegador disponível. Rode: python -m playwright install chromium")

        telas = {}

        async def tela_cena():
            if "cena" not in telas:
                ctx = await b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
                pg = await ctx.new_page()
                await pg.goto(cenas_html.as_uri(), wait_until="networkidle")
                await pg.evaluate("document.fonts.ready.then(() => 1)")
                if not await pg.evaluate("typeof window.__mostrar === 'function' && typeof window.__frase === 'function'"):
                    raise SystemExit("cenas.html precisa definir window.__mostrar e window.__frase (veja o modelo)")
                t = Tela(pg, (W, H), 1)
                await t.iniciar()
                telas["cena"] = t
            return telas["cena"]

        async def tela_demo():
            if "demo" not in telas:
                vw, vh = DEMO.get("viewport", [1440, 810])
                esc = float(DEMO.get("escala", W / vw))
                ctx = await b.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=esc, accept_downloads=False)
                mock = carregar_mock()
                if DEMO.get("interceptar"):
                    async def rota(route):
                        req = route.request
                        u = urlparse(req.url)
                        res = mock.responder(req.method, u.path, dict(parse_qsl(u.query)), req.post_data) if mock else None
                        if res is None:
                            if DEMO.get("deixar_passar"):
                                return await route.continue_()
                            print(f"  [aviso] sem resposta fictícia para {req.method} {u.path} (respondido 404)")
                            return await route.fulfill(status=404, content_type="application/json", body='{"erro":"sem mock"}')
                        st, ct, corpo = res
                        if isinstance(corpo, (dict, list)):
                            corpo, ct = json.dumps(corpo, ensure_ascii=False), ct or "application/json"
                        await route.fulfill(status=st, content_type=ct, body=corpo if isinstance(corpo, bytes) else str(corpo).encode("utf-8"))
                    await ctx.route(DEMO["interceptar"], rota)
                pg = await ctx.new_page()
                pg.set_default_timeout(TIMEOUT)
                t = Tela(pg, (vw, vh), esc)
                await t.iniciar()
                telas["demo"] = t
            return telas["demo"]

        def localizar(pg, alvo):
            if alvo.startswith("css="):
                return pg.locator(alvo[4:]).first
            if alvo.startswith("texto="):
                return pg.get_by_text(alvo[6:], exact=True).first
            return pg.get_by_text(alvo).first

        async def caixa(pg, alvo):
            loc = localizar(pg, alvo)
            await loc.wait_for(state="visible")
            await loc.evaluate("e => e.scrollIntoView({block: 'center', inline: 'nearest'})")
            await asyncio.sleep(0.05)
            bb = await loc.bounding_box()
            if not bb:
                raise RuntimeError(f"alvo sem posição na tela: {alvo}")
            return loc, bb

        async def preparar(pg):
            await pg.evaluate(SETUP, {"w": PAINEL_W, "esq": int(DEMO.get("legenda_margem_esquerda", 24))})
            await pg.evaluate("document.fonts.ready.then(() => 1)")

        async def executar(t, acao, bloco, k, rapido):
            pg = t.page
            if len(acao) != 1:
                raise SystemExit(f"bloco {bloco['id']}, frase {k}: cada ação tem uma chave só ({acao})")
            (nome, v), = acao.items()
            if nome == "ir":
                await pg.goto(urljoin(DEMO["url_base"].rstrip("/") + "/", v.lstrip("/")), wait_until="networkidle")
                await preparar(pg)
                await pg.evaluate(PAINEL, [bloco["_n"], bloco["_total"], bloco.get("card", {}), DEMO.get("caso", "")])
            elif nome == "clicar":
                loc, bb = await caixa(pg, v)
                if not rapido:
                    await pg.evaluate(CURSOR, [bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2, False])
                    await asyncio.sleep(0.6)
                    await pg.evaluate(CURSOR, [bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2, True])
                    await asyncio.sleep(0.15)
                await loc.click()
                await pg.evaluate("() => { const c = document.getElementById('vd-cur'); if (c) { c.classList.remove('press'); setTimeout(() => c.classList.remove('on'), 900); } }")
                try:
                    await pg.wait_for_load_state("networkidle", timeout=3000)
                except Exception:
                    pass
            elif nome == "digitar":
                loc, _ = await caixa(pg, v["em"])
                await loc.click()
                await loc.press_sequentially(v["texto"], delay=0 if rapido else 35)
            elif nome == "rolar":
                loc = localizar(pg, v)
                await loc.evaluate("e => e.scrollIntoView({behavior: 'smooth', block: 'center'})")
                await asyncio.sleep(0 if rapido else 0.8)
            elif nome == "esperar":
                await asyncio.sleep(0 if rapido else v / 1000)
            elif nome == "marcar":
                _, bb = await caixa(pg, v["alvo"])
                await pg.evaluate(MARCA, [bb, v.get("tipo", "anel"), v.get("etiqueta", ""), v.get("spot", True)])
            elif nome == "painel":
                await pg.evaluate(FOCO, v)
            elif nome == "exportar":
                await pg.evaluate(TOAST, [v.get("arquivo", "planilha.xlsx"), v.get("detalhe", "")])
            elif nome == "ocultar":
                await pg.evaluate(OCULTAR, v if isinstance(v, list) else [v])
            elif nome == "js":
                await pg.evaluate(v)
            else:
                raise SystemExit(f"bloco {bloco['id']}, frase {k}: ação desconhecida '{nome}'")

        for n, bd in enumerate(demos, 1):
            bd["_n"], bd["_total"] = n, len(demos)
        ultimo = ROT["blocos"][-1]["id"]

        for bloco in blocos:
            cena = bloco["tipo"] == "cena"
            t = await (tela_cena() if cena else tela_demo())
            pg = t.page
            print(f"{'prévia' if args.previa else 'gravando'} {bloco['id']} ({bloco['tipo']})")
            if cena:
                await pg.evaluate("id => window.__mostrar(id)", bloco["id"])
            elif pg.url == "about:blank":
                # primeira tela: abre antes de começar a gravar, para o vídeo não começar em branco
                f0 = bloco["frases"][0]
                while f0["antes"] and "ir" in f0["antes"][0]:
                    await executar(t, f0["antes"].pop(0), bloco, 0, True)
            else:
                await pg.evaluate(PAINEL, [bloco["_n"], bloco["_total"], bloco.get("card", {}), DEMO.get("caso", "")])
                await pg.evaluate(LEGENDA, "")
                await pg.evaluate(FOCO, "")
            if not args.previa:
                await t.comecar(saida / bloco["id"])
                await asyncio.sleep(RITMO["entrada"])
            inicios = []
            for k, f in enumerate(bloco["frases"]):
                try:
                    if not cena:
                        for a in f["antes"]:
                            await executar(t, a, bloco, k, args.previa)
                        await pg.evaluate(LIMPAR)
                    inicio = t.agora()
                    if cena:
                        await pg.evaluate("([id, k, tx]) => window.__frase(id, k, tx)", [bloco["id"], k, f["texto"]])
                    else:
                        await pg.evaluate(LEGENDA, f["texto"])
                        for a in f["acoes"]:
                            await executar(t, a, bloco, k, args.previa)
                except SystemExit:
                    raise
                except Exception as e:
                    raise SystemExit(f"bloco '{bloco['id']}', frase {k} ({f['texto'][:50]}...): {str(e).splitlines()[0]}\n"
                                     f"Confira o alvo com: python scripts/gravar.py <pasta> --previa")
                if args.previa:
                    await asyncio.sleep(1.2 if cena else 0.7)
                    png = saida / f"{bloco['id']}_{k:02d}.png"
                    await pg.screenshot(path=str(png))
                    previa.append((bloco["id"], k, f["texto"], png.name))
                    continue
                inicios.append(round(inicio, 3))
                d = NARR[bloco["id"]][k]["d"]
                falta = inicio + d + RITMO["gap"] - t.agora()
                if falta > 0:
                    await asyncio.sleep(falta)
            if not args.previa:
                await asyncio.sleep(RITMO["saida"] + (RITMO["final"] if bloco["id"] == ultimo else 0))
                fim = await t.terminar(inicios)
                print(f"  {fim:.1f} s")
        await b.close()

    if args.previa:
        linhas = "".join(f"<figure><img src='{html.escape(png)}'><figcaption><b>{html.escape(i)} · frase {k}</b> {html.escape(tx)}</figcaption></figure>"
                         for i, k, tx, png in previa)
        (saida / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>Prévia do vídeo</title><style>body{font-family:Segoe UI,Arial;background:#F7F8F6;margin:24px}"
            "figure{margin:0 0 28px;max-width:1100px}img{width:100%;border:1px solid #D5DCE6;border-radius:8px}figcaption{margin-top:6px;font-size:15px}</style>"
            f"<h1>Prévia · {html.escape(ROT.get('titulo', ''))}</h1>{linhas}", encoding="utf-8")
        print(f"prévia: {saida / 'index.html'}")


asyncio.run(main())
