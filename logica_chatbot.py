import html
import logging
import os

import telebot
from flask import Flask, abort, request
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from google import genai


# ---------- Configuración ----------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("practibot")

# El servicio no inicia si falta alguna variable obligatoria.
TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
URL = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")

# Puedes cambiar el modelo aquí si eliges otro en la documentación de Gemini.
GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_FALLBACK_MODEL = "gemini-3.8-flash"

# threaded=False procesa el mensaje durante la solicitud y permite registrar errores.
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
gemini = genai.Client(api_key=GEMINI_KEY)


# ---------- Datos del bot ----------

CAREER_DATA = {
    "sistemas": {
        "nombre": "Ing. de Sistemas 💻",
        "habilidades": "Python, React, SQL, Git",
        "oferta": "Desarrollador Fullstack Jr.",
        "empresa": "Tech Innovación",
        "requisitos": "Next.js, Tailwind CSS, PostgreSQL",
        "pregunta": "¿Cómo estructurarías el backend de una app escalable usando Supabase?",
    },
    "psicologia": {
        "nombre": "Psicología 🧠",
        "habilidades": "Entrevistas, Excel, informes",
        "oferta": "Práctica Organizacional",
        "empresa": "Clínica San José",
        "requisitos": "Pruebas psicotécnicas, Wartegg",
        "pregunta": "¿Qué metodología usarías para medir el clima laboral en un equipo de 50 personas?",
    },
    "admon": {
        "nombre": "Admon. de Empresas 📊",
        "habilidades": "Gestión, contabilidad, liderazgo",
        "oferta": "Analista de Proyectos Jr.",
        "empresa": "Grupo Norte",
        "requisitos": "Power BI, KPIs, Scrum",
        "pregunta": "Menciona 3 KPIs que usarías para evaluar la rentabilidad de un proyecto.",
    },
    "derecho": {
        "nombre": "Derecho ⚖️",
        "habilidades": "Investigación, derecho civil, redacción",
        "oferta": "Asistente Jurídico",
        "empresa": "Firma Legal Consultores",
        "requisitos": "Derecho laboral, tutelas",
        "pregunta": "¿Cuáles son los pasos para radicar una acción de tutela por derecho de petición?",
    },
}


def generar_respuesta_ia(prompt):
    """Llama a Gemini y usa un segundo modelo si el principal falla."""
    for model_name in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL):
        try:
            response = gemini.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if response.text:
                return response.text.strip()

            logger.warning("Gemini no devolvió texto usando %s", model_name)
        except Exception:
            logger.exception(
                "Falló Gemini usando %s; probaré el siguiente modelo",
                model_name,
            )

    raise RuntimeError(
        "Gemini no pudo generar una respuesta con los modelos disponibles"
    )


def texto_html(texto):
    """Escapa texto para que una respuesta de IA no rompa parse_mode=HTML."""
    return html.escape(texto)


def botones_retorno(carrera_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            "🔙 Volver al Menú",
            callback_data=f"menu_{carrera_id}",
        )
    )
    markup.row(
        InlineKeyboardButton("🔄 Cambiar Carrera", callback_data="inicio")
    )
    return markup


def teclado_carreras():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Ing. de Sistemas 💻", callback_data="menu_sistemas"),
        InlineKeyboardButton("Psicología 🧠", callback_data="menu_psicologia"),
    )
    markup.row(
        InlineKeyboardButton("Admon. de Empresas 📊", callback_data="menu_admon"),
        InlineKeyboardButton("Derecho ⚖️", callback_data="menu_derecho"),
    )
    return markup


def generar_onboarding():
    return (
        "¡Hola! Soy <b>PractiBot USB</b> 🤖\n"
        "Tu asistente de empleabilidad con IA. "
        "¿De qué programa académico eres?"
    )


# ---------- Comandos y menús ----------

@bot.message_handler(commands=["start"])
def send_welcome(message):
    logger.info("Comando /start recibido en chat %s", message.chat.id)
    bot.send_message(
        message.chat.id,
        generar_onboarding(),
        reply_markup=teclado_carreras(),
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data == "inicio")
def reset_inicio(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        generar_onboarding(),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=teclado_carreras(),
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def menu_principal(call):
    bot.answer_callback_query(call.id)
    carrera_id = call.data.removeprefix("menu_")
    data = CAREER_DATA.get(carrera_id)

    if not data:
        bot.send_message(call.message.chat.id, "No reconocí esa carrera. Usa /start.")
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            "🏢 Ver Ofertas (IA)",
            callback_data=f"oferta_{carrera_id}",
        ),
        InlineKeyboardButton(
            "🎬 Cápsulas (IA)",
            callback_data=f"capsula_{carrera_id}",
        ),
    )
    markup.row(
        InlineKeyboardButton(
            "🎤 Entrevista (IA)",
            callback_data=f"entrevista_{carrera_id}",
        ),
        InlineKeyboardButton("📄 Mi CV", callback_data=f"cv_{carrera_id}"),
    )
    markup.row(
        InlineKeyboardButton("🔄 Cambiar Carrera", callback_data="inicio")
    )

    texto = (
        f"¡Perfecto! Perfil configurado para "
        f"<b>{data['nombre']}</b>.\n\n"
        "¿Qué módulo quieres probar hoy?"
    )
    bot.edit_message_text(
        texto,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML",
    )


# ---------- Funciones con Gemini ----------

