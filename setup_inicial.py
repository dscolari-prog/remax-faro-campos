import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB = "campos_remax.db"

def setup():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT, apellido TEXT, email TEXT UNIQUE,
            password TEXT, rol TEXT DEFAULT 'gestor',
            activo INTEGER DEFAULT 1, fecha_alta TEXT, ultimo_acceso TEXT
        )
    """)
    usuarios = [
        ("Diego","Admin","diego@remaxfaro.com","RemaxFaro2025!","admin"),
        ("Gestor","Uno","gestor1@remaxfaro.com","Gestor1_2025!","gestor"),
    ]
    for nombre,apellido,email,pwd,rol in usuarios:
        pwd_hash = generate_password_hash(pwd)
        try:
            c.execute("INSERT INTO usuarios (nombre,apellido,email,password,rol,activo,fecha_alta) VALUES (?,?,?,?,?,1,?)",
                (nombre,apellido,email,pwd_hash,rol,datetime.now().isoformat()))
            conn.commit()
            print(f"✓ {email} creado")
        except sqlite3.IntegrityError:
            print(f"Ya existe: {email}")
    conn.close()
    print("Setup completado.")

if __name__ == "__main__":
    setup()
