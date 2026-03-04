import os
import traceback
from flask import Flask, request, redirect, url_for, session, make_response, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'please-set-a-secret-key')

ADMIN_PASSWORD  = os.environ.get('ADMIN_PASSWORD', 'admin')
VIEWER_PASSWORD = os.environ.get('VIEWER_PASSWORD', 'viewer')

UPLOAD_DIR     = '/tmp/dashboard_uploads'
DASHBOARD_FILE = os.path.join(UPLOAD_DIR, 'dashboard.html')
DASHBOARD_NAME = os.path.join(UPLOAD_DIR, 'dashboard_name.txt')


# ── Inline templates ──────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{ title }}</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#f0f2f5;min-height:100vh;display:flex;align-items:center;justify-content:center}
    .card{background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.09);
          padding:52px 44px 44px;width:100%;max-width:400px;text-align:center}
    .icon{width:52px;height:52px;background:#ede9fe;border-radius:50%;display:flex;
          align-items:center;justify-content:center;margin:0 auto 24px;font-size:22px}
    h1{font-size:20px;font-weight:700;color:#111;margin-bottom:6px}
    .sub{font-size:14px;color:#6b7280;margin-bottom:32px}
    input[type=password]{width:100%;padding:13px 16px;border:1.5px solid #e5e7eb;border-radius:9px;
                         font-size:15px;outline:none;transition:border-color .2s;margin-bottom:14px}
    input[type=password]:focus{border-color:#6d28d9;box-shadow:0 0 0 3px rgba(109,40,217,.1)}
    button{width:100%;padding:13px;background:#5b21b6;color:#fff;border:none;border-radius:9px;
           font-size:15px;font-weight:600;cursor:pointer;transition:background .2s}
    button:hover{background:#4c1d95}
    .error{color:#dc2626;font-size:13px;margin-top:12px;background:#fef2f2;padding:8px 12px;border-radius:7px}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">🔒</div>
    <h1>{{ title }}</h1>
    <p class="sub">Enter the password to continue</p>
    <form method="post">
      <input type="password" name="password" placeholder="Password" autofocus autocomplete="current-password"/>
      <button type="submit">Enter</button>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
    </form>
  </div>
</body>
</html>"""

EMPTY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Team Dashboard</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#f0f2f5;min-height:100vh;display:flex;align-items:center;justify-content:center}
    .card{background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.09);
          padding:60px 48px;width:100%;max-width:440px;text-align:center}
    .icon{font-size:48px;margin-bottom:20px}
    h1{font-size:20px;font-weight:700;color:#374151;margin-bottom:10px}
    p{font-size:15px;color:#6b7280;line-height:1.5}
    a{display:inline-block;margin-top:32px;font-size:13px;color:#9ca3af;text-decoration:none}
    a:hover{color:#6b7280}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">📭</div>
    <h1>No dashboard is live right now</h1>
    <p>Check back later, or ask your team lead to upload a dashboard.</p>
    <a href="/logout">Log out</a>
  </div>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Dashboard Manager</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#f0f2f5;min-height:100vh;display:flex;align-items:center;
         justify-content:center;padding:24px}
    .card{background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.09);
          padding:44px 40px;width:100%;max-width:480px}
    .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px}
    h1{font-size:20px;font-weight:700;color:#111}
    .logout{font-size:13px;color:#9ca3af;text-decoration:none}
    .logout:hover{color:#6b7280}
    .status{border-radius:10px;padding:16px 18px;margin-bottom:28px;
            display:flex;align-items:center;gap:12px}
    .status.active{background:#ecfdf5;border:1.5px solid #6ee7b7}
    .status.empty{background:#f9fafb;border:1.5px solid #e5e7eb}
    .dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
    .active .dot{background:#10b981}
    .empty  .dot{background:#d1d5db}
    .status-text{flex:1}
    .slabel{font-size:13px;font-weight:600;color:#374151}
    .sname{font-size:12px;color:#6b7280;margin-top:2px;word-break:break-all}
    .view-link{font-size:12px;color:#5b21b6;text-decoration:none;font-weight:500;white-space:nowrap}
    .view-link:hover{text-decoration:underline}
    .section-label{font-size:12px;font-weight:600;color:#9ca3af;text-transform:uppercase;
                   letter-spacing:.05em;margin-bottom:10px}
    .drop-zone{border:2px dashed #d1d5db;border-radius:10px;padding:28px 20px;text-align:center;
               cursor:pointer;transition:border-color .2s,background .2s;margin-bottom:12px;position:relative}
    .drop-zone:hover,.drop-zone.over{border-color:#7c3aed;background:#faf5ff}
    .drop-icon{font-size:28px;margin-bottom:8px}
    .drop-text{font-size:14px;color:#374151;font-weight:500}
    .drop-sub{font-size:12px;color:#9ca3af;margin-top:4px}
    #file-input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
    #file-name{font-size:13px;color:#5b21b6;font-weight:500;margin-bottom:12px;min-height:18px}
    .btn{width:100%;padding:13px;border:none;border-radius:9px;font-size:15px;
         font-weight:600;cursor:pointer;transition:background .2s,opacity .2s}
    .btn-primary{background:#5b21b6;color:#fff}
    .btn-primary:hover{background:#4c1d95}
    .btn-primary:disabled{opacity:.45;cursor:not-allowed}
    .btn-danger{background:#fee2e2;color:#b91c1c;margin-top:10px}
    .btn-danger:hover{background:#fecaca}
    hr{border:none;border-top:1px solid #f3f4f6;margin:28px 0}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>Dashboard Manager</h1>
      <a class="logout" href="/logout">Log out</a>
    </div>

    <div class="status {{ 'active' if has_file else 'empty' }}">
      <div class="dot"></div>
      <div class="status-text">
        <div class="slabel">{{ 'Dashboard is live' if has_file else 'No dashboard active' }}</div>
        <div class="sname">{{ filename if has_file else 'Upload a file below to share it with your team' }}</div>
      </div>
      {% if has_file %}<a class="view-link" href="/" target="_blank">View →</a>{% endif %}
    </div>

    <p class="section-label">Upload New Dashboard</p>
    <form action="/upload" method="post" enctype="multipart/form-data">
      <div class="drop-zone" id="dz">
        <input type="file" name="file" id="file-input" accept=".html"/>
        <div class="drop-icon">📄</div>
        <div class="drop-text">Click to choose a file, or drag &amp; drop</div>
        <div class="drop-sub">HTML files only</div>
      </div>
      <div id="file-name"></div>
      <button class="btn btn-primary" id="upload-btn" disabled>Upload &amp; Go Live</button>
    </form>

    {% if has_file %}
    <hr/>
    <p class="section-label">Remove Current Dashboard</p>
    <form action="/clear" method="post"
          onsubmit="return confirm('Remove the dashboard? Viewers will see an empty page.')">
      <button class="btn btn-danger">Clear Dashboard</button>
    </form>
    {% endif %}
  </div>

  <script>
    const inp = document.getElementById('file-input');
    const lbl = document.getElementById('file-name');
    const btn = document.getElementById('upload-btn');
    const dz  = document.getElementById('dz');
    inp.addEventListener('change', () => {
      if (inp.files.length) { lbl.textContent = '✓ ' + inp.files[0].name; btn.disabled = false; }
    });
    dz.addEventListener('dragover',  e => { e.preventDefault(); dz.classList.add('over'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('over'));
    dz.addEventListener('drop', e => {
      e.preventDefault(); dz.classList.remove('over');
      const file = e.dataTransfer.files[0];
      if (file && file.name.toLowerCase().endsWith('.html')) {
        const dt = new DataTransfer(); dt.items.add(file); inp.files = dt.files;
        lbl.textContent = '✓ ' + file.name; btn.disabled = false;
      } else { lbl.textContent = '⚠ Please drop an .html file'; }
    });
  </script>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Something went wrong</title>
  <style>
    body{font-family:-apple-system,sans-serif;background:#f0f2f5;min-height:100vh;
         display:flex;align-items:center;justify-content:center}
    .card{background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.09);
          padding:52px 44px;max-width:420px;text-align:center}
    .icon{font-size:40px;margin-bottom:16px}
    h1{font-size:18px;font-weight:700;color:#111;margin-bottom:8px}
    p{font-size:14px;color:#6b7280;line-height:1.5}
    a{color:#5b21b6;text-decoration:none}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">⚠️</div>
    <h1>Something went wrong</h1>
    <p>The server hit an unexpected error. Try <a href="/">going back</a>.</p>
  </div>
</body>
</html>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_dashboard():
    try:
        if os.path.exists(DASHBOARD_FILE):
            with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception:
        pass
    return None

def get_dashboard_name():
    try:
        if os.path.exists(DASHBOARD_NAME):
            with open(DASHBOARD_NAME, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception:
        pass
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    return 'ok', 200

@app.route('/', methods=['GET', 'POST'])
def view():
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw in (VIEWER_PASSWORD, ADMIN_PASSWORD):
            session['viewer_ok'] = True
            return redirect(url_for('view'))
        return render_template_string(LOGIN_HTML, error='Incorrect password', title='Team Dashboard')
    if not session.get('viewer_ok'):
        return render_template_string(LOGIN_HTML, error=None, title='Team Dashboard')
    html = get_dashboard()
    if html is None:
        return render_template_string(EMPTY_HTML)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and 'password' in request.form:
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin_ok'] = True
            return redirect(url_for('admin'))
        return render_template_string(LOGIN_HTML, error='Incorrect password', title='Admin Access')
    if not session.get('admin_ok'):
        return render_template_string(LOGIN_HTML, error=None, title='Admin Access')
    return render_template_string(ADMIN_HTML, has_file=get_dashboard() is not None, filename=get_dashboard_name())

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('admin_ok'):
        return redirect(url_for('admin'))
    f = request.files.get('file')
    if f and f.filename.lower().endswith('.html'):
        ensure_upload_dir()
        content = f.read().decode('utf-8')
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as out:
            out.write(content)
        with open(DASHBOARD_NAME, 'w', encoding='utf-8') as out:
            out.write(f.filename)
    return redirect(url_for('admin'))

@app.route('/clear', methods=['POST'])
def clear():
    if not session.get('admin_ok'):
        return redirect(url_for('admin'))
    for path in [DASHBOARD_FILE, DASHBOARD_NAME]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('view'))

@app.errorhandler(500)
def internal_error(e):
    if os.environ.get('SHOW_ERRORS'):
        return f'<pre style="padding:2rem;font-size:13px">{traceback.format_exc()}</pre>', 500
    return render_template_string(ERROR_HTML), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
