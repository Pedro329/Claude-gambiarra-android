import http.cookiejar
import json
import os
import secrets
import string
import threading
import time
import urllib.error
import urllib.request

WEB = "https://nightrouter.ai"
API_BASE = "https://api.nightrouter.ai/v1"
DISCORD = "https://discord.gg/gambiarra"
USER_PREFIX = "gambiarraapi"
KEY_NAME = "gambiarraapi"
EMAIL_DOMAIN = "@bwingmedia.com"
# The free models only answer for keys in the "free" group. A key created in
# "default" or "vip" gets 503 "no available channel" on every -free model.
KEY_GROUP = "free"
# Tried in order if the first choice has no channel for a model.
GROUP_FALLBACK = ("free", "vip", "default")
# Models used to prove a key can really reach the free pool. Several, because
# any one of them can sit at "system is busy" while the others answer.
KEY_GROUP_PROBE = ("deepseek-v4-flash-free", "kimi-k3-free",
                   "gpt-5.6-sol-free", "glm-5.3-free", "deepseek-v3.2-free")

ALNUM = string.ascii_lowercase + string.digits
ALNUM_MIX = string.ascii_letters + string.digits

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": WEB,
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

def rand_username():
    return USER_PREFIX + "".join(secrets.choice(ALNUM) for _ in range(8))

def rand_password():
    body = "".join(secrets.choice(ALNUM_MIX) for _ in range(12))
    return "G" + body + "9"

def _proxy_handler(proxy):
    """Monta o handler com o esquema certo.

    Aceita "ip:porta" (assume http), "http://ip:porta",
    "socks5://ip:porta" e "http://usuario:senha@host:porta" (proxy
    premium). O ProxyHandler do urllib NAO resolve socks sozinho, entao
    tentamos PySocks quando o esquema for socks.
    """
    if not proxy:
        return None
    p = proxy.strip()
    if "://" not in p:
        p = "http://" + p
    esquema = p.split("://", 1)[0].lower()
    par = {"http": p, "https": p}
    if esquema in ("socks4", "socks5", "socks5h"):
        try:
            import socks  # PySocks
            import socket as _socket
            resto = p.split("://", 1)[1]
            cred, _, hostport = resto.rpartition("@")
            host, _, porta = hostport.partition(":")
            user, _, senha = cred.partition(":")
            tipo = socks.SOCKS4 if esquema == "socks4" else socks.SOCKS5
            # instala o handler global do urllib para socks
            return urllib.request.ProxyHandler(
                {"http": "%s://%s" % (esquema, hostport),
                 "https": "%s://%s" % (esquema, hostport)})
        except Exception:
            # sem PySocks: cai para http e deixa falhar de forma limpa
            return urllib.request.ProxyHandler(par)
    return urllib.request.ProxyHandler(par)


class Account:
    __slots__ = ("username", "password", "email", "jar", "opener", "token_id",
                 "proxy")

    def __init__(self, username, password, email, proxy=None):
        self.username = username
        self.password = password
        self.email = email
        self.proxy = proxy
        self.jar = http.cookiejar.CookieJar()
        handlers = [urllib.request.HTTPCookieProcessor(self.jar)]
        try:
            ph = _proxy_handler(proxy)
        except Exception:
            ph = None
        if ph is not None:
            handlers.append(ph)
        self.opener = urllib.request.build_opener(*handlers)
        self.token_id = None

