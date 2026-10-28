import base64, html, http.client, http.server, json, re, socket, urllib.parse, urllib.request

KEY = "/secrets/wireguard_private_key"
DUMMY = "A" * 43 + "="
APP = "dvalcasa-qbittorrent-vpn"
CONTAINERS = [f"{APP}_gluetun_1", f"{APP}_qbittorrent_1"]


class DockerConn(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.connect("/var/run/docker.sock")


def restart(name):
    c = DockerConn()
    c.request("POST", f"/containers/{name}/restart?t=5")
    r = c.getresponse()
    r.read()
    return r.status


def configured():
    try:
        return open(KEY).read().strip() not in ("", DUMMY)
    except OSError:
        return False


def key_from_token(token):
    req = urllib.request.Request("https://api.nordvpn.com/v1/users/services/credentials")
    auth = base64.b64encode(f"token:{token}".encode()).decode()
    req.add_header("Authorization", "Basic " + auth)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)["nordlynx_private_key"]


PAGE = """<!doctype html><html lang="fr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>qBittorrent + NordVPN</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:560px;margin:40px auto;padding:0 16px;background:#0f1428;color:#e8ecff}}
.card{{background:#1b2a6b;border-radius:16px;padding:20px;margin-bottom:16px}}
input{{width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:0;margin:6px 0 12px}}
button,a.btn{{display:inline-block;background:#4687ff;color:#fff;border:0;border-radius:8px;padding:10px 16px;text-decoration:none;cursor:pointer}}
.ok{{color:#6dff9e}}.ko{{color:#ffb86d}}.msg{{background:#0008;padding:10px;border-radius:8px}}
</style>
<h1>qBittorrent + NordVPN</h1>
{msg}
<div class="card"><b>État de la clé :</b> {status}</div>
<div class="card">
<form method="post" action="save">
<b>Option 1 : access token NordVPN</b>
<input name="token" placeholder="Access token (Nord Account → Services → NordVPN)" autocomplete="off">
<b>Option 2 : clé NordLynx directement</b>
<input name="key" placeholder="Clé privée (44 caractères, finit par =)" autocomplete="off">
<button>Enregistrer et redémarrer</button>
</form></div>
<div class="card"><a class="btn" id="q" href="#">Ouvrir qBittorrent</a></div>
<script>document.getElementById('q').href='http://'+location.hostname+':8094'</script>
</html>"""


class H(http.server.BaseHTTPRequestHandler):
    def send(self, msg=""):
        ok = configured()
        status = '<span class="ok">configurée</span>' if ok else '<span class="ko">non configurée (VPN inactif, qBittorrent sans réseau)</span>'
        body = PAGE.format(msg=msg, status=status).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        f = urllib.parse.parse_qs(self.rfile.read(n).decode())
        token = f.get("token", [""])[0].strip()
        key = f.get("key", [""])[0].strip()
        try:
            if not key and token:
                key = key_from_token(token)
            if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", key):
                raise ValueError("Clé invalide (44 caractères base64, finit par =).")
            with open(KEY, "w") as fh:
                fh.write(key + "\n")
            codes = [restart(c) for c in CONTAINERS]
            ok = all(c == 204 for c in codes)
            m = "Clé enregistrée, VPN redémarré." if ok else f"Clé enregistrée, mais redémarrage incomplet ({codes})."
            self.send(f'<div class="card msg">{html.escape(m)}</div>')
        except Exception as e:
            self.send(f'<div class="card msg ko">Erreur : {html.escape(str(e))}</div>')


http.server.ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
