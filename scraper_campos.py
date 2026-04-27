#!/usr/bin/env python3
# =============================================================================
# RE/MAX FARO — Campo Track | Scraper Completo
# Santa Fe, Argentina
# Autor: Campo Track System
# Actualización: Diaria automática 07:00 hs
# =============================================================================

import requests
import schedule
import time
import json
import sqlite3
import re
import smtplib
import logging
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode, quote
import urllib3
urllib3.disable_warnings()

# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================
CONFIG = {
    "db_path": "campos_remax.db",
    "log_path": "scraper.log",
    "json_export": "campos_data.json",
    "schedule_time": "07:00",
    "email_alerts": False,       # Cambiar a True y configurar datos abajo
    "email_from": "tumail@gmail.com",
    "email_to": "diego@remaxfaro.com",
    "email_pass": "TU_APP_PASSWORD_GMAIL",
    "geocode_api": "",           # API key de OpenCage o Google Maps (opcional)
    "delay_between_requests": 2, # segundos entre requests (ser amigable con los servidores)
    "max_pages_per_source": 10,  # páginas máximas por fuente
}

# Headers para simular navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# =============================================================================
# FUENTES — 35+ PORTALES INMOBILIARIOS RURALES
# =============================================================================
FUENTES = [
    # ---- PORTALES NACIONALES GENERALES ----
    {
        "nombre": "Argenprop",
        "url_base": "https://www.argenprop.com",
        "url_busqueda": "https://www.argenprop.com/campo--venta--santa-fe?pagina={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "Zonaprop",
        "url_base": "https://www.zonaprop.com.ar",
        "url_busqueda": "https://www.zonaprop.com.ar/campos-venta-santa-fe-pagina-{page}.html",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "MercadoLibre Rural",
        "url_base": "https://www.mercadolibre.com.ar",
        "url_busqueda": "https://listado.mercadolibre.com.ar/inmuebles/campos/santa-fe/_Desde_{offset}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "Properati",
        "url_base": "https://www.properati.com.ar",
        "url_busqueda": "https://www.properati.com.ar/s/santa-fe/campo/venta?page={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "InmoBuscador",
        "url_base": "https://www.inmobuscador.com.ar",
        "url_busqueda": "https://www.inmobuscador.com.ar/campos/venta/santa-fe/{page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "Clasificados La Nacion",
        "url_base": "https://clasificados.lanacion.com.ar",
        "url_busqueda": "https://clasificados.lanacion.com.ar/inmuebles/campos/venta/santa-fe?pagina={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "OLX Argentina",
        "url_base": "https://www.olx.com.ar",
        "url_busqueda": "https://www.olx.com.ar/santa-fe_g2000503/q-campo-rural?page={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },

    # ---- PORTALES ESPECIALIZADOS RURALES ----
    {
        "nombre": "Rurales.com.ar",
        "url_base": "https://www.rurales.com.ar",
        "url_busqueda": "https://www.rurales.com.ar/campos/venta/santa-fe/?p={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "CampoArgentino",
        "url_base": "https://www.campoargentino.com",
        "url_busqueda": "https://www.campoargentino.com/propiedades/santa-fe/campo/venta/pagina/{page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "InfoCampo",
        "url_base": "https://www.infocampo.com.ar",
        "url_busqueda": "https://www.infocampo.com.ar/clasificados/inmuebles/santa-fe/?page={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "Agrofy",
        "url_base": "https://www.agrofy.com.ar",
        "url_busqueda": "https://www.agrofy.com.ar/s/inmuebles-rurales/santa-fe?page={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "AgroFit",
        "url_base": "https://www.agrofit.com.ar",
        "url_busqueda": "https://www.agrofit.com.ar/clasificados/campos/santa-fe/?pagina={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "Mercofield",
        "url_base": "https://www.mercofield.com.ar",
        "url_busqueda": "https://www.mercofield.com.ar/propiedades/santa-fe/campo?page={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "Dircampo",
        "url_base": "https://www.dircampo.com.ar",
        "url_busqueda": "https://www.dircampo.com.ar/campos-en-venta/santa-fe/{page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "Remate Ganadero",
        "url_base": "https://www.remateganadero.com.ar",
        "url_busqueda": "https://www.remateganadero.com.ar/inmuebles/santa-fe/?p={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "Campo Online",
        "url_base": "https://www.campoonline.com.ar",
        "url_busqueda": "https://www.campoonline.com.ar/buscar/?provincia=santa-fe&tipo=campo&operacion=venta&pagina={page}",
        "tipo": "portal_rural",
        "activo": True,
    },
    {
        "nombre": "Mercado Unico",
        "url_base": "https://www.mercadounico.com",
        "url_busqueda": "https://www.mercadounico.com/inmuebles/campos/santa-fe/?pagina={page}",
        "tipo": "portal_rural",
        "activo": True,
    },

    # ---- INMOBILIARIAS LOCALES SANTA FE ----
    {
        "nombre": "RE/MAX Santa Fe",
        "url_base": "https://www.remax.com.ar",
        "url_busqueda": "https://www.remax.com.ar/listings/buy?adType=Sell&regionId=AR-SF&propertyType=2&page={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "RAES Inmobiliaria",
        "url_base": "https://www.raes.com.ar",
        "url_busqueda": "https://www.raes.com.ar/propiedades/campo/venta/?pagina={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "APL Inmobiliaria",
        "url_base": "https://www.aplinmobiliaria.com.ar",
        "url_busqueda": "https://www.aplinmobiliaria.com.ar/propiedades/?tipo=campo&operacion=venta&pagina={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Sañudo Campo",
        "url_base": "https://www.sañudocampo.com.ar",
        "url_busqueda": "https://www.sañudocampo.com.ar/propiedades/?pagina={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Tizado Santa Fe",
        "url_base": "https://www.tizado.com.ar",
        "url_busqueda": "https://www.tizado.com.ar/propiedades/santa-fe/campo/venta/?pagina={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "LJ Ramos Rural",
        "url_base": "https://www.ljramos.com.ar",
        "url_busqueda": "https://www.ljramos.com.ar/propiedades/campo/venta/santa-fe/?p={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Bullrich Campos",
        "url_base": "https://www.bullrichcampos.com.ar",
        "url_busqueda": "https://www.bullrichcampos.com.ar/propiedades/?provincia=santa-fe&page={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Toribio Achaval Rural",
        "url_base": "https://www.toribioachavalinmobiliaria.com.ar",
        "url_busqueda": "https://www.toribioachavalinmobiliaria.com.ar/propiedades/campo/santa-fe/?p={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Cushman Rural Argentina",
        "url_base": "https://www.cushmanwakefield.com.ar",
        "url_busqueda": "https://www.cushmanwakefield.com.ar/propiedades/campo/venta/santa-fe/?p={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Neoportal",
        "url_base": "https://www.neoportal.com.ar",
        "url_busqueda": "https://www.neoportal.com.ar/campos/venta/santa-fe/?pagina={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "Encuentra24",
        "url_base": "https://www.encuentra24.com.ar",
        "url_busqueda": "https://www.encuentra24.com.ar/argentina-inmuebles-campos-venta/santa-fe?page={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "Icasas",
        "url_base": "https://www.icasas.com.ar",
        "url_busqueda": "https://www.icasas.com.ar/campos/venta/santa-fe/?pagina={page}",
        "tipo": "portal_nacional",
        "activo": True,
    },
    {
        "nombre": "Rodo Inmuebles",
        "url_base": "https://www.rodoinmuebles.com.ar",
        "url_busqueda": "https://www.rodoinmuebles.com.ar/propiedades/campo/venta/santa-fe/?p={page}",
        "tipo": "inmobiliaria",
        "activo": True,
    },
    {
        "nombre": "Diario El Litoral Clasificados",
        "url_base": "https://clasificados.ellitoral.com",
        "url_busqueda": "https://clasificados.ellitoral.com/inmuebles/campos/?pagina={page}",
        "tipo": "diario_local",
        "activo": True,
    },
    {
        "nombre": "Diario La Capital Clasificados",
        "url_base": "https://clasificados.lacapital.com.ar",
        "url_busqueda": "https://clasificados.lacapital.com.ar/inmuebles/campo/venta/?p={page}",
        "tipo": "diario_local",
        "activo": True,
    },
    {
        "nombre": "Facebook Marketplace Rural SF",
        "url_base": "https://www.facebook.com",
        "url_busqueda": "https://www.facebook.com/marketplace/santafe/propertyrentals?propertyType=land",
        "tipo": "red_social",
        "activo": False,  # Requiere login manual - se agrega vía carga manual
    },
    {
        "nombre": "Carga Manual",
        "url_base": None,
        "url_busqueda": None,
        "tipo": "manual",
        "activo": True,
    },
]

# =============================================================================
# BASE DE DATOS
# =============================================================================
def init_db():
    """Inicializa la base de datos con todas las tablas necesarias."""
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()

    # Tabla principal de campos
    c.execute("""
        CREATE TABLE IF NOT EXISTS campos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_id         TEXT UNIQUE,
            titulo          TEXT NOT NULL,
            descripcion     TEXT,
            tipo            TEXT,
            hectareas       REAL,
            precio_usd      REAL,
            precio_ars      REAL,
            precio_ha_usd   REAL,
            zona            TEXT,
            localidad       TEXT,
            provincia       TEXT DEFAULT 'Santa Fe',
            partido         TEXT,
            fuente          TEXT,
            url_original    TEXT,
            lat             REAL,
            lng             REAL,
            geolocalizdo    INTEGER DEFAULT 0,
            dueno_vende     INTEGER DEFAULT 0,
            captado         INTEGER DEFAULT 0,
            activo          INTEGER DEFAULT 1,
            tiene_agua      INTEGER DEFAULT 0,
            tiene_luz       INTEGER DEFAULT 0,
            tiene_gas       INTEGER DEFAULT 0,
            tiene_casa      INTEGER DEFAULT 0,
            tiene_galpon    INTEGER DEFAULT 0,
            tipo_suelo      TEXT,
            acceso          TEXT,
            fecha_pub       TEXT,
            fecha_scraping  TEXT,
            fecha_captacion TEXT,
            gestor_id       INTEGER,
            notas           TEXT
        )
    """)

    # Tabla de usuarios del sistema
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            apellido    TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            rol         TEXT DEFAULT 'gestor',
            activo      INTEGER DEFAULT 1,
            fecha_alta  TEXT,
            ultimo_acceso TEXT
        )
    """)

    # Tabla CRM — seguimiento de captación
    c.execute("""
        CREATE TABLE IF NOT EXISTS crm_acciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            campo_id    INTEGER,
            usuario_id  INTEGER,
            tipo_accion TEXT,
            descripcion TEXT,
            resultado   TEXT,
            proxima_accion TEXT,
            fecha       TEXT,
            FOREIGN KEY(campo_id)   REFERENCES campos(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)

    # Tabla de fuentes scrapeadas
    c.execute("""
        CREATE TABLE IF NOT EXISTS fuentes_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fuente          TEXT,
            fecha_scraping  TEXT,
            campos_nuevos   INTEGER DEFAULT 0,
            campos_total    INTEGER DEFAULT 0,
            estado          TEXT,
            error_msg       TEXT
        )
    """)

    # Tabla matcheos comprador-campo
    c.execute("""
        CREATE TABLE IF NOT EXISTS matcheos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            campo_id    INTEGER,
            comprador   TEXT,
            contacto    TEXT,
            ha_buscadas TEXT,
            tipo_buscado TEXT,
            zona_buscada TEXT,
            presupuesto_usd REAL,
            fecha       TEXT,
            estado      TEXT DEFAULT 'activo'
        )
    """)

    conn.commit()
    return conn


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def generar_hash(titulo, fuente, url):
    """Genera ID único para evitar duplicados."""
    raw = f"{titulo}|{fuente}|{url}"
    return hashlib.md5(raw.encode()).hexdigest()

