#!/usr/bin/env python3
# =============================================================================
# RE/MAX FARO — Campo Track | Servidor Web (Flask)
# Maneja autenticación, usuarios y sirve la API de campos
# =============================================================================

from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, json, os
from datetime import datetime

app = Flask(__name__, static_folder="static")
app.secret_key = "RemaxFaro2025SecretKey!CampoTrack"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

DB_PATH = "campos_remax.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---- MODELO USUARIO ----
class Usuario(UserMixin):
    def __init__(self, id, nombre, apellido, email, rol):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.rol = rol

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    u = conn.execute("SELECT * FROM usuarios WHERE id=? AND activo=1", (user_id,)).fetchone()
    if u:
        return Usuario(u["id"], u["nombre"], u["apellido"], u["email"], u["rol"])
    return None

# ---- RUTAS ----
@app.route("/")
@login_required
def index():
    return send_from_directory("static", "index.html")

@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        data = request.get_json() or request.form
        email = data.get("email","").strip().lower()
        password = data.get("password","")
        conn = get_db()
        u = conn.execute("SELECT * FROM usuarios WHERE email=? AND activo=1",
                         (email,)).fetchone()
        if u and check_password_hash(u["password"], password):
            user = Usuario(u["id"], u["nombre"], u["apellido"], u["email"], u["rol"])
            login_user(user, remember=True)
            conn.execute("UPDATE usuarios SET ultimo_acceso=? WHERE id=?",
                        (datetime.now().isoformat(), u["id"]))
            conn.commit()
            return jsonify({"ok": True, "nombre": u["ndef index():
    return send_from_directory("static", "login.html")ombre"], "rol": u["rol"]})
        return jsonify({"ok": False, "msg": "Email o contraseña incorrectos"}), 401
    return send_from_directory("static", "login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---- API CAMPOS ----
@app.route("/api/campos")
@login_required
def api_campos():
    conn = get_db()
    q = request.args.get("q","")
    tipo = request.args.get("tipo","")
    zona = request.args.get("zona","")
    ha_min = request.args.get("ha_min", 0, type=float)
    ha_max = request.args.get("ha_max", 999999, type=float)
    dueno = request.args.get("dueno","")
    fuente = request.args.get("fuente","")
    captado = request.args.get("captado","")

    sql = "SELECT * FROM campos WHERE activo=1"
    params = []
    if q:
        sql += " AND (titulo LIKE ? OR localidad LIKE ? OR zona LIKE ? OR descripcion LIKE ?)"
        params += [f"%{q}%"]*4
    if tipo:
        sql += " AND tipo=?"; params.append(tipo)
    if zona:
        sql += " AND zona=?"; params.append(zona)
    if ha_min:
        sql += " AND hectareas>=?"; params.append(ha_min)
    if ha_max < 999999:
        sql += " AND hectareas<=?"; params.append(ha_max)
    if dueno == "si":
        sql += " AND dueno_vende=1"
    elif dueno == "no":
        sql += " AND dueno_vende=0"
    if fuente:
        sql += " AND fuente=?"; params.append(fuente)
    if captado == "si":
        sql += " AND captado=1"
    sql += " ORDER BY fecha_scraping DESC"

    rows = conn.execute(sql, params).fetchall()
    return jsonify({"campos": [dict(r) for r in rows], "total": len(rows)})

@app.route("/api/campos/<int:campo_id>", methods=["GET","PUT"])
@login_required
def api_campo_detalle(campo_id):
    conn = get_db()
    if request.method == "PUT":
        data = request.get_json()
        allowed = ["tipo","zona","localidad","notas","captado","dueno_vende",
                   "hectareas","precio_usd","lat","lng","geolocalizdo"]
        sets = ", ".join([f"{k}=?" for k in data if k in allowed])
        vals = [data[k] for k in data if k in allowed] + [campo_id]
        conn.execute(f"UPDATE campos SET {sets} WHERE id=?", vals)
        conn.commit()
        return jsonify({"ok": True})
    row = conn.execute("SELECT * FROM campos WHERE id=?", (campo_id,)).fetchone()
    return jsonify(dict(row)) if row else (jsonify({"error":"No encontrado"}), 404)

@app.route("/api/campos", methods=["POST"])
@login_required
def api_campo_nuevo():
    data = request.get_json()
    conn = get_db()
    conn.execute("""
        INSERT INTO campos (titulo,tipo,hectareas,precio_usd,zona,localidad,fuente,
                           url_original,lat,lng,geolocalizdo,dueno_vende,descripcion,
                           fecha_scraping,activo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
    """, (data.get("titulo"), data.get("tipo"), data.get("hectareas"),
          data.get("precio_usd"), data.get("zona"), data.get("localidad"),
          "Carga Manual", data.get("url_original"), data.get("lat"),
          data.get("lng"), 1 if data.get("lat") else 0,
          1 if data.get("dueno_vende") else 0,
          data.get("descripcion"), datetime.now().isoformat()))
    conn.commit()
    return jsonify({"ok": True})

# ---- API CRM ----
@app.route("/api/crm/acciones", methods=["POST"])
@login_required
def api_crm_accion():
    data = request.get_json()
    conn = get_db()
    conn.execute("""
        INSERT INTO crm_acciones (campo_id, usuario_id, tipo_accion, descripcion, fecha)
        VALUES (?,?,?,?,?)
    """, (data.get("campo_id"), current_user.id, data.get("tipo_accion"),
          data.get("descripcion"), datetime.now().isoformat()))
    conn.commit()
    return jsonify({"ok": True})

@app.route("/api/crm/acciones/<int:campo_id>")
@login_required
def api_crm_historial(campo_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT a.*, u.nombre, u.apellido FROM crm_acciones a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.campo_id=? ORDER BY a.fecha DESC
    """, (campo_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

# ---- API USUARIOS (solo admin) ----
@app.route("/api/usuarios", methods=["GET","POST"])
@login_required
def api_usuarios():
    if current_user.rol != "admin":
        return jsonify({"error": "Sin permiso"}), 403
    conn = get_db()
    if request.method == "POST":
        data = request.get_json()
        pwd_hash = generate_password_hash(data["password"])
        try:
            conn.execute("""
                INSERT INTO usuarios (nombre,apellido,email,password,rol,activo,fecha_alta)
                VALUES (?,?,?,?,?,1,?)
            """, (data["nombre"], data["apellido"], data["email"], pwd_hash,
                  data.get("rol","gestor"), datetime.now().isoformat()))
            conn.commit()
            return jsonify({"ok": True})
        except:
            return jsonify({"ok": False, "msg": "Email ya registrado"}), 400
    rows = conn.execute(
        "SELECT id, nombre, apellido, email, rol, activo, fecha_alta, ultimo_acceso FROM usuarios"
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/usuarios/<int:uid>", methods=["PUT","DELETE"])
@login_required
def api_usuario_detalle(uid):
    if current_user.rol != "admin":
        return jsonify({"error": "Sin permiso"}), 403
    conn = get_db()
    if request.method == "DELETE":
        conn.execute("UPDATE usuarios SET activo=0 WHERE id=?", (uid,))
        conn.commit()
        return jsonify({"ok": True})
    data = request.get_json()
    if "password" in data and data["password"]:
        data["password"] = generate_password_hash(data["password"])
    allowed = ["nombre","apellido","email","rol","activo","password"]
    sets = ", ".join([f"{k}=?" for k in data if k in allowed])
    vals = [data[k] for k in data if k in allowed] + [uid]
    conn.execute(f"UPDATE usuarios SET {sets} WHERE id=?", vals)
    conn.commit()
    return jsonify({"ok": True})

# ---- API ESTADÍSTICAS ----
@app.route("/api/estadisticas")
@login_required
def api_stats():
    conn = get_db()
    stats = {}
    stats["total"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1").fetchone()[0]
    stats["dueno_vende"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1 AND dueno_vende=1").fetchone()[0]
    stats["captados"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1 AND captado=1").fetchone()[0]
    stats["geolocalizados"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1 AND geolocalizdo=1").fetchone()[0]
    stats["por_tipo"] = dict(conn.execute(
        "SELECT tipo, COUNT(*) FROM campos WHERE activo=1 GROUP BY tipo").fetchall())
    stats["por_zona"] = dict(conn.execute(
        "SELECT zona, COUNT(*) FROM campos WHERE activo=1 GROUP BY zona").fetchall())
    stats["por_fuente"] = dict(conn.execute(
        "SELECT fuente, COUNT(*) FROM campos WHERE activo=1 GROUP BY fuente").fetchall())
    stats["ha_total"] = conn.execute(
        "SELECT SUM(hectareas) FROM campos WHERE activo=1").fetchone()[0] or 0
    stats["precio_prom_ha"] = conn.execute(
        "SELECT AVG(precio_ha_usd) FROM campos WHERE activo=1 AND precio_ha_usd > 0").fetchone()[0] or 0
    return jsonify(stats)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
