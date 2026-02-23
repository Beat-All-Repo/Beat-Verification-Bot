# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — BOT COMMANDS SETUP
#  Runs once on startup.
#  Admins see all commands, users see only user commands.
# ═══════════════════════════════════════════════════════

from pyrogram import filters
from pyrogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChatMember,
    BotCommandScopeChat,
)
from bot import Bot
from config import ADMINS


# ── Command lists ─────────────────────────────────────

USER_COMMANDS = [
    BotCommand("start",  "🏠 Main menu"),
    BotCommand("help",   "❓ Help & instructions"),
    BotCommand("mycode", "🔑 Show your current code"),
    BotCommand("revoke", "♻️ Revoke your code"),
]

ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand("addfsub",       "➕ Add a force-sub channel"),
    BotCommand("delfsub",       "➖ Remove a force-sub channel"),
    BotCommand("listfsub",      "📋 List all fsub channels"),
    BotCommand("setmandatory",  "🔐 Set mandatory channel"),
    BotCommand("delmandatory",  "🗑 Remove mandatory channel"),
    BotCommand("showmandatory", "👁 Show mandatory channel"),
]


# ── Set commands on startup ───────────────────────────

@Bot.on_message(filters.command("start") & filters.private)
async def _setup_commands_once(client: Bot, message, _already_set={"done": False}):
    """
    Hooks onto the first /start to set commands.
    Only runs once per bot session.
    """
    if _already_set["done"]:
        return
    _already_set["done"] = True
    await _set_all_commands(client)


async def _set_all_commands(client: Bot):
    try:
        # 1. Default scope — all users see user commands
        await client.set_bot_commands(
            USER_COMMANDS,
            scope=BotCommandScopeDefault(),
        )

        # 2. Each admin sees full admin commands in their private chat
        for admin_id in ADMINS:
            try:
                await client.set_bot_commands(
                    ADMIN_COMMANDS,
                    scope=BotCommandScopeChat(chat_id=admin_id),
                )
                print(f"[COMMANDS] ✅ Admin commands set for {admin_id}")
            except Exception as e:
                print(f"[COMMANDS] ⚠️ Could not set commands for admin {admin_id}: {e}")

        print("[COMMANDS] ✅ All command scopes set successfully")

    except Exception as e:
        print(f"[COMMANDS] ❌ Failed to set commands: {e}")