def detectar_dueno_vende(texto):
    """Detecta si el campo lo vende directamente el dueño."""
    keywords = [
        "dueño vende", "dueño directo", "vendo directo", "particular vende",
        "sin intermediarios", "propietario vende", "trato directo",
        "owner", "venta directa", "dueño", "sin comision"
    ]
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in keywords)

def extraer_hectareas(texto):
    """Extrae hectáreas del texto."""
    patterns = [
        r'(\d+[\.,]?\d*)\s*(?:ha|has|hectáreas|hectareas|hectarea)',
        r'(\d+[\.,]?\d*)\s*ha\b',
    ]
    for p in patterns:
        m = re.search(p, texto.lower())
        if m:
            return float(m.group(1).replace(',', '.'))
    return None

def extraer_precio(texto):
    """Extrae precio en USD del texto."""
    patterns = [
        r'u\$s\s*(\d+[\.,]?\d*)',
        r'usd\s*(\d+[\.,]?\d*)',
        r'u\$d\s*(\d+[\.,]?\d*)',
        r'\$\s*(\d+[\.,]?\d*)\s*(?:usd|dólares)',
        r'(\d+[\.,]?\d*)\s*(?:dólares|dolares|usd)',
    ]
    for p in patterns:
        m = re.search(p, texto.lower())
        if m:
            val = float(m.group(1).replace('.', '').replace(',', '.'))
            if val > 1000:  # precio mínimo razonable
                return val
    return None

