from flask import Flask, render_template, render_template_string, request, session, redirect, url_for, jsonify
from markupsafe import Markup
import uuid
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# -----------------------------------------------------------------------
# Blacklist — common SSTI keywords blocked by "VAR system"
# -----------------------------------------------------------------------
BLACKLIST = [
    'config', 'subprocess', 'import', 'popen',
    'system', 'eval', 'exec', '__class__',
    '__mro__', '__subclasses__', 'request',
    'application', 'globals'
]

def is_blacklisted(value: str) -> bool:
    lower = value.lower()
    return any(word in lower for word in BLACKLIST)

# -----------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if 'players' not in session:
        session['players'] = []
    count = len(session['players'])
    return render_template('dashboard.html', count=count)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'players' not in session:
        session['players'] = []

    error = None
    success = None

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        club      = request.form.get('club', '').strip()
        jersey_no = request.form.get('jersey_number', '').strip()
        signature = request.form.get('jersey_signature', '').strip()

        # Validation
        if not all([name, club, jersey_no, signature]):
            error = "All fields are required."
        elif not jersey_no.isdigit() or not (1 <= int(jersey_no) <= 99):
            error = "Jersey number must be between 1 and 99."
        elif is_blacklisted(signature):
            error = "🟥 VAR Review: Illegal input detected in Jersey Signature. Challenge flagged."
        else:
            player = {
                'id': str(uuid.uuid4()),
                'name': name,
                'club': club,
                'jersey_number': jersey_no,
                'signature': signature   # stored raw — rendered unsafely in /view
            }
            players = session['players']
            players.append(player)
            session['players'] = players
            session.modified = True
            success = f"{name} added to your squad!"

    return render_template('create.html', error=error, success=success)


@app.route('/view')
def view():
    if 'players' not in session:
        session['players'] = []

    players = session['players']
    rendered_cards = []

    for p in players:
        # ----------------------------------------------------------------
        # VULNERABLE SINK — jersey_signature fed directly into
        # render_template_string as raw template code. This is intentional
        # for the CTF challenge. DO NOT use this pattern in production.
        # ----------------------------------------------------------------
        try:
            rendered_sig = render_template_string(p['signature'])
        except Exception:
            rendered_sig = p['signature']

        rendered_cards.append({
            'id': p['id'],
            'name': p['name'],
            'club': p['club'],
            'jersey_number': p['jersey_number'],
            'signature': rendered_sig
        })

    return render_template('view.html', players=rendered_cards)


@app.route('/delete/<player_id>', methods=['POST'])
def delete(player_id):
    if 'players' in session:
        players = [p for p in session['players'] if p['id'] != player_id]
        session['players'] = players
        session.modified = True
    return redirect(url_for('view'))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
