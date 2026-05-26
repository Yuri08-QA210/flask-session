import os
import time
import hashlib
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


@app.before_request
def block_scanners():
    ua = request.headers.get("User-Agent", "").lower()
    bad = ["dirsearch", "gobuster", "sqlmap", "nmap", "nikto", "wfuzz"]
    if any(s in ua for s in bad):
        return "403 Forbidden - Scanner detected", 403


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
    return render_template_string(LOGIN_TMPL, error=error)


LOGIN_TMPL = """
<!doctype html><html><head><title>Login – CTF Lab</title>
<style>
  body{font-family:monospace;background:#0d1117;color:#58a6ff;display:flex;
       justify-content:center;align-items:center;height:100vh;margin:0}
  .box{border:1px solid #30363d;padding:2rem;width:320px;background:#161b22}
  h2{margin:0 0 1rem;color:#e6edf3}
  input{width:100%;box-sizing:border-box;padding:.5rem;margin:.4rem 0 1rem;
        background:#0d1117;border:1px solid #30363d;color:#e6edf3;font-family:monospace}
  button{width:100%;padding:.6rem;background:#238636;border:none;color:#fff;
         font-family:monospace;cursor:pointer;font-size:1rem}
  .err{color:#f85149;margin-bottom:.8rem}
  a{color:#58a6ff;font-size:.85rem}
</style></head><body>
<div class="box">
  <h2>// CTF Login</h2>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <form method="POST">
    <label>Username</label><input name="user" autocomplete="off">
    <label>Password</label><input type="password" name="pass">
    <button type="submit">LOGIN</button>
  </form>
  <br><a href="/about">About</a> &nbsp;|&nbsp; <a href="/register">Register</a>
</div></body></html>
"""


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def register():
    msg = ""
    if request.method == "POST":
        u = request.form.get("user", "").strip()
        p = request.form.get("pass", "")

        role = "guest"

        if not u or not p:
            msg = "Username and password required."
        elif u in USERS_DB:
            msg = "User already exists."
        else:
            USERS_DB[u] = {"pass": p, "role": role}
            # Log to security.log if someone tried to send a role param anyway
            attempted_role = request.form.get("role", "")
            if attempted_role and attempted_role != "guest":
                with open("logs/security.log", "a") as f:
                    f.write(
                        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ALERT: "
                        f"Role escalation attempt by '{u}' requesting role '{attempted_role}'\n"
                    )
            return redirect(url_for("login"))
    return render_template_string(REG_TMPL, msg=msg)


REG_TMPL = """
<!doctype html><html><head><title>Register</title>
<style>
  body{font-family:monospace;background:#0d1117;color:#58a6ff;display:flex;
       justify-content:center;align-items:center;height:100vh;margin:0}
  .box{border:1px solid #30363d;padding:2rem;width:320px;background:#161b22}
  h2{margin:0 0 1rem;color:#e6edf3}
  input{width:100%;box-sizing:border-box;padding:.5rem;margin:.4rem 0 1rem;
        background:#0d1117;border:1px solid #30363d;color:#e6edf3;font-family:monospace}
  button{width:100%;padding:.6rem;background:#1f6feb;border:none;color:#fff;
         font-family:monospace;cursor:pointer;font-size:1rem}
  .msg{color:#f85149;margin-bottom:.8rem}
  a{color:#58a6ff;font-size:.85rem}
</style></head><body>
<div class="box">
  <h2>// Register</h2>
  {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
  <form method="POST">
    <label>Username</label><input name="user" autocomplete="off">
    <label>Password</label><input type="password" name="pass">
    <!-- No role field exposed to player -->
    <button type="submit">REGISTER</button>
  </form>
  <br><a href="/">Back to Login</a>
</div></body></html>
"""


@app.route("/panel")
def panel():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template_string(PANEL_TMPL)