def geocodificar(localidad, provincia="Santa Fe"):
    """Obtiene coordenadas de una localidad."""
    try:
        query = quote(f"{localidad}, {provincia}, Argentina")
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        r = requests.get(url, headers={"User-Agent": "RemaxFaroCampoTrack/1.0"}, timeout=10)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None

def guardar_campo(conn, datos):
    """Guarda un campo en la DB, evitando duplicados."""
    hash_id = generar_hash(datos.get("titulo",""), datos.get("fuente",""), datos.get("url_original",""))
    c = conn.cursor()
    c.execute("SELECT id FROM campos WHERE hash_id = ?", (hash_id,))
    if c.fetchone():
        return False  # Ya existe

    # Geocodificar si tiene localidad pero no coordenadas
    if datos.get("localidad") and not datos.get("lat"):
        lat, lng = geocodificar(datos["localidad"])
        datos["lat"] = lat
        datos["lng"] = lng
        datos["geolocalizdo"] = 1 if lat else 0

    # Calcular precio por hectárea
    if datos.get("precio_usd") and datos.get("hectareas") and datos["hectareas"] > 0:
        datos["precio_ha_usd"] = round(datos["precio_usd"] / datos["hectareas"], 2)

    datos["hash_id"] = hash_id
    datos["fecha_scraping"] = datetime.now().isoformat()

    cols = [k for k in datos if k in [
        "hash_id","titulo","descripcion","tipo","hectareas","precio_usd",
        "precio_ha_usd","zona","localidad","fuente","url_original","lat","lng",
        "geolocalizdo","dueno_vende","fecha_pub","fecha_scraping","notas","activo"
    ]]
    vals = [datos[k] for k in cols]
    placeholders = ",".join(["?" for _ in cols])
    col_str = ",".join(cols)
    c.execute(f"INSERT INTO campos ({col_str}) VALUES ({placeholders})", vals)
    conn.commit()
    return True


