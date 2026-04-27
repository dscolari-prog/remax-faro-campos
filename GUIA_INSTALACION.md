# RE/MAX FARO — Campo Track
## Guía completa de instalación paso a paso

---

## OPCIÓN A — Railway.app (RECOMENDADA · USD 5/mes)

### PASO 1 — Crear cuenta en Railway
1. Ir a https://railway.app
2. Hacer clic en "Start a New Project"
3. Registrarse con cuenta de Google o GitHub (gratuito)

### PASO 2 — Subir el proyecto
1. Ir a https://github.com y crear cuenta gratuita
2. Crear nuevo repositorio: "remax-faro-campos"
3. Subir todos los archivos de esta carpeta al repositorio

   **Forma fácil (sin código):**
   - En GitHub, hacer clic en "Add file" → "Upload files"
   - Arrastrar todos los archivos de la carpeta
   - Hacer clic en "Commit changes"

### PASO 3 — Conectar Railway con GitHub
1. En Railway, hacer clic en "New Project"
2. Seleccionar "Deploy from GitHub repo"
3. Conectar tu cuenta de GitHub
4. Seleccionar el repositorio "remax-faro-campos"
5. Railway detecta automáticamente que es Python y lo configura

### PASO 4 — Configurar variables de entorno
En Railway, ir a tu proyecto → Settings → Variables y agregar:
```
SECRET_KEY = RemaxFaro2025SecretKey_CambiameXFavor
FLASK_ENV = production
```

### PASO 5 — Agregar dominio
1. En Railway → Settings → Domains
2. Hacer clic en "Generate Domain"
3. Obtendrás una URL como: https://remax-faro-campos.up.railway.app

### PASO 6 — Setup inicial de usuarios
1. En Railway, ir a tu servicio → Deploy
2. Hacer clic en "New Service" → "Command"
3. Ejecutar: `python setup_inicial.py`
4. Esto crea todos los usuarios con sus contraseñas

### PASO 7 — Ingresar a la plataforma
1. Ir a tu URL de Railway
2. Usar las credenciales creadas:
   - Admin: diego@remaxfaro.com / RemaxFaro2025!
   - ⚠️ CAMBIAR LA CONTRASEÑA INMEDIATAMENTE desde el panel

---

## OPCIÓN B — Render.com (GRATUITA con límites)

### PASO 1 — Crear cuenta
1. Ir a https://render.com
2. Registrarse con Google o GitHub

### PASO 2 — Subir a GitHub
(igual que Opción A, Paso 2)

### PASO 3 — Crear Web Service
1. En Render, hacer clic en "New +" → "Web Service"
2. Conectar repositorio de GitHub
3. Configurar:
   - Name: remax-faro-campos
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app_web.py`

### PASO 4 — Variables de entorno
En Render → Environment:
```
SECRET_KEY = RemaxFaro2025SecretKey_CambiameXFavor
```

### PASO 5 — Deploy
Hacer clic en "Create Web Service".
Render instala todo automáticamente (~3 minutos).

### PASO 6 — Setup usuarios
En Render → Shell:
```bash
python setup_inicial.py
```

---

## PASO A PASO — GESTIÓN DE USUARIOS

### Crear nuevo usuario (desde el panel web)
1. Ingresar como Admin
2. Ir a la sección "Usuarios"
3. Hacer clic en "Nuevo usuario"
4. Completar: Nombre, Apellido, Email, Contraseña, Rol
5. Guardar

### Roles disponibles:
- **admin** → acceso total, puede crear/borrar usuarios
- **gestor** → puede ver campos, registrar acciones CRM, NO puede crear usuarios

### Cambiar contraseña
1. Ingresar como Admin
2. Ir a "Usuarios" → Editar usuario
3. Ingresar nueva contraseña → Guardar

### Desactivar usuario (cuando un gestor deja RE/MAX FARO)
1. Admin → Usuarios → Editar
2. Cambiar estado a "Inactivo"
3. El gestor pierde acceso inmediatamente

---

## SCRAPER — ACTIVACIÓN DEL SCRAPING DIARIO

### El scraper se ejecuta automáticamente a las 07:00 hs.

Para agregarlo como segundo servicio en Railway:
1. En Railway → tu proyecto → "New Service"
2. Seleccionar "Worker"
3. Start Command: `python scraper_campos.py`

### Agregar alertas por email (opcional):
En `scraper_campos.py`, cambiar:
```python
"email_alerts": True,
"email_from": "tumail@gmail.com",
"email_to": "diego@remaxfaro.com",
"email_pass": "TU_APP_PASSWORD_GMAIL",
```

Para obtener App Password de Gmail:
1. Ir a https://myaccount.google.com/security
2. Activar verificación en 2 pasos
3. Buscar "Contraseñas de aplicación"
4. Crear nueva → copiar el código de 16 caracteres

---

## USUARIOS INICIALES CREADOS

| Nombre | Email | Contraseña temporal | Rol |
|--------|-------|--------------------|----|
| Diego Admin | diego@remaxfaro.com | RemaxFaro2025! | admin |
| Gestor Uno | gestor1@remaxfaro.com | Gestor1_2025! | gestor |
| Gestor Dos | gestor2@remaxfaro.com | Gestor2_2025! | gestor |
| Gestor Tres | gestor3@remaxfaro.com | Gestor3_2025! | gestor |

⚠️ **CAMBIAR TODAS LAS CONTRASEÑAS DESPUÉS DEL PRIMER ACCESO**

---

## SOPORTE

Si algo no funciona, traéme el mensaje de error exacto y lo resuelvo.
— Campo Track | RE/MAX FARO | Santa Fe, Argentina