PANEL_TMPL = """
<!doctype html><html><head><title>Panel</title>
<style>
  body{font-family:monospace;background:#0d1117;color:#e6edf3;padding:2rem}
  .card{border:1px solid #30363d;padding:1.5rem;margin:1rem 0;background:#161b22;max-width:600px}
  h3{margin:0 0 .5rem;color:#58a6ff}
  a{color:#3fb950}
  .tag{display:inline-block;padding:.1rem .5rem;border-radius:3px;font-size:.8rem;
       background:#21262d;color:#8b949e;margin-left:.5rem}
</style></head><body>
<div class="card">
  <h3>// Dashboard</h3>
  <p>User: <strong>{{ session.get("user") }}</strong>
     <span class="tag">{{ session.get("role") }}</span></p>

  {% if session.get("role") == "support" %}
  <p> System Logs: <a href="/view-log?file=app.log">View app.log</a></p>
  <p><small>Hint: Check the log carefully — it may reveal where other files are stored.</small></p>
  {% endif %}

  {% if session.get("role") == "quanly" %}
  <p> Manager Access: <a href="/internal-assets/cerdentials.txt.bak">cerdentials.txt.bak</a></p>
  {% endif %}

  {% if session.get("user") == "admin" and session.get("role") == "quanly" %}
  <p> Admin Portal: <a href="/admin">Go to Admin Panel</a></p>
  {% endif %}

  {% if session.get("role") == "guest" %}
  <p>You have guest access. Nothing to see here... or is there?</p>
  {% endif %}
</div>
</body></html>
"""


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if session.get("user") != "admin" or session.get("role") != "quanly":
        return "403 Access Denied", 403

    error = ""
    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        if otp == ADMIN_OTP and ADMIN_OTP:
            return render_template_string("""
<!doctype html><html><head><title>Flag 3</title>
<style>body{font-family:monospace;background:#0d1117;color:#3fb950;
      display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{border:1px solid #238636;padding:2rem;background:#0d2a0d;text-align:center}
h2{color:#58d68d}pre{color:#f0e68c;font-size:1.2rem}</style></head><body>
<div class="box"><h2>🚩 FLAG 3 CAPTURED</h2>
<pre>FLAG{admin_privileged_access_granted_2026}</pre>
<p>Congratulations! You completed the full CTF chain.</p>
</div></body></html>
""")
        error = "Invalid OTP."

    return render_template_string("""
<!doctype html><html><head><title>Admin OTP</title>
<style>body{font-family:monospace;background:#0d1117;color:#e6edf3;
      display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{border:1px solid #30363d;padding:2rem;width:340px;background:#161b22}
h2{color:#58a6ff}input{width:100%;box-sizing:border-box;padding:.5rem;
   background:#0d1117;border:1px solid #30363d;color:#e6edf3;font-family:monospace;margin:.5rem 0 1rem}
button{width:100%;padding:.6rem;background:#238636;border:none;color:#fff;cursor:pointer;font-family:monospace}
.err{color:#f85149;margin-bottom:.8rem}</style></head><body>
<div class="box">
  <h2>// Admin Portal</h2>
  <p>Enter the OTP found in <code>cerdentials.txt.bak</code></p>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <form method="POST">
    <input name="otp" placeholder="OTP code" autocomplete="off">
    <button type="submit">VERIFY</button>
  </form>
</div></body></html>
""", error=error)


@app.route("/internal-assets/<path:filename>")
def secure_assets(filename):
    if session.get("role") != "quanly":
        return "403 Forbidden", 403
    # Prevent path traversal on THIS endpoint
    safe = os.path.basename(filename)
    return send_from_directory("internal_assets", safe)


@app.route("/view-log")
def view_log():
    if not session.get("user"):
        return redirect(url_for("login"))

    filename = request.args.get("file", "")

    if filename == "app.log":
        try:
            return "<pre>" + open(os.path.join("logs", "app.log"), "r").read() + "</pre>"
        except Exception:
            return "File not found", 404

    if session.get("user") != "support_staff":
        return "403 Forbidden - Support staff only", 403

    try:
        file_path = os.path.join("logs", filename)
        content = open(file_path, "r").read()
        return "<pre>" + content + "</pre>"
    except Exception:
        return "File not found", 404


@app.route("/about")
def about():
    return """<!doctype html><html><head><title>About</title>
<style>body{font-family:monospace;background:#0d1117;color:#8b949e;padding:2rem}
h2{color:#58a6ff}code{color:#3fb950}a{color:#58a6ff}</style></head><body>
<h2>// CTF Challenge Platform</h2>
<p>This platform runs a Flask application serving support and management staff.</p>
<p>Known accounts: <code>support_staff</code> (support role), management (role: quanly).</p>
<p>Tip: Support staff can <code>view-log</code> files. Logs sometimes contain sensitive paths.</p>
<br><a href="/">← Back to Login</a>
</body></html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