# =============================================================================
# SCRAPERS POR PORTAL
# =============================================================================
def get_soup(url, retries=3):
    """Descarga y parsea una URL con reintentos."""
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")
            time.sleep(CONFIG["delay_between_requests"])
        except Exception as e:
            logging.warning(f"Error en {url}: {e}")
            time.sleep(3)
    return None

def scrape_argenprop(conn):
    nuevos = 0
    for page in range(1, CONFIG["max_pages_per_source"] + 1):
        url = FUENTES[0]["url_busqueda"].format(page=page)
        soup = get_soup(url)
        if not soup:
            break
        cards = soup.find_all("div", class_=re.compile(r"posting-card|listing-item"))
        if not cards:
            break
        for card in cards:
            titulo = card.find(class_=re.compile(r"title|nombre")) 
            titulo = titulo.get_text(strip=True) if titulo else "Campo Santa Fe"
            texto = card.get_text(" ")
            link = card.find("a", href=True)
            url_orig = urljoin(FUENTES[0]["url_base"], link["href"]) if link else url
            datos = {
                "titulo": titulo,
                "fuente": "Argenprop",
                "url_original": url_orig,
                "hectareas": extraer_hectareas(texto),
                "precio_usd": extraer_precio(texto),
                "dueno_vende": 1 if detectar_dueno_vende(texto) else 0,
                "descripcion": texto[:500],
                "activo": 1,
            }
            if guardar_campo(conn, datos):
                nuevos += 1
        time.sleep(CONFIG["delay_between_requests"])
    return nuevos

