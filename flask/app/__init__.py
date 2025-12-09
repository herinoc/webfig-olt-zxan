# app/__init__.py
from app.routes import main
from flask import Flask

def create_app():
    app = Flask(__name__)

    # Simpan konfigurasi, bukan koneksi
    app.config['DB_CONFIG'] = {
        'host': 'localhost',
        'user': 'root',
        'password': 'tux',
        'database': 'nms_db'
    }

    from .routes import main
    app.register_blueprint(main)

    return app
