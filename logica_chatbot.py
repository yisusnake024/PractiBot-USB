import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import google.generativeai as genai

# ==========================================
# 1. CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ==========================================
TOKEN = os.environ.get('TELEGRAM_TOKEN', 'TU_TOKEN_AQUI')
URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://practibot-usb.onrender.com/')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', 'TU_API_KEY_DE_GEMINI_AQUI')

# Inicialización de Bot y Servidor
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Configuración de Gemini
if GEMINI_KEY and GEMINI_KEY != 'TU_API_KEY_DE_GEMINI_AQUI':
    genai.configure(api_key=GEMINI_KEY)
    modelo_gemini = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 2. BASE DE DATOS SIMULADA (PROTOTIPO)
# ==========================================
CAREER_DATA = {
    "sistemas": {
        "nombre": "Ing. de Sistemas 💻",
        "oferta_titulo": "Desarrollador Frontend",
        "empresa": "Tech Innovación",
        "match": "💡 <b>80% compatibilidad.</b> Piden Tailwind CSS. ¿Ver cápsula?",
        "pregunta": "¿Cómo estructurarías el backend de una app escalable usando Supabase?"
    },
    "psicologia": {
        "nombre": "Psicología 🧠",
        "oferta_titulo": "Práctica Organizacional",
        "empresa": "Clínica San José",
        "match": "💡 <b>80% compatibilidad.</b> Piden pruebas Wartegg. ¿Ver repaso?",
        "pregunta": "¿Qué metodología usarías para medir el clima laboral en un equipo de 50 personas?"
    },
    "admon": {
        "nombre": "Admon. de Empresas 📊",
        "oferta_titulo": "Analista de Proyectos Jr.",
        "empresa": "Grupo Norte",
        "match": "💡 <b>80% compatibilidad.</b> Exigen Power BI. ¿Ver micro-tutorial?",
        "pregunta": "Menciona 3 KPIs que usarías para evaluar la rentabilidad de un proyecto."
    },
    "derecho": {
        "nombre": "Derecho ⚖️",
        "oferta_titulo": "Asistente Jurídico",
        "empresa": "Firma Legal Consultores",
        "match": "💡 <b>80% compatibilidad.</b> Piden actualización laboral. ¿Leer resumen?",
        "pregunta": "¿Cuáles son los pasos para radicar una acción de tutela por vulneración al derecho de petición?"
    }
}

# ==========================================
# 3. FUNCIONES DE NAVEGACIÓN Y TECLADOS
# ==========================================
def botones_retorno(carrera_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔙 Volver al Menú", callback_data=f"menu_{carrera_id}"))
    markup.row(InlineKeyboardButton("🔄 Cambiar Carrera", callback_data="inicio"))
    return markup

def teclado_carreras():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Ing. de Sistemas 💻", callback_data="menu_sistemas"), 
               InlineKeyboardButton("Psicología 🧠", callback_data="menu_psicologia"))
    markup.row(InlineKeyboardButton("Admon. de Empresas 📊", callback_data="menu_admon"), 
               InlineKeyboardButton("Derecho ⚖️", callback_data="menu_derecho"))
    return markup

def generar_onboarding():
    return "¡Hola! Soy <b>PractiBot USB</b> 🤖\nTu asistente de empleabilidad. Para enviarte ofertas y tips personalizados, ¿de qué programa académico eres?"

