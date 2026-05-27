import os
import re
from flask import Flask, request, session, render_template_string, redirect, url_for, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Q4_210-S0-Cut3_vclll")

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

USERS_DB = {
    "support_staff": {"pass": "yeahhh_player_is_gay", "role": "support"},
    "admin":         {"pass": "yamatekudasai210", "role": "quanly"},
}

ADMIN_OTP = os.environ.get("ADMIN_OTP", "123456")

BASE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    :root { --neon-blue: #00f3ff; --neon-pink: #ff00ff; --bg-dark: #050505; }
    body { font-family: 'Share Tech Mono', monospace; background: var(--bg-dark); color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)); }
    .box, .card { background: rgba(10, 10, 10, 0.9); border: 2px solid var(--neon-blue); padding: 2.5rem; width: 340px; box-shadow: 0 0 15px var(--neon-blue), inset 0 0 10px var(--neon-blue); text-transform: uppercase; }
    h2, h3 { color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); margin-top: 0; }
    input { width: 100%; padding: 0.8rem; margin: 0.5rem 0 1.5rem; background: #000; border: 1px solid var(--neon-pink); color: var(--neon-blue); font-family: 'Orbitron'; box-sizing: border-box; }
    button { width: 100%; padding: 0.8rem; background: transparent; border: 1px solid var(--neon-blue); color: var(--neon-blue); cursor: pointer; transition: 0.3s; font-weight: bold; }
    button:hover { background: var(--neon-blue); color: #000; box-shadow: 0 0 20px var(--neon-blue); }
    .err { color: var(--neon-pink); font-size: 0.8rem; margin-bottom: 1rem; text-shadow: 0 0 5px var(--neon-pink); }
    a { color: var(--neon-pink); text-decoration: none; font-size: 0.85rem; }
    .card { max-width: 600px; width: auto; }
</style>
"""

@app.before_request
def block_scanners():
    ua = request.headers.get("User-Agent", "").lower()
    bad = ["dirsearch", "gobuster", "sqlmap", "nmap", "nikto", "wfuzz"]
    if any(s in ua for s in bad): return "403 Forbidden", 403
    bad_patterns = [r"\.\.", r"\.\/", r"\{", r"\}", r"\(", r"\)"]
    if any(re.search(p, request.full_path) for p in bad_patterns): return "503 Service Unavailable", 200

# Error Handler 404 tùy chỉnh
@app.errorhandler(404)
def page_not_found(e):
    html = "<!doctype html><html><head><title>404</title>" + BASE_CSS + "</head><body><div class='box'><h2>// 404</h2><p class='err'>BRUH, U LOST?</p><a href='/'>GO BACK TO REALITY</a></div></body></html>"
    return render_template_string(html), 404

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
    html = "<!doctype html><html><head><title>Login</title>" + BASE_CSS + "</head><body><div class='box'><h2>// LOGIN</h2>{% if error %}<div class='err'>{{ error }}</div>{% endif %}<form method='POST'><label>Username</label><input name='user' autocomplete='off'><label>Password</label><input type='password' name='pass'><button type='submit'>ACCESS</button></form><a href='/register'>Register Account</a> | <a href='/about'>About</a></div></body></html>"
    return render_template_string(html, error=error)

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
    html = "<!doctype html><html><head><title>Register</title>" + BASE_CSS + "</head><body><div class='box'><h2>// Register</h2>{% if msg %}<div class='err'>{{ msg }}</div>{% endif %}<form method='POST'><label>Username</label><input name='user'><label>Password</label><input type='password' name='pass'><button type='submit'>REGISTER</button></form><a href='/'>Back</a></div></body></html>"
    return render_template_string(html, msg=msg)

@app.route("/panel")
def panel():
    if not session.get("user"): return redirect(url_for("login"))
    html = "<!doctype html><html><head><title>Panel</title>" + BASE_CSS + "</head><body><div class='card'><h3>// DASHBOARD</h3><p>User: <strong>{{ session.get('user') }}</strong></p>{% if session.get('role') == 'support' %}<p><a href='/view-log?file=app.log'>View app.log</a></p>{% endif %}{% if session.get('role') == 'quanly' %}<p><a href='/internal-assets/cerdentials.txt.bak'>cerdentials.txt.bak</a></p>{% endif %}{% if session.get('user') == 'admin' %}<p><a href='/admin'>Admin Panel</a></p>{% endif %}</div></body></html>"
    return render_template_string(html)

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if session.get("user") != "admin" or session.get("role") != "quanly": return "403", 403
    if request.method == "POST":
        if request.form.get("otp") == ADMIN_OTP: return "QA210{yamate_senpai_access_granted_2026}"
    html = "<!doctype html><html><head><title>Admin</title>" + BASE_CSS + "</head><body><div class='box'><form method='POST'><input name='otp' placeholder='OTP'><button>VERIFY</button></form></div></body></html>"
    return render_template_string(html)

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

@app.route("/about")
def about():
    html = "<!doctype html><html><head><title>About</title>" + BASE_CSS + "</head><body><div class='card'><h2>// SYSTEM INFO</h2><p>Bruh v2026.5</p><p>TIP: LOGS ARE NOT JUST TEXT. THEY ARE WINDOWS INTO THE SYSTEM.</p><br><a href='/'>← RETURN TO TERMINAL</a></div></body></html>"
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
