from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Menyimpan alamat IP perangkat secara dinamis di memori server
device_registry = {}

@app.route('/')
def home():
    return "AMETHA LAB - FLASK RELAY SERVER IS ACTIVE"

# PERBAIKAN UTAMA: Mengizinkan metode GET agar bisa diakses langsung saat tautan diklik di browser HP
@app.route('/handshake', methods=['GET', 'POST'])
def background_handshake():
    """Menerima ketukan data otomatis dari browser HP target saat memindai/mengklik QR Code."""
    # 1. Deteksi IP Publik HP Anda yang berkunjung lewat internet luar secara otomatis
    device_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Jika ada banyak IP proxy terdaftar, ambil IP pertama (IP asli ponsel)
    if device_ip and ',' in device_ip:
        device_ip = device_ip.split(',')[0].strip()
        
    device_port = "5555" # Port standar nirkabel ADB Android
    
    if device_ip:
        target_address = f"{device_ip}:{device_port}"
        device_registry["active_target"] = target_address
        
        # Tampilan pesan sukses di layar browser HP Anda agar senyap dan informatif
        return f"""
        <html>
            <head><title>Success</title></head>
            <body style="background-color: black; color: #00ff00; font-family: monospace; text-align: center; padding-top: 50px;">
                <h2>[ AMETHA LAB SECURITY ]</h2>
                <p>Paket Terkonfirmasi.</p>
                <p>Status Gateway: {target_address}</p>
                <p>Anda bisa menutup halaman ini sekarang.</p>
            </body>
        </html>
        """, 200
        
    return jsonify({"status": "failed", "message": "No IP detected"}), 400

@app.route('/get_target', methods=['GET'])
def get_target_device():
    """Dipanggil oleh PC Lab untuk menarik otomatis IP HP yang sudah terkunci di server."""
    target = device_registry.get("active_target", "")
    if target:
        return jsonify({"status": "ready", "target": target}), 200
    return jsonify({"status": "waiting", "target": ""}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
