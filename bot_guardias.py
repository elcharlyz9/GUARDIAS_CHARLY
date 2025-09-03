import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuración
TOKEN = os.environ.get('TELEGRAM_TOKEN', '8229142878:AAFlWgfCg3RiMfVmDS9LiOnBsNv31jhjejU')
PORT = int(os.environ.get('PORT', 8080))
DATA_FILE = "guardias.json"

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class GuardiasManager:
    def __init__(self):
        self.guardias = self.cargar_guardias()
    
    def cargar_guardias(self):
        """Cargar guardias desde archivo JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def guardar_guardias(self):
        """Guardar guardias en archivo JSON"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.guardias, f, ensure_ascii=False, indent=2)
    
    def agregar_guardia(self, persona, fecha_inicio, semanas=1):
        """Agregar una guardia semanal"""
        fecha = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        
        for i in range(semanas):
            fecha_semana = fecha + timedelta(weeks=i)
            fecha_fin = fecha_semana + timedelta(days=6)
            
            semana_key = fecha_semana.strftime("%Y-W%U")
            
            if semana_key not in self.guardias:
                self.guardias[semana_key] = []
            
            self.guardias[semana_key].append({
                "persona": persona,
                "fecha_inicio": fecha_semana.strftime("%Y-%m-%d"),
                "fecha_fin": fecha_fin.strftime("%Y-%m-%d")
            })
        
        self.guardar_guardias()
    
    def obtener_guardias_mes(self, año, mes):
        """Obtener guardias de un mes específico"""
        guardias_mes = {}
        
        for semana_key, guardias in self.guardias.items():
            for guardia in guardias:
                fecha_inicio = datetime.strptime(guardia["fecha_inicio"], "%Y-%m-%d")
                if fecha_inicio.year == año and fecha_inicio.month == mes:
                    if semana_key not in guardias_mes:
                        guardias_mes[semana_key] = []
                    guardias_mes[semana_key].append(guardia)
        
        return guardias_mes
    
    def crear_texto_guardias(self, año, mes):
        """Crear texto formateado con las guardias del mes"""
        guardias_mes = self.obtener_guardias_mes(año, mes)
        
        nombre_mes = datetime(año, mes, 1).strftime("%B %Y").title()
        
        texto = f"📅 **GUARDIAS DE {nombre_mes.upper()}**\n"
        texto += "━" * 35 + "\n\n"
        
        if not guardias_mes:
            texto += "❌ No hay guardias programadas para este mes"
            return texto
        
        for semana_key in sorted(guardias_mes.keys()):
            guardias = guardias_mes[semana_key]
            for guardia in guardias:
                fecha_inicio = datetime.strptime(guardia["fecha_inicio"], "%Y-%m-%d")
                fecha_fin = datetime.strptime(guardia["fecha_fin"], "%Y-%m-%d")
                
                num_semana = fecha_inicio.strftime("%U")
                
                texto += f"🔸 **Semana {num_semana}**\n"
                texto += f"👤 **Persona:** {guardia['persona']}\n"
                texto += f"📆 **Inicio:** {fecha_inicio.strftime('%d/%m/%Y (%A)')}\n"
                texto += f"📆 **Fin:** {fecha_fin.strftime('%d/%m/%Y (%A)')}\n"
                texto += "─" * 25 + "\n\n"
        
        return texto

# Instancia del manager
guardias_manager = GuardiasManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    mensaje = """
🚨 **Bot de Guardias Semanales** 🚨

**Comandos disponibles:**
• `/guardias` - Ver guardias del mes actual
• `/guardias YYYY MM` - Ver guardias de un mes específico
• `/agregar_guardia PERSONA YYYY-MM-DD [SEMANAS]` - Agregar guardia
• `/ayuda` - Ver esta ayuda

**Ejemplo:** `/agregar_guardia Juan 2024-01-15 2`
    """
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda"""
    mensaje = """
📋 **Ayuda - Bot de Guardias**

**Comandos disponibles:**

🔍 `/guardias` 
Ver guardias del mes actual

🔍 `/guardias 2024 03`
Ver guardias de marzo 2024

➕ `/agregar_guardia Juan 2024-01-15`
Agregar una guardia semanal para Juan desde el 15/01/2024

➕ `/agregar_guardia Maria 2024-02-01 3`
Agregar 3 guardias consecutivas para María desde el 01/02/2024

**Formato de fechas:** YYYY-MM-DD (Año-Mes-Día)
**Las guardias son semanales** (7 días desde la fecha de inicio)
    """
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def ver_guardias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /guardias - Ver guardias del mes"""
    try:
        # Obtener parámetros o usar mes actual
        if context.args and len(context.args) >= 2:
            año = int(context.args[0])
            mes = int(context.args[1])
        else:
            hoy = datetime.now()
            año = hoy.year
            mes = hoy.month
        
        # Validar mes
        if mes < 1 or mes > 12:
            await update.message.reply_text("❌ Mes inválido. Usar números del 1 al 12.")
            return
        
        # Generar texto
        texto = guardias_manager.crear_texto_guardias(año, mes)
        
        # Enviar mensaje
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text("❌ Formato inválido. Usar: `/guardias YYYY MM`", parse_mode='Markdown')
    except Exception as e:
        print(f"Error en ver_guardias: {e}")
        await update.message.reply_text("❌ Error al obtener las guardias.")

async def agregar_guardia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /agregar_guardia - Agregar nueva guardia"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: `/agregar_guardia PERSONA YYYY-MM-DD [SEMANAS]`\n"
                "Ejemplo: `/agregar_guardia Juan 2024-01-15 2`",
                parse_mode='Markdown'
            )
            return
        
        persona = context.args[0]
        fecha_inicio = context.args[1]
        semanas = int(context.args[2]) if len(context.args) > 2 else 1
        
        # Validar fecha
        datetime.strptime(fecha_inicio, "%Y-%m-%d")
        
        # Agregar guardia
        guardias_manager.agregar_guardia(persona, fecha_inicio, semanas)
        
        if semanas == 1:
            mensaje = f"✅ **Guardia agregada:**\n👤 {persona}\n📅 {fecha_inicio}"
        else:
            mensaje = f"✅ **{semanas} guardias agregadas:**\n👤 {persona}\n📅 Desde {fecha_inicio}"
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        
    except ValueError as e:
        if "time data" in str(e):
            await update.message.reply_text("❌ Fecha inválida. Usar formato YYYY-MM-DD")
        else:
            await update.message.reply_text("❌ Número de semanas inválido.")
    except Exception as e:
        print(f"Error en agregar_guardia: {e}")
        await update.message.reply_text("❌ Error al agregar la guardia.")

# Webhook para Render (necesario para el plan gratuito)
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()

def main():
    """Función principal"""
    # Iniciar servidor de salud en un hilo separado
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Crear aplicación del bot
    application = Application.builder().token(TOKEN).build()
    
    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("guardias", ver_guardias))
    application.add_handler(CommandHandler("agregar_guardia", agregar_guardia))
    
    # Iniciar bot
    print("🤖 Bot iniciado en Render. Puerto:", PORT)
    application.run_polling()

if __name__ == '__main__':
    main()