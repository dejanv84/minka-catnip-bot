import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext._utils.webhookhandler import WebhookServer
from telegram.ext._application import Application

# Nastavi beleženje
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Povezava z bazo podatkov za sledenje točkam
conn = sqlite3.connect('catnip.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS players (user_id INTEGER PRIMARY KEY, username TEXT, catnip INTEGER)''')
conn.commit()

# Funkcija za začetek igre
async def start(update: Update, context: CallbackContext):
    logger.info(f"Received /start command from user {update.message.from_user.id}")
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name
    
    c.execute("INSERT OR IGNORE INTO players (user_id, username, catnip) VALUES (?, ?, ?)", (user_id, username, 0))
    conn.commit()
    
    await update.message.reply_text(
        f"Meow meow, {username}! 🐾 I’m Minka, the cosmic kitty, and I need your help to get to Mars! 🚀\n"
        "Join my Catnip Quest by completing tasks to earn catnip 🌿. Use /tasks to see how you can help!\n"
        "Since the group chat is locked, send your task proofs directly to me here in private messages."
    )

# Funkcija za prikaz nalog
async def tasks(update: Update, context: CallbackContext):
    logger.info(f"Received /tasks command from user {update.message.from_user.id}")
    await update.message.reply_text(
        "Here’s how you can earn catnip 🌿:\n"
        "1️⃣ Buy $COSCAT (0.05 SOL or more) on Pump.fun and send a screenshot here: +50 catnip\n"
        "2️⃣ Invite a friend to join CosmoCat Crew (send their username): +20 catnip\n"
        "3️⃣ Share a Minka meme on X with #CosmoCat and send the link: +30 catnip\n"
        "Send proof of your tasks directly to me here in private messages. Use /score to check your points."
    )

# Funkcija za preverjanje točk
async def score(update: Update, context: CallbackContext):
    logger.info(f"Received /score command from user {update.message.from_user.id}")
    user_id = update.message.from_user.id
    c.execute("SELECT catnip FROM players WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    catnip = result[0] if result else 0
    await update.message.reply_text(f"Meow meow! 🐾 You have {catnip} catnip 🌿.")

# Funkcija za obdelavo dokazil (slike, besedilo, povezave)
async def handle_proof(update: Update, context: CallbackContext):
    logger.info(f"Received proof from user {update.message.from_user.id}")
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    # Potrdi prejem dokazila igralcu
    await update.message.reply_text(
        f"Thanks for sending your proof, {username}! 🐾 I’ll review it and add your catnip soon. Check your score with /score."
    )
    
    # Obvesti admina (tebe) o novem dokazilu
    proof_message = f"New proof from {username} (ID: {user_id}):"
    await context.bot.send_message(chat_id=int(os.getenv("ADMIN_ID")), text=proof_message)
    
    # Če je dokazilo slika
    if update.message.photo:
        await context.bot.send_photo(chat_id=int(os.getenv("ADMIN_ID")), photo=update.message.photo[-1].file_id)
    # Če je dokazilo besedilo ali povezava
    elif update.message.text:
        await context.bot.send_message(chat_id=int(os.getenv("ADMIN_ID")), text=update.message.text)

# Funkcija za ročno dodajanje točk (za admina)
async def addcatnip(update: Update, context: CallbackContext):
    logger.info(f"Received /addcatnip command from user {update.message.from_user.id}")
    if update.message.from_user.id != int(os.getenv("ADMIN_ID")):
        return
    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
        c.execute("UPDATE players SET catnip = catnip + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        await context.bot.send_message(chat_id=user_id, text=f"Meow meow! 🐾 You’ve earned {amount} catnip 🌿. Check your score with /score.")
        await update.message.reply_text(f"Added {amount} catnip to user {user_id}!")
    except:
        await update.message.reply_text("Usage: /addcatnip <user_id> <amount>")

# Funkcija za zbiranje naslovov denarnic (neobvezno, če si dodal /submitwallet)
async def submitwallet(update: Update, context: CallbackContext):
    logger.info(f"Received /submitwallet command from user {update.message.from_user.id}")
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    await update.message.reply_text(
        "Please send your Solana wallet address to receive your $COSCAT rewards."
    )

async def handle_wallet(update: Update, context: CallbackContext):
    logger.info(f"Received wallet address from user {update.message.from_user.id}")
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    wallet_address = update.message.text
    
    # Obvesti admina o naslovu denarnice
    await context.bot.send_message(
        chat_id=int(os.getenv("ADMIN_ID")),
        text=f"New wallet address from {username} (ID: {user_id}):\n{wallet_address}"
    )
    await update.message.reply_text(
        f"Thanks, {username}! Your wallet address has been submitted. You’ll receive your $COSCAT rewards soon."
    )

# Ustvari aplikacijo
app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

# Dodaj handlerje
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tasks", tasks))
app.add_handler(CommandHandler("score", score))
app.add_handler(CommandHandler("addcatnip", addcatnip))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proof))
app.add_handler(MessageHandler(filters.PHOTO, handle_proof))
app.add_handler(CommandHandler("submitwallet", submitwallet))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^(https?://)'), handle_wallet))

# Inicializacija aplikacije
async def on_startup():
    logger.info("Initializing application...")
    webhook_url = f"https://minka-catnip-bot.onrender.com/{os.getenv('BOT_TOKEN')}"
    await app.initialize()
    await app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

# Zaustavitev aplikacije
async def on_shutdown():
    logger.info("Shutting down application...")
    await app.shutdown()

# ASGI aplikacija za uvicorn/gunicorn
async def application(scope, receive, send):
    logger.info("Received ASGI request")
    if scope['type'] == 'http':
        path = scope['path'].strip('/')
        if path == os.getenv("BOT_TOKEN"):
            body = b""
            while True:
                message = await receive()
                body += message.get('body', b'')
                if message.get('more_body', False) is False:
                    break
            update = Update.de_json(body.decode('utf-8'), app.bot)
            await app.process_update(update)
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'OK',
            })
        else:
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Not Found',
            })
    elif scope['type'] == 'lifespan':
        message = await receive()
        if message['type'] == 'lifespan.startup':
            await on_startup()
            await send({'type': 'lifespan.startup.complete'})
        elif message['type'] == 'lifespan.shutdown':
            await on_shutdown()
            await send({'type': 'lifespan.shutdown.complete'})