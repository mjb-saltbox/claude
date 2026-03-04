from flask import Flask, render_template, request, redirect, url_for, session, make_response
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'please-set-a-secret-key')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
VIEWER_PASSWORD = os.environ.get('VIEWER_PASSWORD', 'viewer')

DASHBOARD_FILE = '/tmp/dashboard.html'
DASHBOARD_NAME_FILE = '/tmp/dashboard_name.txt'


def get_dashboard():
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def get_dashboard_name():
    if os.path.exists(DASHBOARD_NAME_FILE):
        with open(DASHBOARD_NAME_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


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
        content = f.read().decode('utf-8')
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as out:
            out.write(content)
        with open(DASHBOARD_NAME_FILE, 'w', encoding='utf-8') as out:
            out.write(f.filename)
    return redirect(url_for('admin'))


@app.route('/clear', methods=['POST'])
def clear():
    if not session.get('admin_ok'):
        return redirect(url_for('admin'))

    for path in [DASHBOARD_FILE, DASHBOARD_NAME_FILE]:
        if os.path.exists(path):
            os.remove(path)

    return redirect(url_for('admin'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('view'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
