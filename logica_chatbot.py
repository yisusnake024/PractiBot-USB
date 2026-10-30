import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import google.generativeai as genai

# ==========================================
# 1. CREDENCIALES Y CONFIGURACIÓN
# ==========================================
TOKEN = os.environ.get('TELEGRAM_TOKEN', '8172026872:AAHK_FSIIMfSKfwLC6W5rUzx7fqtZF8FOzI')
URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://practibot-usb.onrender.com')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', 'AQ.Ab8RN6LMjC7m8DyZY3I6Nrh0yFJaQPOVeG1yAyryt57GN5peLA')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Configuración de Gemini
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        modelo_gemini = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configurando Gemini: {e}")

# ==========================================
# 2. BASE DE DATOS Y PERFILES
# ==========================================
CAREER_DATA = {
    "sistemas": {
        "nombre": "Ing. de Sistemas 💻",
        "habilidades_estudiante": "Python, React, SQL, Git",
        "oferta_titulo": "Desarrollador Fullstack Jr.",
        "empresa": "Tech Innovación",
        "requisitos_vacante": "Next.js, Tailwind CSS, PostgreSQL",
        "pregunta": "¿Cómo estructurarías el backend de una app escalable usando Supabase?"
    },
    "psicologia": {
        "nombre": "Psicología 🧠",
        "habilidades_estudiante": "Entrevistas, Excel, informes",
        "oferta_titulo": "Práctica Organizacional",
        "empresa": "Clínica San José",
        "requisitos_vacante": "Pruebas psicotécnicas, Wartegg",
        "pregunta": "¿Qué metodología usarías para medir el clima laboral en un equipo de 50 personas?"
    },
    "admon": {
        "nombre": "Admon. de Empresas 📊",
        "habilidades_estudiante": "Gestión, contabilidad, liderazgo",
        "oferta_titulo": "Analista de Proyectos Jr.",
        "empresa": "Grupo Norte",
        "requisitos_vacante": "Power BI, KPIs, Scrum",
        "pregunta": "Menciona 3 KPIs que usarías para evaluar la rentabilidad de un proyecto."
    },
    "derecho": {
        "nombre": "Derecho ⚖️",
        "habilidades_estudiante": "Investigación, derecho civil, redacción",
        "oferta_titulo": "Asistente Jurídico",
        "empresa": "Firma Legal Consultores",
        "requisitos_vacante": "Derecho laboral, tutelas",
        "pregunta": "¿Cuáles son los pasos para radicar una acción de tutela por derecho de petición?"
    }
}

# ==========================================
# 3. NAVEGACIÓN Y MENÚS
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
    return "¡Hola! Soy <b>PractiBot USB</b> 🤖\nTu asistente de empleabilidad con IA. ¿De qué programa académico eres?"

