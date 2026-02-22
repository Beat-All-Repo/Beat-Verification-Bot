# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — FSUB WATCHER
#  Auto-revokes codes when users leave any watched channel
# ═══════════════════════════════════════════════════════

from pyrogram.types import ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus
from bot import Bot
from database.database import get_fsub_channels, get_mandatory_channel, invalidate_all_codes


@Bot.on_chat_member_updated()
async def handle_member_update(client: Bot, update: ChatMemberUpdated):
    chat_id = update.chat.id

    # Build set of watched channels from DB
    fsub     = set(await get_fsub_channels())
    mand     = await get_mandatory_channel()
    watched  = fsub | ({mand} if mand else set())

    if chat_id not in watched:
        return

    old = update.old_chat_member
    new = update.new_chat_member
    if not old or not new:
        return

    was_in = old.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    )
    now_in = new.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    )

    if was_in and not now_in:
        user_id = old.user.id
        print(f"[FSUB] User {user_id} left {chat_id} — invalidating codes")
        await invalidate_all_codes(user_id)
