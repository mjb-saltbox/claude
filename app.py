import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, make_response

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'please-set-a-secret-key')

ADMIN_PASSWORD  = os.environ.get('ADMIN_PASSWORD', 'admin')
VIEWER_PASSWORD = os.environ.get('VIEWER_PASSWORD', 'viewer')

# /tmp is guaranteed writable on Render (and most cloud platforms)
UPLOAD_DIR     = '/tmp/dashboard_uploads'
DASHBOARD_FILE = os.path.join(UPLOAD_DIR, 'dashboard.html')
DASHBOARD_NAME = os.path.join(UPLOAD_DIR, 'dashboard_name.txt')


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


# ── Health check (useful for UptimeRobot pings) ───────────────────────────────

@app.route('/health')
def health():
    return 'ok', 200


# ── Viewer ────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def view():
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw in (VIEWER_PASSWORD, ADMIN_PASSWORD):
            session['viewer_ok'] = True
            return redirect(url_for('view'))
        return render_template('login.html', error='Incorrect password', title='Team Dashboard')

    if not session.get('viewer_ok'):
        return render_template('login.html', error=None, title='Team Dashboard')

    html = get_dashboard()
    if html is None:
        return render_template('empty.html')

    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and 'password' in request.form:
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin_ok'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error='Incorrect password', title='Admin Access')

    if not session.get('admin_ok'):
        return render_template('login.html', error=None, title='Admin Access')

    return render_template(
        'admin.html',
        has_file=get_dashboard() is not None,
        filename=get_dashboard_name()
    )


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


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(500)
def internal_error(e):
    tb = traceback.format_exc()
    # Only expose details if SHOW_ERRORS env var is set — remove after debugging
    if os.environ.get('SHOW_ERRORS'):
        return f'<pre style="padding:2rem;font-size:13px">{tb}</pre>', 500
    return render_template('error.html'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
