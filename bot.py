"""
my-telegram-bot — starter bot with a built-in HTTP health-check endpoint.

Commands:
  /start  — greet the user
  /help   — list available commands
  /echo   — echo back whatever the user sends

A minimal HTTP server listens on PORT (default 8000) so the platform can
perform liveness checks against the container.
"""

import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8000))


# ---------------------------------------------------------------------------
# Health-check HTTP server (runs in a background daemon thread)
# ---------------------------------------------------------------------------

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):  # silence access logs
        pass


def _start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), _HealthHandler)
    logger.info("Health-check server listening on port %s", PORT)
    server.serve_forever()


# ---------------------------------------------------------------------------
# Telegram bot handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Hi <b>{user.first_name}</b>! 👋\n"
        "I'm your bot. Type /help to see what I can do."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start — say hello\n"
        "/help  — show this message\n"
        "Just send me any text and I'll echo it back!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    # Start the health-check server in the background
    health_thread = threading.Thread(target=_start_health_server, daemon=True)
    health_thread.start()

    # Build and run the bot
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Bot is starting (long-polling)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
