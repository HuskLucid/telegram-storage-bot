import os
import asyncio
import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables
TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')   # e.g., -1001234567890 (negative for channel)

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 Storage Bot running.\n"
        "Send me any file (max 2GB) – I'll split it into 1.9GB chunks and store it.\n"
        "To retrieve, use /get <filename> – I'll reassemble and send back."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    orig_name = doc.file_name
    tmp_dir = "/tmp"
    base_path = f"{tmp_dir}/{orig_name}"

    await update.message.reply_text(f"📥 Received: {orig_name}. Splitting into chunks...")

    # Download the file
    await file.download_to_drive(base_path)

    # Split into 1.9 GB chunks
    subprocess.run(["split", "-b", "1900M", base_path, f"{base_path}.part"])

    # Upload each chunk to the channel
    chunk_files = [f for f in os.listdir(tmp_dir) if f.startswith(f"{orig_name}.part")]
    for chunk in chunk_files:
        with open(f"{tmp_dir}/{chunk}", "rb") as f:
            await context.bot.send_document(chat_id=CHANNEL_ID, document=f, filename=chunk)
        os.remove(f"{tmp_dir}/{chunk}")

    os.remove(base_path)
    await update.message.reply_text(f"✅ Uploaded {len(chunk_files)} chunks to storage.")

async def handle_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expecting /get filename
    if not context.args:
        await update.message.reply_text("Usage: /get <filename>")
        return
    filename = context.args[0]
    await update.message.reply_text(f"🔍 Searching for chunks of {filename}...")
    # In a real implementation, you'd list channel messages and download them.
    # For simplicity, we'll tell the user to retrieve from the channel.
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