@bot.callback_query_handler(func=lambda call: call.data.startswith("oferta_"))
def ver_oferta_ia(call):
    bot.answer_callback_query(call.id, "Analizando vacante...")
    carrera_id = call.data.removeprefix("oferta_")
    data = CAREER_DATA.get(carrera_id)

    if not data:
        return

    prompt = (
        f"Compara el perfil de un estudiante de {data['nombre']} "
        f"(habilidades: {data['habilidades']}) con esta vacante: "
        f"{data['oferta']} en {data['empresa']}. "
        f"Requisitos: {data['requisitos']}. "
        "Dame un porcentaje de compatibilidad y un feedback breve "
        "de dos líneas con tono motivador."
    )

    try:
        respuesta = texto_html(generar_respuesta_ia(prompt))
        texto = (
            f"📢 <b>VACANTE: {data['oferta']}</b>\n"
            f"🏢 {data['empresa']}\n\n"
            f"🤖 <b>Análisis IA:</b>\n{respuesta}"
        )
    except Exception:
        logger.exception("Falló la generación del análisis de vacante")
        texto = (
            f"📢 <b>VACANTE: {data['oferta']}</b>\n"
            "⚠️ No pude generar el análisis con IA en este momento."
        )

    bot.edit_message_text(
        texto,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=botones_retorno(carrera_id),
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("capsula_"))
def generar_capsula_ia(call):
    bot.answer_callback_query(call.id, "Generando cápsula...")
    carrera_id = call.data.removeprefix("capsula_")
    data = CAREER_DATA.get(carrera_id)

    if not data:
        return

    prompt = (
        f"Crea un microtutorial de tres viñetas cortas para un estudiante "
        f"de {data['nombre']} sobre estos requisitos profesionales: "
        f"{data['requisitos']}."
    )

    try:
        respuesta = texto_html(generar_respuesta_ia(prompt))
        texto = f"🎬 <b>Micro-Cápsula</b>\n\n{respuesta}"
    except Exception:
        logger.exception("Falló la generación de la cápsula")
        texto = "⚠️ No pude generar la cápsula con IA en este momento."

    bot.edit_message_text(
        texto,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=botones_retorno(carrera_id),
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("entrevista_"))
def simular_entrevista(call):
    bot.answer_callback_query(call.id)
    carrera_id = call.data.removeprefix("entrevista_")
    data = CAREER_DATA.get(carrera_id)

    if not data:
        return

    texto = (
        "🎙️ <b>Simulador de Entrevistas</b>\n\n"
        f"Pregunta:\n<i>“{data['pregunta']}”</i>\n\n"
        "<b>Escribe tu respuesta aquí mismo:</b>"
    )
    mensaje = bot.edit_message_text(
        texto,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(
        mensaje,
        procesar_respuesta_entrevista,
        carrera_id,
    )


def procesar_respuesta_entrevista(message, carrera_id):
    if not message.text:
        bot.send_message(
            message.chat.id,
            "Por favor, responde con un mensaje de texto.",
            reply_markup=botones_retorno(carrera_id),
        )
        return

    data = CAREER_DATA.get(carrera_id)
    if not data:
        return

    espera = bot.send_message(message.chat.id, "⏳ Evaluando tu respuesta...")

    prompt = (
        f"Eres reclutador. Carrera: {data['nombre']}. "
        f"Pregunta: {data['pregunta']}. "
        f"Respuesta del estudiante: {message.text}. "
        "Da feedback en dos párrafos: qué hizo bien y qué puede mejorar."
    )

    try:
        respuesta = texto_html(generar_respuesta_ia(prompt))
    except Exception:
        logger.exception("Falló la evaluación de la respuesta de entrevista")
        respuesta = "⚠️ No pude analizar tu respuesta con IA en este momento."

    bot.edit_message_text(
        f"🤖 <b>Feedback IA:</b>\n\n{respuesta}",
        message.chat.id,
        espera.message_id,
        reply_markup=botones_retorno(carrera_id),
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("cv_"))
def generar_cv(call):
    bot.answer_callback_query(call.id)
    carrera_id = call.data.removeprefix("cv_")
    texto = (
        "¡Tu CV está optimizado! 📄\n"
        "¿Autorizas compartirlo con empresas aliadas?"
    )

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Sí, enviar", callback_data=f"menu_{carrera_id}")
    )
    markup.row(
        InlineKeyboardButton("🔙 Volver", callback_data=f"menu_{carrera_id}")
    )
    bot.edit_message_text(
        texto,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


# ---------- Webhook de Telegram para Render ----------

@app.route("/", methods=["GET"])
def health():
    """Render usa esta ruta para comprobar que el servicio está activo."""
    try:
        result = bot.set_webhook(
            url=f"{URL}/telegram-webhook",
            secret_token=WEBHOOK_SECRET,
        )
        if not result:
            logger.error("Telegram no confirmó la configuración del webhook")
            return "No se pudo configurar el webhook", 500

        logger.info("Webhook configurado correctamente")
        return "PractiBot está activo", 200
    except Exception:
        logger.exception("Error configurando el webhook")
        return "Error configurando el webhook", 500


@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    if (
        request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        != WEBHOOK_SECRET
    ):
        logger.warning("Solicitud webhook rechazada: secreto incorrecto")
        abort(403)

    update_data = request.get_json(silent=True)
    if not update_data:
        logger.error("Telegram envió una solicitud sin JSON válido")
        abort(400)

    try:
        update = telebot.types.Update.de_json(update_data)
        logger.info("Actualización de Telegram recibida: %s", update.update_id)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception:
        logger.exception("Error procesando una actualización de Telegram")
        return "Error procesando actualización", 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
    )

