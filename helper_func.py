# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — HELPERS
#
#  FSub check: MEMBER status OR in req_users DB
#  Mandatory check: MEMBER status only (direct join)
# ═══════════════════════════════════════════════════════

import os
import random
from pyrogram.enums import ChatMemberStatus
from database.database import (
    get_fsub_channels,
    get_mandatory_channel,
    req_user_exist,
)


async def is_sub(client, user_id: int, channel_id: int) -> bool:
    """Check if user is a real member of a channel (MEMBER/ADMIN/OWNER)."""
    try:
        member = await client.get_chat_member(channel_id, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def is_sub_fsub(client, user_id: int, channel_id: int) -> bool:
    """
    FSub channel check — passes if EITHER:
    1. User is a full MEMBER/ADMIN/OWNER, OR
    2. User has sent a join request (stored in req_users DB)

    This allows join-request-mode channels to work correctly.
    """
    # Check real membership first
    if await is_sub(client, user_id, channel_id):
        return True
    # Fall back to join-request DB
    return await req_user_exist(channel_id, user_id)


async def is_subscribed(client, user_id: int) -> bool:
    """
    Check ALL fsub channels.
    Uses is_sub_fsub so join-request users are counted as subscribed.
    """
    channels = await get_fsub_channels()
    for ch_id in channels:
        if not await is_sub_fsub(client, user_id, ch_id):
            return False
    return True


async def is_in_mandatory(client, user_id: int) -> bool:
    """
    Check mandatory verification channel.
    Uses direct membership check only (mandatory channel uses direct join).
    """
    ch_id = await get_mandatory_channel()
    if not ch_id:
        return True  # No mandatory channel set → skip check
    return await is_sub(client, user_id, ch_id)


def get_pic(env_key: str, fallback: str) -> str:
    """Pick a random picture from comma-separated env var."""
    pics = os.environ.get(env_key, "").split(",")
    pics = [p.strip() for p in pics if p.strip()]
    return random.choice(pics) if pics else fallback
