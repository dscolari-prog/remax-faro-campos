from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from datetime import datetime

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "RemaxFaro2025SecretKey")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

DB_PATH = "campos_remax.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class Usuario(UserMixin):
    def __init__(self, id, nombre, email, rol):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.rol = rol

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    u = conn.execute("SELECT * FROM usuarios WHERE id=? AND activo=1", (user_id,)).fetchone()
    if u:
        return Usuario(u["id"], u["nombre"], u["email"], u["rol"])
    return None

@app.route("/")
@login_required
def index():
    return send_from_directory("static", "login.html")

@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        data = request.get_json() or request.form
        email = data.get("email","").strip().lower()
        password = data.get("password","")
        conn = get_db()
        u = conn.execute("SELECT * FROM usuarios WHERE email=? AND activo=1", (email,)).fetchone()
        if u and check_password_hash(u["password"], password):
            user = Usuario(u["id"], u["nombre"], u["email"], u["rol"])
            login_user(user, remember=True)
            return jsonify({"ok": True, "nombre": u["nombre"]})
        return jsonify({"ok": False, "msg": "Email o contraseña incorrectos"}), 401
    return send_from_directory("static", "index.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")

@app.route("/api/campos")
@login_required
def api_campos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM campos WHERE activo=1 ORDER BY fecha_scraping DESC").fetchall()
    return jsonify({"campos": [dict(r) for r in rows], "total": len(rows)})

@app.route("/api/estadisticas")
@login_required
def api_stats():
    conn = get_db()
    stats = {}
    stats["total"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1").fetchone()[0]
    stats["dueno_vende"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1 AND dueno_vende=1").fetchone()[0]
    stats["captados"] = conn.execute("SELECT COUNT(*) FROM campos WHERE activo=1 AND captado=1").fetchone()[0]
    return jsonify(stats)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
