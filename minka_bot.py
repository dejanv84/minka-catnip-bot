import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Povezava z bazo podatkov za sledenje točkam
conn = sqlite3.connect('catnip.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS players (user_id INTEGER PRIMARY KEY, username TEXT, catnip INTEGER)''')
conn.commit()

# Funkcija za začetek igre
async def start(update: Update, context: CallbackContext):
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
    await update.message.reply_text(
        "Here’s how you can earn catnip 🌿:\n"
        "1️⃣ Buy $COSCAT (0.05 SOL or more) on Pump.fun and send a screenshot here: +50 catnip\n"
        "2️⃣ Invite a friend to join CosmoCat Crew (send their username): +20 catnip\n"
        "3️⃣ Share a Minka meme on X with #CosmoCat and send the link: +30 catnip\n"
        "Send proof of your tasks directly to me here in private messages. Use /score to check your points."
    )

# Funkcija za preverjanje točk
async def score(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    c.execute("SELECT catnip FROM players WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    catnip = result[0] if result else 0
    await update.message.reply_text(f"Meow meow! 🐾 You have {catnip} catnip 🌿.")

# Funkcija za obdelavo dokazil (slike, besedilo, povezave)
async def handle_proof(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    # Potrdi prejem dokazila igralcu
    await update.message.reply_text(
        f"Thanks for sending your proof, {username}! 🐾 I’ll review it and add your catnip soon. Check your score with /score."
    )
    
    # Obvesti admina (tebe) o novem dokazilu
    proof_message = f"New proof from {username} (ID: {user_id}):"
    await context.bot.send_message(chat_id=int(os.getenv("899820232")), text=proof_message)  # Zamenjaj z tvojim Telegram ID-jem
    
    # Če je dokazilo slika
    if update.message.photo:
        await context.bot.send_photo(chat_id=int(os.getenv("899820232")), photo=update.message.photo[-1].file_id)
    # Če je dokazilo besedilo ali povezava
    elif update.message.text:
        await context.bot.send_message(chat_id=int(os.getenv("899820232")), text=update.message.text)

# Funkcija za ročno dodajanje točk (za admina)
async def addcatnip(update: Update, context: CallbackContext):
    if update.message.from_user.id != int(os.getenv("899820232")):  # Zamenjaj z ID-jem admina (tvoj ID)
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

# Glavna funkcija
def main():
    # Ustvari aplikacijo z BotFather tokenom
    app = Application.builder().token(os.getenv("8018248459:AAGvQWJJ9EbGbVEiyffWcWLQXNi2W_KYhQ0").build()  # Zamenjaj z BotFather tokenom

    # Dodaj handlerje
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tasks", tasks))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("addcatnip", addcatnip))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_proof))
    app.add_handler(MessageHandler(filters.PHOTO, handle_proof))

    # Začni bot-a
    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()