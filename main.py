from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Memori RAM Render untuk menyimpan alamat port nirkabel PC Lab
ALAMAT_NGROK_LAB = ""

@app.route('/handshake', methods=['GET', 'POST'])
def handshake():
    global ALAMAT_NGROK_LAB
    
    # JALUR A: Menangkap sinkronisasi koordinat dari aplikasi run.py PC Lab Anda
    ip_lab = request.args.get('ip_lab')
    if ip_lab:
        ALAMAT_NGROK_LAB = ip_lab.replace("https://", "").replace("http://", "").strip()
        return f"✅ Terkunci: {ALAMAT_NGROK_LAB}", 200

    # JALUR B: HP TARGET SCAN QR (HTTP 302 REDIRECT - BYPASS ABOUT:BLANK#BLOCKED)
    if not ALAMAT_NGROK_LAB:
        return "❌ Server PC Lab Anda belum menyetorkan alamat Ngrok baru ke awan Render.", 503

    # Memaksa browser HP target melompat lurus melalui header HTTP resmi (100% Lolos Sensor Android)
    destination_url = f"https://{ALAMAT_NGROK_LAB}"
    return redirect(destination_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
