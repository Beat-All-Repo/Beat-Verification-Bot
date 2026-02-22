# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — ENTRY POINT
# ═══════════════════════════════════════════════════════

import asyncio
import threading
import logging
from bot import Bot
from api import start_api

log = logging.getLogger(__name__)


async def run_bot():
    bot = Bot()
    await bot.start()
    log.info("✅ Bot is running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()  # block forever


if __name__ == "__main__":
    # Flask API runs in background thread (sync, no conflict with asyncio)
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    log.info("🌐 Flask API thread started")

    # Pyrogram bot runs in main thread
    asyncio.run(run_bot())
