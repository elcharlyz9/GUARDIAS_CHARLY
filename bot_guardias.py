#!/usr/bin/env python3
import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuración
TOKEN = os.environ.get('TELEGRAM_TOKEN')
PORT = int(os.environ.get('PORT', 8080))

# Verificar token
if not TOKEN:
    print("ERROR: Variable TELEGRAM_TOKEN no configurada")
    exit(1)

# Configurar logging simple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base de datos simple en memoria
guardias = {}

# Funciones básicas
def agregar_guardia_db(nombre, fecha):
    if fecha not in guardias:
        guardias[fecha] = []
    guardias[fecha].append(nombre)

def obtener_guardias_db():
    if not guardias:
        return "No hay guardias registradas"
    
    resultado = "📅 GUARDIAS REGISTRADAS:\n\n"
    for fecha in sorted(guardias.keys()):
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            dia = fecha_obj.strftime("%d/%m/%Y (%A)")
            personas = ", ".join(guardias[fecha])
            resultado += f"📆 {dia}\n👥 {personas}\n\n"
        except:
            resultado += f"📆 {fecha}\n👥 {', '.join(guardias[fecha])}\n\n"
    
    return resultado

# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
🚨 Bot de Guardias Activo 🚨

Comandos disponibles:
/agregar Juan 2024-12-25 - Agregar guardia
/guardias - Ver todas las guardias
/ayuda - Ver esta ayuda

Bot funcionando en Render ✅
    """
    await update.message.reply_text(mensaje)
    logger.info("Comando /start ejecutado")

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Uso: /agregar NOMBRE YYYY-MM-DD\nEjemplo: /agregar Juan 2024-12-25")
            return
        
        nombre = context.args[0]
        fecha = context.args[1]
        
        # Validar formato de fecha
        datetime.strptime(fecha, "%Y-%m-%d")
        
        # Agregar a base de datos
        agregar_guardia_db(nombre, fecha)
        
        await update.message.reply_text(f"✅ Guardia agregada:\n👤 {nombre}\n📅 {fecha}")
        logger.info(f"Guardia agregada: {nombre} - {fecha}")
        
    except ValueError:
        await update.message.reply_text("❌ Fecha inválida. Usar formato: YYYY-MM-DD")
    except Exception as e:
        await update.message.reply_text("❌ Error al agregar guardia")
        logger.error(f"Error en agregar: {e}")

async def ver_guardias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        mensaje = obtener_guardias_db()
        await update.message.reply_text(mensaje)
        logger.info("Guardias mostradas")
    except Exception as e:
        await update.message.reply_text("❌ Error al mostrar guardias")
        logger.error(f"Error en guardias: {e}")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
📋 AYUDA DEL BOT:

/agregar Juan 2024-12-25
Agregar guardia para Juan el 25 de diciembre

/guardias 
Ver todas las guardias registradas

/start
Mensaje de inicio

Formato de fecha: YYYY-MM-DD
Ejemplo: 2024-12-25
    """
    await update.message.reply_text(mensaje)

# Servidor web simple para Render
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot funcionando OK')
    
    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP

def servidor_web():
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
        print(f"Servidor web en puerto {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"Error servidor: {e}")

def main():
    # Iniciar servidor web
    web_thread = threading.Thread(target=servidor_web, daemon=True)
    web_thread.start()
    
    # Crear bot
    app = Application.builder().token(TOKEN).build()
    
    # Agregar comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("guardias", ver_guardias))
    app.add_handler(CommandHandler("ayuda", ayuda))
    
    # Iniciar bot
    print("🤖 Bot iniciado en Render")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()