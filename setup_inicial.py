#!/usr/bin/env python3
"""
RE/MAX FARO — Setup inicial de usuarios
Ejecutar UNA SOLA VEZ después de subir la aplicación al servidor.
"""
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB = "campos_remax.db"

def setup():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Crear tabla usuarios si no existe
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT, apellido TEXT, email TEXT UNIQUE,
            password TEXT, rol TEXT DEFAULT 'gestor',
            activo INTEGER DEFAULT 1, fecha_alta TEXT, ultimo_acceso TEXT
        )
    """)

    usuarios = [
        # (nombre, apellido, email, contraseña, rol)
        # ⚠️ CAMBIAR CONTRASEÑAS ANTES DE USAR EN PRODUCCIÓN
        ("Diego",   "Admin",    "diego@remaxfaro.com",   "RemaxFaro2025!",  "admin"),
        ("Gestor",  "Uno",      "gestor1@remaxfaro.com", "Gestor1_2025!",   "gestor"),
        ("Gestor",  "Dos",      "gestor2@remaxfaro.com", "Gestor2_2025!",   "gestor"),
        ("Gestor",  "Tres",     "gestor3@remaxfaro.com", "Gestor3_2025!",   "gestor"),
    ]

    print("\n{'='*50}")
    print("RE/MAX FARO — Setup de Usuarios")
    print("{'='*50}\n")

    for nombre, apellido, email, pwd, rol in usuarios:
        pwd_hash = generate_password_hash(pwd)
        try:
            c.execute("""
                INSERT INTO usuarios (nombre,apellido,email,password,rol,activo,fecha_alta)
                VALUES (?,?,?,?,?,1,?)
            """, (nombre, apellido, email, pwd_hash, rol, datetime.now().isoformat()))
            conn.commit()
            print(f"✓ {nombre} {apellido} | {email} | Rol: {rol}")
            if rol == "admin":
                print(f"  → Contraseña temporal: {pwd} (CAMBIARLA DESPUÉS)")
        except sqlite3.IntegrityError:
            print(f"  (ya existe): {email}")

    print("\n✓ Setup completado. Usuarios listos.")
    print("⚠️  Recordá cambiar las contraseñas desde el panel Admin.\n")
    conn.close()

if __name__ == "__main__":
    setup()