# ==========================================
# 4. MANEJADORES DE TELEGRAM
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        generar_onboarding(), 
        reply_markup=teclado_carreras(), 
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'inicio')
def reset_inicio(call):
    bot.edit_message_text(
        generar_onboarding(), 
        call.message.chat.id, 
        call.message.message_id, 
        reply_markup=teclado_carreras(), 
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def menu_principal(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏢 Ver Ofertas (IA)", callback_data=f"oferta_{carrera_id}"), 
               InlineKeyboardButton("🎬 Cápsulas (IA)", callback_data=f"capsula_{carrera_id}"))
    markup.row(InlineKeyboardButton("🎤 Entrevista (IA)", callback_data=f"entrevista_{carrera_id}"), 
               InlineKeyboardButton("📄 Mi CV", callback_data=f"cv_{carrera_id}"))
    markup.row(InlineKeyboardButton("🔄 Cambiar Carrera", callback_data="inicio"))
    
    texto = f"¡Perfecto! Perfil configurado para <b>{data['nombre']}</b>.\n\n¿Qué módulo quieres probar hoy?"
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('oferta_'))
def ver_oferta_ia(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    bot.answer_callback_query(call.id, "Analizando vacante con IA...")
    
    try:
        prompt = f"""
        Compara el perfil de un estudiante de {data['nombre']} (Habilidades: {data['habilidades_estudiante']}) 
        con esta vacante: Cargo: {data['oferta_titulo']} en {data['empresa']}. Requisitos: {data['requisitos_vacante']}.
        Dame un porcentaje de compatibilidad y un feedback breve de 2 líneas con tono motivador.
        """
        respuesta_ia = modelo_gemini.generate_content(prompt).text
        texto_final = f"📢 <b>VACANTE: {data['oferta_titulo']}</b>\n🏢 {data['empresa']}\n\n🤖 <b>Análisis IA:</b>\n{respuesta_ia}"
    except Exception:
        texto_final = f"📢 <b>VACANTE: {data['oferta_titulo']}</b>\n(Análisis IA no disponible temporalmente)"

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔙 Volver al Menú", callback_data=f"menu_{carrera_id}"))
    bot.edit_message_text(texto_final, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('capsula_'))
def generar_capsula_ia(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    bot.answer_callback_query(call.id, "Generando cápsula...")
    
    try:
        prompt = f"Crea un micro-tutorial de 3 viñetas cortas para un estudiante de {data['nombre']} sobre: {data['requisitos_vacante']}."
        respuesta_ia = modelo_gemini.generate_content(prompt).text
        texto_final = f"🎬 <b>Micro-Cápsula</b>\n\n{respuesta_ia}"
    except Exception:
        texto_final = "⚠️ Error generando la cápsula."

    bot.edit_message_text(texto_final, call.message.chat.id, call.message.message_id, reply_markup=botones_retorno(carrera_id), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('entrevista_'))
def simular_entrevista(call):
    carrera_id = call.data.split('_')[1]
    data = CAREER_DATA[carrera_id]
    
    texto = f"🎙️ <b>Simulador de Entrevistas</b>\n\nPregunta:\n<i>\"{data['pregunta']}\"</i>\n\n<b>Escribe tu respuesta aquí mismo:</b>"
    msg = bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    bot.register_next_step_handler(msg, procesar_respuesta_entrevista, carrera_id)

def procesar_respuesta_entrevista(message, carrera_id):
    respuesta_usuario = message.text
    msg_espera = bot.send_message(message.chat.id, "⏳ <i>Evaluando respuesta con IA...</i>", parse_mode='HTML')
    
    try:
        prompt = f"Eres reclutador. Carrera: {CAREER_DATA[carrera_id]['nombre']}. Pregunta: {CAREER_DATA[carrera_id]['pregunta']}. Respuesta estudiante: {respuesta_usuario}. Dale feedback de 2 párrafos: qué hizo bien y qué mejorar."
        respuesta_ia = modelo_gemini.generate_content(prompt).text
    except Exception:
        respuesta_ia = "⚠️ Error analizando tu respuesta."
    
    bot.edit_message_text(f"🤖 <b>Feedback IA:</b>\n\n{respuesta_ia}", message.chat.id, msg_espera.message_id, reply_markup=botones_retorno(carrera_id), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('cv_'))
def generar_cv(call):
    carrera_id = call.data.split('_')[1]
    texto = "¡Tu CV está optimizado! 📄\n¿Autorizas compartirlo con empresas aliadas?"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🚀 Sí, enviar", callback_data=f"menu_{carrera_id}"))
    markup.row(InlineKeyboardButton("🔙 Volver", callback_data=f"menu_{carrera_id}"))
    bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

# ==========================================
# 5. ENDPOINTS FLASK Y WEBHOOK
# ==========================================
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def webhook():
    try:
        # Intentamos configurar el webhook de forma segura
        bot.remove_webhook()
        bot.set_webhook(url=f"{URL}/{TOKEN}")
    except Exception as e:
        print(f"Aviso de webhook (puede ignorarse si ya está activo): {e}")
    
    return "🚀 Servidor activo y Webhook configurado con éxito.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
