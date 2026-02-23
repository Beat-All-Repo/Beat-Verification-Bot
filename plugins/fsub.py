# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — FSUB WATCHER
#
#  FSub channels use join-request mode:
#    on_chat_join_request  → store user in req_users DB
#    on_chat_member_updated → remove from req_users when user leaves
#                           → invalidate codes when user leaves
#
#  Mandatory channel: also watches join requests now,
#  so it works regardless of whether the channel uses
#  direct join or "Approve new members" mode.
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


# ── Handle join requests (FSub + Mandatory channels) ──

@Bot.on_chat_join_request()
async def handle_join_request(client: Bot, request: ChatJoinRequest):
    chat_id = request.chat.id
    user_id = request.from_user.id

    fsub_channels = await get_fsub_channels()
    mand_ch       = await get_mandatory_channel()

    # Watch BOTH fsub channels AND the mandatory channel
    watched = set(fsub_channels)
    if mand_ch:
        watched.add(mand_ch)

    if chat_id not in watched:
        return

    # Store user in req_users so is_subscribed() / is_in_mandatory() count them as joined
    if not await req_user_exist(chat_id, user_id):
        await req_user(chat_id, user_id)
        source = "mandatory" if chat_id == mand_ch else "fsub"
        print(f"[FSUB] ✅ Stored join request ({source}): user {user_id} → channel {chat_id}")


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

        # Remove from req_users DB (covers both fsub and mandatory channels)
        if await req_user_exist(chat_id, user_id):
            await del_req_user(chat_id, user_id)

        # Invalidate all their codes
        await invalidate_all_codes(user_id)
