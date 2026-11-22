"""Tela do CUSTOM PROVIDER (dentro do CONFIG).

Deixa a pessoa informar uma base url compativel com OpenAI e as keys
dela. O provider entra no catalogo como "custom:<id>" e o programa
rotaciona essas keys igual as do NightRouter.

Fluxo da tela:
  lista os custom salvos + "adicionar novo"
  em cada custom: ver keys, adicionar keys, testar, usar, remover
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import custom_provider
import menu_principal as mp
import temas
import tela_config as cfg

ESC = "\x1b["


def _p(t):
    return temas.paleta(t)


def _caixa(corpo, tema, largura, t):
    if tema == temas.INFINITY:
        return mp.moldura_infinity(corpo, largura, t)
    return mp.moldura_legacy(corpo, largura)


def _esconder(key):
    """Mostra so o comeco e o fim da key, para caber na tela."""
    k = key or ""
    if not k:
        return ""
    if len(k) <= 12:
        return k
    return k[:8] + "..." + k[-4:]


def _le_linha(tema, largura, titulo, valor_inicial="", dica="", senha=False):
    """Le uma linha do teclado. Devolve (texto, confirmado)."""
    buffer = valor_inicial
    erro = ""
    sys.stdout.write(ESC + "?25l")
    try:
        while True:
            c, r = mp.tamanho()
            t = time.time()
            largura = max(50, min(c - 1, 96))
            p = _p(tema)
            cursor = "_" if int(t * 2) % 2 == 0 else " "
            mostrar = buffer if not senha else "*" * len(buffer)
            if len(mostrar) > 58:
                mostrar = mostrar[-58:]
            corpo = [""]
            corpo.extend(cfg._cabecalho(titulo, tema, largura, t))
            corpo.append("")
            corpo.append("  " + p["primaria"] + "  " + mostrar + cursor
                         + temas.RESET)
            corpo.append("")
            if dica:
                corpo.append("  " + p["fraco"] + dica + temas.RESET)
            corpo.append("  " + p["fraco"]
                         + "enter confirma   esc cancela" + temas.RESET)
            if erro:
                corpo.append("  " + p["erro"] + "! " + erro + temas.RESET)
            else:
                corpo.append("")
            mp.desenhar(_caixa(corpo, tema, largura, t), c, r)
            tecla = mp.le_texto(0.09)
            if tecla is None:
                continue
            if tecla == "esc":
                return "", False
            if tecla == "enter":
                return buffer.strip(), True
            if tecla == "backspace":
                buffer = buffer[:-1]
            elif tecla == "colar":
                # a key costuma vir do clipboard: cola inteira
                try:
                    buffer += (mp.colar_area() or "").strip()
                except Exception:
                    pass
            elif tecla == "espaco":
                buffer += " "
            elif len(tecla) == 1 and tecla.isprintable():
                buffer += tecla
            erro = ""
    finally:
        sys.stdout.write(temas.RESET + ESC + "?25h")
        sys.stdout.flush()


def _menu(conf, titulo, opcoes, dica=""):
    """Menu generico. Devolve o indice escolhido ou None (esc)."""
    tema = (conf or {}).get("tema") or temas.LEGACY
    escolhido = 0
    mp.drenar()
    sys.stdout.write(ESC + "?25l")
    try:
        while True:
            c, r = mp.tamanho()
            t = time.time()
            largura = max(50, min(c - 1, 96))
            p = _p(tema)
            corpo = [""]
            corpo.extend(cfg._cabecalho(titulo, tema, largura, t))
            corpo.append("")
            for i, texto in enumerate(opcoes):
                corpo.append(cfg._linha_opcao(texto, i == escolhido, tema, t,
                                              i == escolhido))
            corpo.append("")
            if dica:
                corpo.append("  " + p["fraco"] + dica + temas.RESET)
            corpo.append("")
            corpo.append(cfg._rodape(tema, largura, t))
            mp.desenhar(_caixa(corpo, tema, largura, t), c, r)
            tecla = mp.le_tecla(0.09)
            if tecla is None:
                continue
            if tecla in ("cima", "k"):
                escolhido = (escolhido - 1) % len(opcoes)
            elif tecla in ("baixo", "j"):
                escolhido = (escolhido + 1) % len(opcoes)
            elif tecla in ("esc", "backspace"):
                return None
            elif tecla == "enter":
                return escolhido
            elif len(tecla) == 1 and tecla.isdigit():
                n = int(tecla)
                if 1 <= n <= len(opcoes):
                    return n - 1
    finally:
        sys.stdout.write(temas.RESET + ESC + "?25h")
        sys.stdout.flush()


def _rodar_detalhe(conf, prov_nome):
    """Tela de um custom: keys, testar, usar, remover."""
    tema = conf.get("tema") or temas.LEGACY
    aviso = ""
    aviso_ate = 0.0
    escolhido = 0
    mp.drenar()

    def opcoes():
        return ["modo: %s" % ("FREE (so gratuitos)" if prov_atual_modo() == "free"
                              else "SALDO (todos os modelos)"),
                "adicionar keys", "testar conexao", "usar (ativar)",
                "contas sem saldo", "remover este provider", "voltar"]

    def prov_atual_modo():
        p = custom_provider.por_nome(prov_nome)
        return (p.get("modo") if p else "free") or "free"

    sys.stdout.write(ESC + "?25l")
    try:
        while True:
            prov = custom_provider.por_nome(prov_nome)
            if not prov:
                return
            c, r = mp.tamanho()
            t = time.time()
            largura = max(50, min(c - 1, 96))
            p = _p(tema)
            corpo = [""]
            corpo.extend(cfg._cabecalho("CUSTOM  /  " + prov["titulo"].upper(),
                                        tema, largura, t))
            corpo.append("")
            corpo.append("  " + p["texto2"] + "base url" + temas.RESET + "  "
                         + p["texto"] + prov["base"] + temas.RESET)
            if prov.get("modelo"):
                corpo.append("  " + p["texto2"] + "modelo  " + temas.RESET
                             + "  " + p["texto"] + prov["modelo"]
                             + temas.RESET)
            n = len(prov["keys"])
            cor = p["ok"] if n else p["alerta"]
            corpo.append("  " + p["texto2"] + "keys    " + temas.RESET + "  "
                         + cor + "%d keys na rotacao" % n + temas.RESET)
            corpo.append("")
            for i, k in enumerate(prov["keys"][:6]):
                corpo.append("    " + p["fraco"] + "#%d  " % i + p["texto2"]
                             + _esconder(k) + temas.RESET)
            if n > 6:
                corpo.append("    " + p["fraco"] + "+%d outras"
                             % (n - 6) + temas.RESET)
            corpo.append("")
            corpo.append(mp.divisor(largura, tema, t))
            for i, texto in enumerate(opcoes()):
                corpo.append(cfg._linha_opcao(texto, i == escolhido, tema, t,
                                              i == escolhido))
            corpo.append("")
            if aviso and time.time() < aviso_ate:
                corpo.append("  " + p["alerta"] + aviso + temas.RESET)
            else:
                corpo.append("")
            corpo.append(cfg._rodape(tema, largura, t))
            mp.desenhar(_caixa(corpo, tema, largura, t), c, r)

            tecla = mp.le_tecla(0.09)
            if tecla is None:
                continue
            ops = opcoes()
            if tecla in ("cima", "k"):
                escolhido = (escolhido - 1) % len(ops)
            elif tecla in ("baixo", "j"):
                escolhido = (escolhido + 1) % len(ops)
            elif tecla in ("esc", "backspace"):
                return
            elif len(tecla) == 1 and tecla.isdigit():
                n2 = int(tecla)
                if 1 <= n2 <= len(ops):
                    escolhido = n2 - 1
                    tecla = "enter"
                else:
                    continue
            if tecla != "enter":
                continue

            acao = ops[escolhido]
            if acao.startswith("modo:"):
                novo = ("saldo" if prov_atual_modo() == "free" else "free")
                import custom_modo
                custom_modo.definir_modo(prov["nome"], novo)
                aviso = ("modo SALDO: todos os modelos; conta sem saldo sai "
                         "da base" if novo == "saldo"
                         else "modo FREE: so modelos gratuitos; rate limit "
                              "troca de modelo")
                aviso_ate = time.time() + 7
                escolhido = 0
            elif acao == "contas sem saldo":
                _tela_mortas(prov["nome"])
                mp.drenar()
                escolhido = 0
            elif acao == "adicionar keys":
                txt, ok = _le_linha(
                    tema, largura, "CUSTOM  /  KEYS",
                    dica="cole as keys separadas por virgula, espaco ou linha")
                if ok and txt:
                    novas = [k.strip() for k in
                             txt.replace(",", " ").replace(";", " ").split()
                             if k.strip()]
                    total = custom_provider.adicionar_keys(prov["nome"], novas)
                    aviso = "%d keys adicionadas (total %d)" % (len(novas), total)
                    aviso_ate = time.time() + 6
                mp.drenar()
            elif acao == "testar conexao":
                key = prov["keys"][0] if prov["keys"] else ""
                ok, msg = custom_provider.testar(prov, key)
                aviso = ("ok: " + msg) if ok else ("falhou: " + msg)
                aviso_ate = time.time() + 8
            elif acao == "usar (ativar)":
                import providers
                if providers.definir("custom:" + prov["nome"]):
                    aviso = "ativado - reinicie o app para valer"
                else:
                    aviso = "nao consegui gravar o config"
                aviso_ate = time.time() + 8
            elif acao == "remover este provider":
                r2 = _menu(conf, "REMOVER?",
                           ["sim, remover " + prov["titulo"],
                            "nao, voltar"])
                if r2 == 0:
                    custom_provider.remover(prov["nome"])
                    return
                mp.drenar()
            elif acao == "voltar":
                return
    finally:
        sys.stdout.write(temas.RESET + ESC + "?25h")
        sys.stdout.flush()


def _tela_mortas(nome_custom):
    """Lista as contas removidas por falta de saldo e deixa reviver."""
    import custom_modo
    while True:
        mortas = custom_modo.listar_mortas(nome_custom)
        itens = list(mortas.items())
        ops = ["voltar"]
        if itens:
            ops.insert(0, "devolver TODAS para a base")
        for k, info in itens:
            ops.append("devolver %s" % _esconder(k))
        idx = _menu(None, "CUSTOM  /  CONTAS SEM SALDO", ops,
                    "%d conta(s) removida(s) por falta de saldo" % len(itens))
        if idx is None or idx == len(ops) - 1:
            return
        if itens and idx == 0:
            custom_modo.reviver(nome_custom)
            continue
        if itens and 1 <= idx <= len(itens):
            custom_modo.reviver(nome_custom, itens[idx - 1][0])
            continue


def _novo(conf):
    """Cadastra um custom novo: nome, base url e keys."""
    tema = conf.get("tema") or temas.LEGACY
    largura = 80
    base, ok = _le_linha(tema, largura, "CUSTOM  /  NOVA BASE URL", "",
                         dica="ex: https://api.provedor.com/v1")
    if not ok or not base:
        return
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    nome, ok = _le_linha(tema, largura, "CUSTOM  /  APELIDO", "",
                         dica="aparece no CONFIG. enter usa o dominio")
    if not ok:
        return
    keys, ok = _le_linha(tema, largura, "CUSTOM  /  KEYS", "",
                         dica="uma ou varias, separadas por virgula/espaco "
                              "(pode deixar vazio e colocar depois)")
    if not ok:
        keys = ""
    lista_keys = [k.strip() for k in
                  keys.replace(",", " ").replace(";", " ").split() if k.strip()]
    # modo de uso: FREE (so gratuitos) ou SALDO (todos os modelos)
    esc = _menu(conf, "CUSTOM  /  MODO DE USO",
                ["FREE - so modelos gratuitos, rotaciona no rate limit",
                 "SALDO - todos os modelos, conta sem saldo sai da base"],
                "da para trocar depois no menu do provider")
    modo = "saldo" if esc == 1 else "free"
    try:
        prov = custom_provider.adicionar(nome, base, lista_keys, modo=modo)
    except ValueError as exc:
        return str(exc)
    # testa na hora e avisa
    ok2, msg = custom_provider.testar(prov, prov["keys"][0] if prov["keys"] else "")
    _aviso_curto(conf, prov["titulo"],
                 ("conectou: " + msg) if ok2 else ("cadastrado. teste: " + msg))
    return None


def _aviso_curto(conf, titulo, texto):
    tema = conf.get("tema") or temas.LEGACY
    mp.drenar()
    sys.stdout.write(ESC + "?25l")
    try:
        for _ in range(12):
            c, r = mp.tamanho()
            t = time.time()
            largura = max(50, min(c - 1, 92))
            p = _p(tema)
            corpo = [""]
            corpo.extend(cfg._cabecalho("CUSTOM  /  " + titulo.upper(),
                                        tema, largura, t))
            corpo.append("")
            corpo.append("  " + p["texto"] + texto + temas.RESET)
            corpo.append("")
            corpo.append("  " + p["fraco"] + "qualquer tecla continua"
                         + temas.RESET)
            corpo.append("")
            mp.desenhar(_caixa(corpo, tema, largura, t), c, r)
            if mp.le_tecla(0.25) is not None:
                return
    finally:
        sys.stdout.write(temas.RESET + ESC + "?25h")
        sys.stdout.flush()


def tela_custom(conf, cols=None, rows=None):
    """Entrada do CONFIG -> Custom Provider."""
    while True:
        lista = custom_provider.carregar(forcar=True)
        try:
            import providers
            ativo = providers.nome_atual().replace("custom:", "")
        except Exception:
            ativo = ""
        ops = []
        for p in lista:
            marca = "   [ativo]" if p["nome"] == ativo else ""
            ops.append("%s  (%d keys)%s" % (p["titulo"], len(p["keys"]), marca))
        idx_novo = len(ops)
        ops.append("+ adicionar nova base url")
        idx = _menu(conf, "CONFIG  /  CUSTOM PROVIDER", ops,
                    "sua base url, suas keys, rotacionando igual o NightRouter")
        if idx is None:
            return
        if idx == idx_novo:
            _novo(conf)
        elif idx < len(lista):
            _rodar_detalhe(conf, lista[idx]["nome"])
