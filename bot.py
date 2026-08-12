import os
import asyncio
import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Read from environment variables (set in Render)
TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not TOKEN or not CHANNEL_ID:
    raise ValueError("BOT_TOKEN and CHANNEL_ID must be set in environment")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Storage bot is running. Send me a file.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    orig_name = doc.file_name
    tmp_dir = "/tmp"
    base_path = f"{tmp_dir}/{orig_name}"

    await update.message.reply_text(f"📥 Received: {orig_name}. Splitting...")

    await file.download_to_drive(base_path)
    subprocess.run(["split", "-b", "1900M", base_path, f"{base_path}.part"])

    chunk_files = [f for f in os.listdir(tmp_dir) if f.startswith(f"{orig_name}.part")]
    for chunk in chunk_files:
        with open(f"{tmp_dir}/{chunk}", "rb") as f:
            await context.bot.send_document(chat_id=CHANNEL_ID, document=f, filename=chunk)
        os.remove(f"{tmp_dir}/{chunk}")

    os.remove(base_path)
    await update.message.reply_text(f"✅ Uploaded {len(chunk_files)} chunks.")

async def handle_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /get <filename>")
        return
    filename = context.args[0]
    await update.message.reply_text(f"🔍 Searching for chunks of {filename}...")
    await update.message.reply_text("Manual retrieval: go to the storage channel and download all .part files, then reassemble with: cat *.part.* > file")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", handle_get))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    logging.info("Bot started polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