# ==========================================
# 4. FLUJOS PRINCIPALES DEL BOT
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, generar_onboarding(), reply_markup=teclado_carreras(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'inicio')
def reset_inicio(call):
    bot.edit_message_text(generar_onboarding(), call.message.chat.id, call.message.message_id, reply_markup=teclado_carreras(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def menu_principal(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏢 Ofertas", callback_data=f"oferta_{carrera_id}"), 
               InlineKeyboardButton("📄 Mi CV", callback_data=f"cv_{carrera_id}"))
    markup.row(InlineKeyboardButton("🎤 Entrevista IA", callback_data=f"entrevista_{carrera_id}"), 
               InlineKeyboardButton("📑 Trámites", callback_data=f"tramites_{carrera_id}"))
    markup.row(InlineKeyboardButton("🔄 Cambiar Carrera", callback_data="inicio"))
    
    texto = f"¡Perfecto! Perfil configurado para <b>{data['nombre']}</b>.\n\n¿Qué necesitas hoy?"
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('oferta_'))
def ver_oferta(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    texto = f"📢 <b>NUEVA VACANTE</b>\n\n<b>Cargo:</b> {data['oferta_titulo']}\n<b>Empresa:</b> {data['empresa']}\n\n{data['match']}"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✅ Postularme", callback_data=f"menu_{carrera_id}"),
               InlineKeyboardButton("🎬 Ver Cápsula", callback_data=f"menu_{carrera_id}"))
    markup.add(InlineKeyboardButton("🔙 Volver al Menú", callback_data=f"menu_{carrera_id}"))
    
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('cv_'))
def generar_cv(call):
    carrera_id = call.data.split('_')[1]
    texto = "¡Tu hoja de vida está lista! 📄\n\nHay 3 empresas aliadas de tu facultad buscando practicantes. ¿Autorizas compartir tu CV directamente con sus equipos de selección?"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🚀 Sí, enviar a empresas", callback_data=f"enviado_{carrera_id}"))
    markup.row(InlineKeyboardButton("⬇️ Solo descargar", callback_data=f"menu_{carrera_id}"))
    
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('enviado_'))
def confirmacion_cv(call):
    carrera_id = call.data.split('_')[1]
    texto = "✅ <b>¡Excelente!</b>\nTu perfil ha sido enviado exitosamente a nuestras empresas aliadas. Te notificaremos por aquí apenas revisen tu solicitud."
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=botones_retorno(carrera_id), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('tramites_'))
def tramites(call):
    carrera_id = call.data.split('_')[1]
    texto = "📑 <b>Trámites Automáticos</b>\n¿Qué documento necesitas generar para la universidad?"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Carta Presentación", callback_data=f"menu_{carrera_id}"), 
               InlineKeyboardButton("Certificado Notas", callback_data=f"menu_{carrera_id}"))
    markup.row(InlineKeyboardButton("Convenio Práctica", callback_data=f"menu_{carrera_id}"))
    markup.add(InlineKeyboardButton("🔙 Volver al Menú", callback_data=f"menu_{carrera_id}"))
    
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

# ==========================================
# 5. INTEGRACIÓN CON GEMINI (SIMULADOR)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('entrevista_'))
def simular_entrevista(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    texto = f"🎙️ <b>Simulador de Entrevistas con IA</b>\n\nPregunta técnica:\n<i>\"{data['pregunta']}\"</i>\n\n<b>Escribe tu respuesta aquí mismo</b> para que nuestro sistema la evalúe:"
    
    msg = bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    # Le decimos al bot que espere el texto del usuario y lo envíe a procesar
    bot.register_next_step_handler(msg, procesar_respuesta_entrevista, carrera_id)

def procesar_respuesta_entrevista(message, carrera_id):
    respuesta_usuario = message.text
    
    # Mensaje temporal de espera
    msg_espera = bot.send_message(message.chat.id, "⏳ <i>Analizando tu respuesta con IA...</i>", parse_mode='HTML')
    
    try:
        # Prompt que condiciona la personalidad de Gemini
        prompt_sistema = f"""
        Eres un reclutador senior evaluando a un estudiante universitario de la carrera de {CAREER_DATA[carrera_id]['nombre']}.
        Le hiciste la siguiente pregunta técnica: "{CAREER_DATA[carrera_id]['pregunta']}"
        El estudiante respondió lo siguiente: "{respuesta_usuario}"
        
        Evalúa su respuesta. Dame una retroalimentación de máximo 3 párrafos cortos (con un tono profesional, constructivo y motivador).
        Dile qué hizo bien y qué aspecto técnico o teórico puede mejorar. Usa algunos emojis sutiles.
        """
        
        # Llamada a Gemini
        respuesta_ia = modelo_gemini.generate_content(prompt_sistema)
        feedback = respuesta_ia.text
        
    except Exception as e:
        feedback = "⚠️ Hubo un error al conectar con la Inteligencia Artificial. Asegúrate de que las API Keys estén bien configuradas en el servidor."
    
    # Actualiza el mensaje de carga con la respuesta de la IA y muestra los botones de retorno
    bot.edit_message_text(feedback, message.chat.id, msg_espera.message_id, reply_markup=botones_retorno(carrera_id), parse_mode='HTML')

# ==========================================
# 6. CONFIGURACIÓN DEL SERVIDOR FLASK (WEBHOOK)
# ==========================================
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Vinculamos el bot con la URL asignada por Render
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    return "🚀 Servidor activo. Webhook configurado correctamente.", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