class FarmError(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.message = message
        self.status = status

def _request(account, method, url, payload, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in BASE_HEADERS.items():
        req.add_header(k, v)
    req.add_header("Referer", WEB + "/register")
    try:
        with account.opener.open(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, "conexao: %s" % type(e).__name__

def register(account):
    payload = {
        "username": account.username,
        "email": account.email,
        "password": account.password,
        "password2": account.password,
    }
    status, body = _request(account, "POST", WEB + "/bff/user/register", payload)
    return _verdict(status, body)

def login(account):
    payload = {"username": account.username, "password": account.password}
    status, body = _request(account, "POST", WEB + "/bff/user/login", payload)
    return _verdict(status, body)

def create_key(account, group=None):
    payload = {
        "name": KEY_NAME,
        "expired_time": -1,
        "model_limits_enabled": False,
        "model_limits": "",
        "allow_ips": "",
        "group": group or KEY_GROUP,
        "unlimited_quota": True,
    }
    ok, err, key = _create(account, payload)
    return ok, err, key

def _create(account, payload):
    status, body = _request(account, "POST", WEB + "/bff/token/", payload)
    ok, detail = _verdict(status, body)
    if not ok:
        return False, detail, None
    try:
        data = json.loads(body)["data"]
    except (ValueError, KeyError, TypeError):
        return False, "key ausente na resposta", None
    key = data.get("key") if isinstance(data, dict) else None
    if not isinstance(key, str) or not key:
        return False, "key vazia", None
    account.token_id = data.get("id")
    return True, "", key

def _verdict(status, body):
    if status != 200:
        return False, "HTTP %d: %s" % (status, body[:120].replace("\n", " "))
    try:
        data = json.loads(body)
    except ValueError:
        return False, "resposta invalida: %s" % body[:120]
    if not data.get("success"):
        msg = str(data.get("message") or "falha")
        if "Invalid parameters" in msg:
            msg = "parametros recusados pelo site"
        return False, msg[:120]
    return True, ""

def _email_para(username):
    """E-mail da conta nova.

    Olha o CONFIG > MAIL: usa o provedor escolhido para o farm, desde
    que esteja ligado. O Gmailnator precisa de chave. Se nada servir,
    cai no dominio local: o cadastro nao pode parar por causa do e-mail.
    """
    try:
        import temas
        conf = temas.carregar() or {}
        escolhido = conf.get("mail_farm") or "gmailnator"
        ligados = conf.get("mail_ligados")
        if not isinstance(ligados, list):
            ligados = ["gmailnator"]
        if escolhido in ligados:
            if escolhido == "gmailnator":
                import gmailnator
                chave = (conf.get("mail_gmailnator_key") or "").strip()
                if chave:
                    try:
                        novo = gmailnator.criar(chave)
                        if novo and "@" in novo:
                            return novo
                    except Exception:
                        pass
            else:
                import tempmail
                ctx = tempmail.criar(escolhido)
                if ctx and ctx.get("email"):
                    return ctx["email"]
    except Exception:
        pass
    return username + EMAIL_DOMAIN


def harvest_one(attempt, proxy=None):
    account = Account(rand_username(), rand_password(), "", proxy=proxy)
    account.email = _email_para(account.username)
    ok, err = register(account)
    if not ok:
        return None, "cadastro: " + err
    ok, err = login(account)
    if not ok:
        return None, "login: " + err
    ok, err, key = create_key(account)
    if not ok:
        return None, "key: " + err
    probe_key = key if key.startswith("sk-") else "sk-" + key
    status, body = probe_api(probe_key, timeout=25)
    if status in (401, 403):
        return None, "key recusada pela API (%s)" % status
    if status != 200:
        return None, "API fora do ar (%s)" % status
    # A key can authenticate and still be useless: only the group that owns
    # the -free channels can actually answer them. Recreate the token in the
    # next group when this one has no channel.
    group = KEY_GROUP
    usable, detail = usable_group(account, probe_key)
    if not usable:
        for alt in GROUP_FALLBACK:
            if alt == group:
                continue
            ok, err, alt_key = create_key(account, group=alt)
            if not ok or not alt_key:
                continue
            alt_probe = alt_key if alt_key.startswith("sk-") else "sk-" + alt_key
            good, why = usable_group(account, alt_probe)
            if good:
                probe_key, group, detail = alt_probe, alt, why
                break
        else:
            return None, "grupo sem canal: " + detail
    return ({"user": account.username, "pass": account.password,
             "email": account.email, "name": KEY_NAME, "key": probe_key,
             "group": group, "attempt": attempt, "proxy": proxy or "",
             "at": time.strftime("%Y-%m-%d %H:%M:%S")}, "")

def usable_group(account, api_key, model=None):
    """Ask the upstream whether this key can actually reach the free pool.

    A 429 counts as success: the channel exists and we only hit the 3-per-
    minute cap. So does 503 "system is busy": the model is routed, just
    overloaded right now. Only "no available channel" means a wrong group."""
    targets = [model] if model else list(KEY_GROUP_PROBE)
    why = "sem resposta"
    for target in targets:
        status, body = probe_chat(api_key, model=target, timeout=35)
        low = (body or "").lower()
        if status == 200:
            return True, "ok"
        if "rate_limit" in low or "too many requests" in low:
            return True, "rate limit (canal ok)"
        if "system is busy" in low or "try again" in low:
            return True, "ocupado (canal ok)"
        if "no available channel" in low:
            why = "sem canal em " + target
            continue
        if "insufficient_user_quota" in low:
            return False, "conta sem saldo"
        why = "resposta %s em %s" % (status, target)
    return False, why

def login_slow(account, retries=4, first_wait=40):
    for attempt in range(retries):
        ok, err = login(account)
        if ok:
            return True, ""
        if "429" not in err:
            return False, err
        time.sleep(first_wait * (attempt + 1))
    return False, "login limitado (429) - espere alguns minutos"

def list_tokens(account):
    status, body = _request(account, "GET", WEB + "/bff/token/?p=1&size=50", None)
    if status != 200:
        return []
    try:
        return json.loads(body).get("data", {}).get("items", []) or []
    except (ValueError, AttributeError):
        return []

def reveal_key(account, token_id):
    status, body = _request(account, "POST",
                            WEB + "/bff/token/%s/key" % token_id, {})
    if status != 200:
        return None
    try:
        data = json.loads(body)
    except ValueError:
        return None
    data = data.get("data") if isinstance(data, dict) else None
    if isinstance(data, dict) and isinstance(data.get("key"), str):
        return data["key"]
    if isinstance(data, str) and len(data) > 20:
        return data
    return None

def become_api_key(account, token_id, retries=4):
    for attempt in range(retries):
        value = reveal_key(account, token_id)
        if value:
            return value if value.startswith("sk-") else "sk-" + value
        time.sleep(4 + attempt * 8)
    return None

def probe_api(api_key, model=None, timeout=25):
    """Validate a key without spending quota.

    /v1/models answers 401 for a bad key and 200 for a good one, and never
    returns 503 - unlike /chat/completions, which fails with "No available
    channel" whenever the free pool is busy. The chat call is only the
    fallback for when /v1/models is unreachable.
    """
    req = urllib.request.Request(API_BASE + "/models")
    req.add_header("Authorization", "Bearer " + api_key)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except urllib.error.HTTPError as exc:
        code = exc.code
        body = exc.read().decode("utf-8", "replace")
        if code in (401, 403):
            return code, body[:200]
        return code, body[:200]
    except Exception as exc:
        return 0, repr(exc)

def probe_chat(api_key, model=None, timeout=40):
    """Real answered-call test. Slow and quota-hungry, so only for spot checks."""
    target = model or "deepseek-v4-flash-free"
    body = json.dumps({"model": target, "max_tokens": 8,
                       "messages": [{"role": "user", "content": "hi"}]}).encode()
    req = urllib.request.Request(API_BASE + "/chat/completions", data=body,
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + api_key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:
        return 0, repr(exc)

class KeyStore:

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.items = []
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            raw = None
        if isinstance(raw, dict) and isinstance(raw.get("keys"), list):
            self.items = [x for x in raw["keys"] if isinstance(x, dict)]
        elif isinstance(raw, list):
            self.items = [x for x in raw if isinstance(x, dict)]
        elif isinstance(raw, dict):
            self.items = [{"name": k, "key": v} for k, v in raw.items()
                          if isinstance(v, str)]
        seen = set()
        clean = []
        for it in self.items:
            k = it.get("key")
            if isinstance(k, str) and k and k not in seen:
                seen.add(k)
                clean.append(it)
        self.items = clean

    def count(self):
        with self.lock:
            return len(self.items)

    def keys(self):
        with self.lock:
            return [it["key"] for it in self.items if it.get("key")]

    def add(self, record):
        with self.lock:
            self.items.append(record)
            self._flush_locked()

    def _flush_locked(self):
        tmp = self.path + ".tmp"
        payload = {
            "meta": {
                "app": "NightRouter Farmer",
                "discord": DISCORD,
                "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "keys": self.items,
        }
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    def flush(self):
        with self.lock:
            self._flush_locked()
