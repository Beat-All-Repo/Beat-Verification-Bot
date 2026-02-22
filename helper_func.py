# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — HELPERS
#  Channels are read from MongoDB, not config.
# ═══════════════════════════════════════════════════════

import os
import random
from pyrogram.enums import ChatMemberStatus
from database.database import get_fsub_channels, get_mandatory_channel


async def is_sub(client, user_id: int, channel_id: int) -> bool:
    """Check if user is member of a single channel."""
    try:
        member = await client.get_chat_member(channel_id, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def is_subscribed(client, user_id: int) -> bool:
    """Check ALL fsub channels stored in DB."""
    channels = await get_fsub_channels()
    for ch_id in channels:
        if not await is_sub(client, user_id, ch_id):
            return False
    return True


async def is_in_mandatory(client, user_id: int) -> bool:
    """Check mandatory verification channel stored in DB."""
    ch_id = await get_mandatory_channel()
    if not ch_id:
        return True  # No mandatory channel set → skip check
    return await is_sub(client, user_id, ch_id)


def get_pic(env_key: str, fallback: str) -> str:
    """Pick a random picture from comma-separated env var."""
    pics = os.environ.get(env_key, "").split(",")
    pics = [p.strip() for p in pics if p.strip()]
    return random.choice(pics) if pics else fallback
