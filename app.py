import os
import re
from functools import wraps
from flask import Flask, request, session, render_template_string, redirect, url_for, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Q4_210-S0-Cut3_vclll")

USERS_DB = {
    "support_staff": {"pass": "yeahhh_player_is_gay", "role": "support"},
    "admin":         {"pass": "yamatekudasai210", "role": "quanly"},
}

ADMIN_OTP = os.environ.get("ADMIN_OTP", "OTP-7f3a9b2c")

BASE_CSS = """
<link href="https://googleapis.com" rel="stylesheet">
<style>
    :root { --neon-blue: #00f3ff; --neon-pink: #ff00ff; --bg-dark: #050505; }
    body { font-family: 'Share Tech Mono', monospace; background: var(--bg-dark); color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)); }
    .box, .card { background: rgba(10, 10, 10, 0.9); border: 2px solid var(--neon-blue); padding: 2.5rem; width: 340px; box-shadow: 0 0 15px var(--neon-blue), inset 0 0 10px var(--neon-blue); text-transform: uppercase; }
    h2, h3 { color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); margin-top: 0; }
    input { width: 100%; padding: 0.8rem; margin: 0.5rem 0 1.5rem; background: #000; border: 1px solid var(--neon-pink); color: var(--neon-blue); font-family: 'Orbitron'; box-sizing: border-box; }
    button { width: 100%; padding: 0.8rem; background: transparent; border: 1px solid var(--neon-blue); color: var(--neon-blue); cursor: pointer; transition: 0.3s; font-weight: bold; }
    button:hover { background: var(--neon-blue); color: #000; box-shadow: 0 0 20px var(--neon-blue); }
    .err { color: var(--neon-pink); font-size: 0.8rem; margin-bottom: 1rem; text-shadow: 0 0 5px var(--neon-pink); }
    a { color: var(--neon-pink); text-decoration: none; font-size: 0.85rem; display: block; margin-top: 10px; }
    .card { max-width: 600px; width: auto; }
</style>
"""

PANEL_HTML = """
<!doctype html><html><head><title>Panel</title>"""+BASE_CSS+"""</head>
<body><div class='card'><h3>// DASHBOARD</h3><p>User: {{ u }}</p><p>Role: {{ role }}</p>
{% if role == 'support' or role == 'quanly' %}
<a href='/view-log'>[ ACCESS INTERNAL LOGS ]</a>
{% endif %}</div></body></html>
"""

def is_admin():
    return USERS_DB.get(session.get("user"), {}).get("role") == "quanly"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin(): return "403 Forbidden", 403
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def basic_waf():
    ua = request.headers.get("User-Agent", "").lower()
    if any(s in ua for s in ["curl", "wget", "sqlmap", "nikto", "gobuster"]):
        return "403 Forbidden - Bot Detected", 403

@app.route("/", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        u, p = request.form.get("user", "").strip(), request.form.get("pass", "")
        if USERS_DB.get(u) and USERS_DB[u]["pass"] == p:
            session.clear()
            session["user"] = u
            return redirect(url_for("panel"))
        error = "Invalid credentials"
    
    return render_template_string("<!doctype html><html><head><title>Login</title>"+BASE_CSS+"</head><body><div class='box'><h2>// LOGIN</h2>{% if error %}<div class='err'>{{ error }}</div>{% endif %}<form method='POST'><label>Username</label><input name='user'><label>Password</label><input type='password' name='pass'><button type='submit'>ACCESS</button></form><!-- TODO: Remember to send new credentials to support_staff: yeahhh_player_is_gay --></div></body></html>", error=error)


@app.route("/panel")
def panel():
    if not session.get("user"): return redirect(url_for("login"))
    return render_template_string(PANEL_HTML, u=session.get("user"), role=USERS_DB.get(session.get("user"), {}).get("role"))

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_panel():
    if request.method == "POST":
        if request.form.get("otp") == ADMIN_OTP: return "QA{yamate_senpai_access_granted_2026}"
    return render_template_string("<!doctype html><html><head><title>Admin</title>"+BASE_CSS+"</head><body><div class='box'><form method='POST'><input name='otp' placeholder='OTP'><button>VERIFY</button></form></div></body></html>")

@app.route("/view-log")
def view_log():
    if not (USERS_DB.get(session.get("user", ""), {}).get("role") in ["support", "quanly"]):
        return "403 Forbidden", 403
    
    # Giấu tham số ở đây: người dùng phải tự fuzz ra tên tham số 'file'
    log_file = request.args.get("file")
    
    if not log_file:
        return "ERROR: Missing 'file' parameter. Usage: /view-log?file=<filename>", 400

    try:
        return send_from_directory(os.getcwd(), log_file)
    except Exception:
        return "404 Not Found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
