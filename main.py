# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — ENTRY POINT
# ═══════════════════════════════════════════════════════

import asyncio
import threading
import logging
from pyrogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from bot import Bot
from api import start_api
from config import ADMINS

log = logging.getLogger(__name__)

# ── Command lists ─────────────────────────────────────

USER_COMMANDS = [
    BotCommand("start",  " Main menu"),
    BotCommand("help",   " Help & instructions"),
    BotCommand("mycode", " Show your current code"),
    BotCommand("revoke", "♻️ Revoke your code"),
]

ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand("addfsub",       "➕ Add a force-sub channel"),
    BotCommand("delfsub",       "➖ Remove a force-sub channel"),
    BotCommand("listfsub",      " List all fsub channels"),
    BotCommand("setmandatory",  " Set mandatory channel"),
    BotCommand("delmandatory",  " Remove mandatory channel"),
    BotCommand("showmandatory", " Show mandatory channel"),
]


async def set_commands(bot: Bot):
    """Set scoped commands — admins see admin menu, users see user menu."""
    try:
        # All users → user commands
        await bot.set_bot_commands(
            USER_COMMANDS,
            scope=BotCommandScopeDefault(),
        )
        log.info("✅ Default user commands set")

        # Each admin → full command list in their private chat
        for admin_id in ADMINS:
            try:
                await bot.set_bot_commands(
                    ADMIN_COMMANDS,
                    scope=BotCommandScopeChat(chat_id=admin_id),
                )
                log.info(f"✅ Admin commands set for {admin_id}")
            except Exception as e:
                log.warning(f"⚠️ Could not set admin commands for {admin_id}: {e}")

    except Exception as e:
        log.error(f"❌ set_commands failed: {e}")


async def run_bot():
    bot = Bot()
    await bot.start()

    # Set command scopes right after bot starts
    await set_commands(bot)

    log.info("✅ Bot is running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()  # block forever


if __name__ == "__main__":
    # Flask API in background thread
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    log.info("🌐 Flask API thread started")

    # Pyrogram bot in main thread
    asyncio.run(run_bot())