def scrape_zonaprop(conn):
    nuevos = 0
    for page in range(1, CONFIG["max_pages_per_source"] + 1):
        url = FUENTES[1]["url_busqueda"].format(page=page)
        soup = get_soup(url)
        if not soup:
            break
        cards = soup.find_all(attrs={"data-id": True})
        if not cards:
            # Intento alternativo
            cards = soup.find_all("div", class_=re.compile(r"posting|card-listing"))
        if not cards:
            break
        for card in cards:
            texto = card.get_text(" ")
            titulo_el = card.find(class_=re.compile(r"title|h2|postTitle"))
            titulo = titulo_el.get_text(strip=True) if titulo_el else "Campo Santa Fe"
            link = card.find("a", href=True)
            url_orig = urljoin(FUENTES[1]["url_base"], link["href"]) if link else url
            # Extraer localidad
            loc_el = card.find(class_=re.compile(r"location|address|localidad"))
            localidad = loc_el.get_text(strip=True) if loc_el else ""
            datos = {
                "titulo": titulo,
                "fuente": "Zonaprop",
                "url_original": url_orig,
                "hectareas": extraer_hectareas(texto),
                "precio_usd": extraer_precio(texto),
                "localidad": localidad,
                "dueno_vende": 1 if detectar_dueno_vende(texto) else 0,
                "descripcion": texto[:500],
                "activo": 1,
            }
            if guardar_campo(conn, datos):
                nuevos += 1
        time.sleep(CONFIG["delay_between_requests"])
    return nuevos

def scrape_mercadolibre(conn):
    nuevos = 0
    for offset in range(0, CONFIG["max_pages_per_source"] * 48, 48):
        url = FUENTES[2]["url_busqueda"].format(offset=offset if offset > 0 else 1)
        soup = get_soup(url)
        if not soup:
            break
        items = soup.find_all("li", class_=re.compile(r"results-item|ui-search-result"))
        if not items:
            break
        for item in items:
            texto = item.get_text(" ")
            titulo_el = item.find(class_=re.compile(r"item__title|ui-search-item__title"))
            titulo = titulo_el.get_text(strip=True) if titulo_el else "Campo Santa Fe"
            link = item.find("a", href=True)
            url_orig = link["href"] if link else url
            precio_el = item.find(class_=re.compile(r"price|amount"))
            datos = {
                "titulo": titulo,
                "fuente": "MercadoLibre",
                "url_original": url_orig,
                "hectareas": extraer_hectareas(texto),
                "precio_usd": extraer_precio(texto),
                "dueno_vende": 1 if detectar_dueno_vende(texto) else 0,
                "descripcion": texto[:500],
                "activo": 1,
            }
            if guardar_campo(conn, datos):
                nuevos += 1
        time.sleep(CONFIG["delay_between_requests"])
    return nuevos

