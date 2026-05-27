import os
import re
from flask import Flask, request, session, render_template_string, redirect, url_for, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "CTF_SECRET_DO_NOT_SHARE_2026")

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

USERS_DB = {
    "support_staff": {"pass": "password_bi_an_123", "role": "support"},
    "admin":         {"pass": "admin_super_secret_pass_2026", "role": "quanly"},
}

ADMIN_OTP = os.environ.get("ADMIN_OTP", "")

BASE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'JetBrains Mono', monospace; background: radial-gradient(circle at center, #1a1f26 0%, #0d1117 100%); color: #c9d1d9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .box { background: rgba(22, 27, 34, 0.8); backdrop-filter: blur(10px); border: 1px solid #30363d; padding: 2.5rem; width: 320px; border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
    h2 { color: #58a6ff; margin-top: 0; }
    input { width: 100%; padding: 0.8rem; margin: 0.5rem 0 1.5rem; background: #0d1117; border: 1px solid #30363d; color: #e6edf3; border-radius: 4px; outline: none; }
    button { width: 100%; padding: 0.8rem; background: #238636; border: none; color: #fff; border-radius: 4px; cursor: pointer; transition: 0.3s; }
    button:hover { background: #2ea043; }
    .err { color: #f85149; font-size: 0.8rem; margin-bottom: 1rem; }
    a { color: #58a6ff; text-decoration: none; font-size: 0.85rem; }
</style>
"""

@app.before_request
def block_scanners():
    ua = request.headers.get("User-Agent", "").lower()
    bad = ["dirsearch", "gobuster", "sqlmap", "nmap", "nikto", "wfuzz"]
    if any(s in ua for s in bad): return "403 Forbidden", 403
    bad_patterns = [r"\.\.", r"\.\/", r"\{", r"\}", r"\(", r"\)"]
    if any(re.search(p, request.full_path) for p in bad_patterns): return "503 Service Unavailable", 200

@app.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    error = ""
    if request.method == "POST":
        u = request.form.get("user", "").strip()
        p = request.form.get("pass", "")
        if u in USERS_DB and USERS_DB[u]["pass"] == p:
            session.clear()
            session["user"] = u
            session["role"] = USERS_DB[u]["role"]
            return redirect(url_for("panel"))
        error = "Invalid credentials"
    return render_template_string(f"<!doctype html><html><head><title>Login</title>{BASE_CSS}</head><body><div class='box'><h2>// Login</h2>{% if error %}<div class='err'>{{ error }}</div>{% endif %}<form method='POST'><label>Username</label><input name='user' autocomplete='off'><label>Password</label><input type='password' name='pass'><button type='submit'>LOGIN</button></form><a href='/register'>Register</a></div></body></html>", error=error)

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def register():
    msg = ""
    if request.method == "POST":
        u = request.form.get("user", "").strip()
        p = request.form.get("pass", "")
        if not u or not p: msg = "Required."
        elif u in USERS_DB: msg = "Exists."
        else:
            USERS_DB[u] = {"pass": p, "role": "guest"}
            return redirect(url_for("login"))
    return render_template_string(f"<!doctype html><html><head><title>Register</title>{BASE_CSS}</head><body><div class='box'><h2>// Register</h2>{% if msg %}<div class='err'>{{ msg }}</div>{% endif %}<form method='POST'><label>Username</label><input name='user'><label>Password</label><input type='password' name='pass'><button type='submit'>REGISTER</button></form><a href='/'>Back</a></div></body></html>", msg=msg)

@app.route("/panel")
def panel():
    if not session.get("user"): return redirect(url_for("login"))
    return render_template_string(f"<!doctype html><html><head><title>Panel</title>{BASE_CSS}<style>.card{{background:#161b22;border:1px solid #30363d;padding:2rem;border-radius:8px;max-width:600px;margin:auto}}</style></head><body><div class='card'><h3>// Dashboard</h3><p>User: <strong>{{ session.get('user') }}</strong></p>{% if session.get('role') == 'support' %}<p><a href='/view-log?file=app.log'>View app.log</a></p>{% endif %}{% if session.get('role') == 'quanly' %}<p><a href='/internal-assets/cerdentials.txt.bak'>cerdentials.txt.bak</a></p>{% endif %}{% if session.get('user') == 'admin' %}<p><a href='/admin'>Admin Panel</a></p>{% endif %}</div></body></html>")

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if session.get("user") != "admin" or session.get("role") != "quanly": return "403", 403
    if request.method == "POST":
        if request.form.get("otp") == ADMIN_OTP: return "FLAG{admin_privileged_access_granted_2026}"
    return render_template_string(f"<!doctype html><html><head><title>Admin</title>{BASE_CSS}</head><body><div class='box'><form method='POST'><input name='otp' placeholder='OTP'><button>VERIFY</button></form></div></body></html>")

@app.route("/internal-assets/<path:filename>")
def secure_assets(filename):
    if session.get("role") != "quanly": return "403", 403
    return send_from_directory("internal_assets", os.path.basename(filename))

@app.route("/view-log")
def view_log():
    if not session.get("user"): return redirect(url_for("login"))
    filename = request.args.get("file", "")
    base_dir = os.path.abspath("logs")
    requested_path = os.path.abspath(os.path.join(base_dir, filename))
    if not requested_path.startswith(base_dir): return "403", 403
    try:
        if filename == "app.log" or session.get("user") == "support_staff":
            with open(requested_path, "r") as f: return f"<pre>{f.read()}</pre>"
        return "403", 403
    except: return "Not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
