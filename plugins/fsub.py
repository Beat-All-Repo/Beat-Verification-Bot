# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — FSUB WATCHER
#
#  FSub channels use join-request mode:
#    on_chat_join_request  → store user in req_users DB
#    on_chat_member_updated → remove from req_users when user leaves
#                           → invalidate codes when user leaves
#
#  Mandatory channel uses direct join (no request handling here).
# ═══════════════════════════════════════════════════════

from pyrogram.types import ChatMemberUpdated, ChatJoinRequest
from pyrogram.enums import ChatMemberStatus
from bot import Bot
from database.database import (
    get_fsub_channels,
    get_mandatory_channel,
    invalidate_all_codes,
    reqChannel_exist,
    req_user_exist,
    req_user,
    del_req_user,
)


# ── Handle join requests (FSub channels only) ─────────

@Bot.on_chat_join_request()
async def handle_join_request(client: Bot, request: ChatJoinRequest):
    chat_id = request.chat.id
    user_id = request.from_user.id

    # Only process FSub channels (mandatory uses direct join — no requests)
    if not await reqChannel_exist(chat_id):
        return

    # Store user in req_users so is_subscribed() counts them as joined
    if not await req_user_exist(chat_id, user_id):
        await req_user(chat_id, user_id)
        print(f"[FSUB] ✅ Stored join request: user {user_id} → channel {chat_id}")


# ── Handle member updates ─────────────────────────────

@Bot.on_chat_member_updated()
async def handle_member_update(client: Bot, update: ChatMemberUpdated):
    chat_id = update.chat.id

    # Watch both fsub and mandatory channels
    fsub    = set(await get_fsub_channels())
    mand    = await get_mandatory_channel()
    watched = fsub | ({mand} if mand else set())

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
        print(f"[FSUB] User {user_id} left {chat_id} — cleaning up")

        # Remove from req_users DB if this is a fsub channel
        if chat_id in fsub:
            if await req_user_exist(chat_id, user_id):
                await del_req_user(chat_id, user_id)

        # Invalidate all their codes
        await invalidate_all_codes(user_id)
