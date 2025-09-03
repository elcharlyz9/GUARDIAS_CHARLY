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

import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Configuración
TOKEN = os.environ.get('TELEGRAM_TOKEN')
PORT = int(os.environ.get('PORT', 8080))

if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN no configurado")
    exit(1)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base de datos en memoria
guardias = {}

def agregar_guardia(nombre, fecha, semanas=1):
    """Agregar guardia(s) a la base de datos"""
    try:
        fecha_inicio = datetime.strptime(fecha, "%Y-%m-%d")
        
        for i in range(semanas):
            fecha_guardia = fecha_inicio + timedelta(weeks=i)
            fecha_fin = fecha_guardia + timedelta(days=6)
            fecha_key = fecha_guardia.strftime("%Y-%m-%d")
            
            if fecha_key not in guardias:
                guardias[fecha_key] = []
            
            guardias[fecha_key].append({
                "nombre": nombre,
                "inicio": fecha_guardia.strftime("%Y-%m-%d"),
                "fin": fecha_fin.strftime("%Y-%m-%d")
            })
        return True
    except ValueError:
        return False

def obtener_guardias_texto(año=None, mes=None):
    """Obtener guardias como texto formateado"""
    if not guardias:
        return "❌ No hay guardias registradas"
    
    # Si no se especifica mes, usar actual
    if not año or not mes:
        hoy = datetime.now()
        año = hoy.year
        mes = hoy.month
    
    # Filtrar guardias del mes
    guardias_mes = []
    for fecha_key, lista_guardias in guardias.items():
        fecha_obj = datetime.strptime(fecha_key, "%Y-%m-%d")
        if fecha_obj.year == año and fecha_obj.month == mes:
            for guardia in lista_guardias:
                guardias_mes.append(guardia)
    
    if not guardias_mes:
        nombre_mes = datetime(año, mes, 1).strftime("%B %Y").title()
        return f"❌ No hay guardias para {nombre_mes}"
    
    # Ordenar por fecha
    guardias_mes.sort(key=lambda x: x['inicio'])
    
    # Crear texto
    nombre_mes = datetime(año, mes, 1).strftime("%B %Y").title()
    texto = f"📅 **GUARDIAS - {nombre_mes.upper()}**\n"
    texto += "━" * 30 + "\n\n"
    
    for guardia in guardias_mes:
        fecha_inicio = datetime.strptime(guardia['inicio'], "%Y-%m-%d")
        fecha_fin = datetime.strptime(guardia['fin'], "%Y-%m-%d")
        
        texto += f"👤 **{guardia['nombre']}**\n"
        texto += f"📅 {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}\n"
        texto += f"📝 {fecha_inicio.strftime('%A')} a {fecha_fin.strftime('%A')}\n"
        texto += "─" * 25 + "\n\n"
    
    return texto

# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
🚨 **Bot de Guardias Semanales** 🚨

**Comandos:**
• `/agregar Juan 2024-12-25` - Agregar guardia
• `/agregar Maria 2024-12-25 2` - Agregar 2 guardias
• `/guardias` - Ver guardias del mes actual
• `/guardias 2024 12` - Ver guardias de dic 2024
• `/ayuda` - Ver ayuda completa

✅ **Bot funcionando en Render**
    """
    await update.message.reply_text(mensaje, parse_mode='Markdown')
    logger.info(f"Start ejecutado por {update.effective_user.first_name}")

async def cmd_agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **Uso:** `/agregar NOMBRE YYYY-MM-DD [SEMANAS]`\n"
                "**Ejemplos:**\n"
                "• `/agregar Juan 2024-12-25`\n"
                "• `/agregar Maria 2024-12-25 3`",
                parse_mode='Markdown'
            )
            return
        
        nombre = context.args[0]
        fecha = context.args[1]
        semanas = int(context.args[2]) if len(context.args) > 2 else 1
        
        if agregar_guardia(nombre, fecha, semanas):
            if semanas == 1:
                mensaje = f"✅ **Guardia agregada:**\n👤 {nombre}\n📅 {fecha}"
            else:
                mensaje = f"✅ **{semanas} guardias agregadas:**\n👤 {nombre}\n📅 Desde {fecha}"
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            logger.info(f"Guardia agregada: {nombre} - {fecha}")
        else:
            await update.message.reply_text("❌ Fecha inválida. Usar formato: YYYY-MM-DD")
    
    except ValueError:
        await update.message.reply_text("❌ Número de semanas inválido")
    except Exception as e:
        logger.error(f"Error en agregar: {e}")
        await update.message.reply_text("❌ Error al agregar guardia")

async def cmd_guardias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) >= 2:
            año = int(context.args[0])
            mes = int(context.args[1])
        else:
            hoy = datetime.now()
            año = hoy.year
            mes = hoy.month
        
        if mes < 1 or mes > 12:
            await update.message.reply_text("❌ Mes inválido (1-12)")
            return
        
        texto = obtener_guardias_texto(año, mes)
        await update.message.reply_text(texto, parse_mode='Markdown')
        logger.info(f"Guardias mostradas: {año}-{mes}")
    
    except ValueError:
        await update.message.reply_text("❌ Formato: `/guardias 2024 12`", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en guardias: {e}")
        await update.message.reply_text("❌ Error al mostrar guardias")

async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """
📋 **AYUDA - Bot de Guardias**

**📝 Agregar Guardias:**
• `/agregar Juan 2024-12-25`
  Guardia de una semana para Juan

• `/agregar Maria 2024-12-25 3`
  3 guardias consecutivas para María

**📅 Ver Guardias:**
• `/guardias`
  Guardias del mes actual

• `/guardias 2024 12`
  Guardias de diciembre 2024

**ℹ️ Información:**
• Cada guardia dura 7 días
• Formato fecha: YYYY-MM-DD
• Bot activo 24/7 en Render
    """
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# Servidor HTTP para Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot de Guardias funcionando correctamente!')
    
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    logger.info(f"Servidor HTTP iniciado en puerto {PORT}")
    server.serve_forever()

def main():
    # Servidor HTTP en hilo separado
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Crear aplicación
    app = Application.builder().token(TOKEN).build()
    
    # Agregar comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agregar", cmd_agregar))
    app.add_handler(CommandHandler("guardias", cmd_guardias))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    
    # Iniciar bot
    logger.info("🤖 Bot de Guardias iniciado correctamente")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()