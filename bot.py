# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — BOT CLASS
# ═══════════════════════════════════════════════════════

import logging
from datetime import datetime, timezone
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="VerifyBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"},
            sleep_threshold=30,
            workers=4,
        )
        self.uptime = datetime.now(timezone.utc)

    async def start(self):
        await super().start()
        me = await self.get_me()
        logging.info(f"✅ Bot started as @{me.username} ({me.id})")

    async def stop(self):
        await super().stop()
        logging.info("🛑 Bot stopped")