def scrape_generico(conn, fuente_config):
    """
    Scraper genérico para portales con estructura HTML estándar.
    Funciona para la mayoría de los portales del listado.
    """
    nombre = fuente_config["nombre"]
    nuevos = 0
    for page in range(1, CONFIG["max_pages_per_source"] + 1):
        url = fuente_config["url_busqueda"].format(page=page, offset=(page-1)*20)
        soup = get_soup(url)
        if not soup:
            break

        # Buscar contenedores de propiedades con selectores comunes
        cards = (
            soup.find_all(class_=re.compile(r"propert|listing|campo|result|card|posting", re.I))
            or soup.find_all("article")
            or soup.find_all("li", class_=re.compile(r"item|result", re.I))
        )
        if not cards or len(cards) < 2:
            break

        for card in cards[:30]:  # máximo 30 por página
            texto = card.get_text(" ", strip=True)
            if len(texto) < 50:
                continue
            if not any(w in texto.lower() for w in ["campo","ha ","hectárea","hectarea","rural","agrícola","ganadero","tambo"]):
                continue

            titulo_el = (card.find(re.compile(r"h1|h2|h3")) or
                        card.find(class_=re.compile(r"title|nombre|heading", re.I)))
            titulo = titulo_el.get_text(strip=True)[:200] if titulo_el else texto[:80]

            link = card.find("a", href=True)
            url_orig = urljoin(fuente_config["url_base"], link["href"]) if link else url

            loc_el = card.find(class_=re.compile(r"location|address|localidad|ciudad", re.I))
            localidad = loc_el.get_text(strip=True)[:100] if loc_el else ""

            datos = {
                "titulo": titulo,
                "fuente": nombre,
                "url_original": url_orig,
                "hectareas": extraer_hectareas(texto),
                "precio_usd": extraer_precio(texto),
                "localidad": localidad,
                "dueno_vende": 1 if detectar_dueno_vende(texto) else 0,
                "descripcion": texto[:500],
                "activo": 1,
            }
            if guardar_campo(conn, datos):
                nuevos += 1
        time.sleep(CONFIG["delay_between_requests"])
    return nuevos


