from flask import Flask, request, redirect, render_template_string
import json

app = Flask(__name__)

# Variabel global di memori RAM Render yang kebal mati listrik
ALAMAT_NGROK_LAB = ""
PERANGKAT_TERDAFTAR = {}

@app.route('/handshake', methods=['GET', 'POST'])
def handshake():
    global ALAMAT_NGROK_LAB
    
    # JALUR A: Menerima setoran alamat Ngrok baru dari aplikasi run.py PC Lab Anda
    ip_lab = request.args.get('ip_lab')
    if ip_lab:
        ALAMAT_NGROK_LAB = ip_lab.replace("tcp://", "").strip()
        return f"✅ Koordinat Lab Sukses Terkunci di Render: {ALAMAT_NGROK_LAB}", 200

    # JALUR B: HP Target mendeteksi sesi lama dan meminta panggil balik (Auto-Reconnect)
    token_reconnect = request.args.get('reconnect')
    if token_reconnect:
        if not ALAMAT_NGROK_LAB:
            return "❌ PC Lab sedang offline atau belum menyetorkan alamat Ngrok baru.", 503
        
        destination_url = ALAMAT_NGROK_LAB
        if not destination_url.startswith("http"):
            destination_url = f"https://{destination_url}"
            
        # Langsung bypass halaman utama, lempar koneksi HP target menuju server lokal PC Lab Anda
        return redirect(destination_url)

    # JALUR C: HP Target melakukan pemindaian QR Code pertama kali (Pemberian Otoritas Sesi)
    # Menyuguhkan halaman antarmuka pintar yang akan merekam Token ke LocalStorage ponsel target
    return render_template_string("""
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
            <h2>[ MEDUSA AUTOMATION PROXY ]</h2>
            <p id="status-text">Mengecek otentikasi sesi perangkat...</p>
            <br>
            <button id="main-btn" class="btn" onclick="mulaiOtomatisasi()" style="display:none;">OTORISASI PERANGKAT</button>
        </div>

        <script>
            // Memeriksa apakah memori internal ponsel target sudah menyimpan token lama
            let tokenSesi = localStorage.getItem("medusa_session_token");
            
            if (tokenSesi) {
                document.getElementById("status-text").innerText = "Sesi valid ditemukan! Menghubungkan ulang ke PC Lab...";
                setTimeout(() => {
                    window.location.href = window.location.pathname + "?reconnect=" + tokenSesi;
                }, 1200);
            } else {
                document.getElementById("status-text").innerText = "Otoritas perangkat diperlukan untuk sinkronisasi pertama.";
                document.getElementById("main-btn").style.display = "inline-block";
            }

            function mulaiOtomatisasi() {
                // Generate token acak unik untuk mengunci identitas browser HP target ini
                let tokenBaru = "HP_" + Math.random().toString(36).substring(2, 9).toUpperCase();
                localStorage.setItem("medusa_session_token", tokenBaru);
                
                let labAddress = "{{ alamat_lab }}";
                if (!labAddress.startsWith("http")) {
                    labAddress = "https://" + labAddress;
                }
                
                // Daftarkan token baru dan lempar browser HP target melintasi gerbang proxy menuju PC Lab
                window.location.href = labAddress + "/?register_token=" + tokenBaru;
            }
        </script>
    </body>
    </html>
    """, alamat_lab=ALAMAT_NGROK_LAB), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