# =============================================================================
# MOTOR PRINCIPAL DE SCRAPING
# =============================================================================
def run_scraping():
    """Ejecuta el scraping completo de todas las fuentes."""
    logging.info("=" * 60)
    logging.info(f"INICIO SCRAPING — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logging.info("=" * 60)

    conn = init_db()
    total_nuevos = 0
    resumen = []

    for fuente in FUENTES:
        if not fuente["activo"] or fuente["url_busqueda"] is None:
            continue

        nombre = fuente["nombre"]
        logging.info(f"Scrapeando: {nombre}")
        nuevos = 0
        estado = "ok"
        error_msg = ""

        try:
            # Scrapers específicos para los principales portales
            if nombre == "Argenprop":
                nuevos = scrape_argenprop(conn)
            elif nombre == "Zonaprop":
                nuevos = scrape_zonaprop(conn)
            elif nombre == "MercadoLibre Rural":
                nuevos = scrape_mercadolibre(conn)
            else:
                # Scraper genérico para el resto
                nuevos = scrape_generico(conn, fuente)

        except Exception as e:
            estado = "error"
            error_msg = str(e)
            logging.error(f"Error en {nombre}: {e}")

        # Registrar en log
        c = conn.cursor()
        c.execute("""
            INSERT INTO fuentes_log (fuente, fecha_scraping, campos_nuevos, estado, error_msg)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, datetime.now().isoformat(), nuevos, estado, error_msg))
        conn.commit()

        total_nuevos += nuevos
        resumen.append(f"  {nombre}: {nuevos} nuevos")
        logging.info(f"  → {nuevos} campos nuevos encontrados")

    # Exportar JSON para la plataforma web
    exportar_json(conn)

    logging.info(f"\nRESUMEN SCRAPING:")
    for linea in resumen:
        logging.info(linea)
    logging.info(f"TOTAL NUEVOS: {total_nuevos}")
    logging.info("=" * 60)

    # Enviar alerta por email si hay campos nuevos
    if total_nuevos > 0 and CONFIG["email_alerts"]:
        enviar_alerta_email(total_nuevos, resumen)

    conn.close()
    return total_nuevos


# =============================================================================
# EXPORTACIÓN JSON
# =============================================================================
def exportar_json(conn):
    """Exporta todos los campos activos a JSON para la plataforma web."""
    c = conn.cursor()
    c.execute("""
        SELECT id, titulo, tipo, hectareas, precio_usd, precio_ha_usd,
               zona, localidad, fuente, url_original, lat, lng,
               geolocalizdo, dueno_vende, captado, descripcion,
               fecha_pub, fecha_scraping
        FROM campos WHERE activo = 1
        ORDER BY fecha_scraping DESC
    """)
    cols = [d[0] for d in c.description]
    rows = [dict(zip(cols, row)) for row in c.fetchall()]
    with open(CONFIG["json_export"], "w", encoding="utf-8") as f:
        json.dump({"campos": rows, "total": len(rows),
                   "actualizado": datetime.now().isoformat()}, f,
                  ensure_ascii=False, indent=2)
    logging.info(f"JSON exportado: {len(rows)} campos → {CONFIG['json_export']}")


# =============================================================================
# ALERTAS EMAIL
# =============================================================================
def enviar_alerta_email(total, resumen):
    """Envía alerta por email cuando hay nuevos campos."""
    try:
        msg = MIMEMultipart()
        msg["From"] = CONFIG["email_from"]
        msg["To"] = CONFIG["email_to"]
        msg["Subject"] = f"RE/MAX FARO — {total} campos nuevos detectados"
        body = f"""
RE/MAX FARO — Campo Track
Alerta de nuevos campos
{datetime.now().strftime('%d/%m/%Y %H:%M')}

Se detectaron {total} campos nuevos:

{chr(10).join(resumen)}

Ingresá a la plataforma para verlos: http://tu-servidor/

--
Campo Track | RE/MAX FARO | Santa Fe
        """
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(CONFIG["email_from"], CONFIG["email_pass"])
            smtp.send_message(msg)
        logging.info("Alerta email enviada.")
    except Exception as e:
        logging.error(f"Error enviando email: {e}")


# =============================================================================
# GESTIÓN DE USUARIOS
# =============================================================================
def crear_usuario(conn, nombre, apellido, email, password, rol="gestor"):
    """Crea un usuario con contraseña hasheada."""
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO usuarios (nombre, apellido, email, password, rol, activo, fecha_alta)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (nombre, apellido, email, pwd_hash, rol, datetime.now().isoformat()))
        conn.commit()
        print(f"✓ Usuario creado: {nombre} {apellido} ({email}) — Rol: {rol}")
        return True
    except sqlite3.IntegrityError:
        print(f"✗ El email {email} ya existe.")
        return False

def listar_usuarios(conn):
    c = conn.cursor()
    c.execute("SELECT id, nombre, apellido, email, rol, activo FROM usuarios")
    print("\n{:<4} {:<20} {:<30} {:<12} {:<8}".format("ID","Nombre","Email","Rol","Activo"))
    print("-" * 80)
    for row in c.fetchall():
        print("{:<4} {:<20} {:<30} {:<12} {:<8}".format(*row))


# =============================================================================
# SETUP INICIAL DE USUARIOS
# =============================================================================
def setup_usuarios_iniciales(conn):
    """Crea los usuarios iniciales del sistema."""
    usuarios = [
        ("Diego", "Admin", "diego@remaxfaro.com", "RemaxFaro2025!", "admin"),
        ("Gestor", "Demo", "gestor@remaxfaro.com", "Gestor2025!", "gestor"),
    ]
    print("\n--- CREANDO USUARIOS INICIALES ---")
    for u in usuarios:
        crear_usuario(conn, *u)


# =============================================================================
# SCHEDULER — EJECUCIÓN AUTOMÁTICA DIARIA
# =============================================================================
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(CONFIG["log_path"]),
            logging.StreamHandler()
        ]
    )

    conn = init_db()
    setup_usuarios_iniciales(conn)

    print("\n" + "=" * 60)
    print("   RE/MAX FARO — Campo Track Scraper")
    print("   Santa Fe, Argentina")
    print("=" * 60)
    print(f"   Scraping diario programado: {CONFIG['schedule_time']} hs")
    print(f"   Base de datos: {CONFIG['db_path']}")
    print(f"   Fuentes activas: {sum(1 for f in FUENTES if f['activo'] and f['url_busqueda'])}")
    print("=" * 60 + "\n")

    # Primera ejecución inmediata
    print("Ejecutando primer scraping...")
    run_scraping()

    # Programar ejecución diaria
    schedule.every().day.at(CONFIG["schedule_time"]).do(run_scraping)
    logging.info(f"Scheduler activo. Próxima ejecución: {CONFIG['schedule_time']} hs")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
