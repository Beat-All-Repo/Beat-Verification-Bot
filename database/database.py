# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — DATABASE (MongoDB)
#
#  Two clients:
#   • Motor   (async) → used by Pyrogram bot
#   • pymongo (sync)  → used by Flask API routes
# ═══════════════════════════════════════════════════════

import random
import string
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from config import MONGO_URI, DB_NAME, MAX_DEVICES

# ── Async client (bot) ────────────────────────────────
_async_client  = AsyncIOMotorClient(MONGO_URI)
_async_db      = _async_client[DB_NAME]

a_users_col    = _async_db["users"]
a_codes_col    = _async_db["codes"]
a_devices_col  = _async_db["devices"]
a_channels_col = _async_db["channels"]       # fsub channels
a_settings_col = _async_db["settings"]       # mandatory channel + other settings
a_req_col      = _async_db["req_users"]      # join-request users per fsub channel

# ── Sync client (Flask API) ───────────────────────────
_sync_client  = MongoClient(MONGO_URI)
_sync_db      = _sync_client[DB_NAME]

s_codes_col   = _sync_db["codes"]
s_devices_col = _sync_db["devices"]


# ═══════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ═══════════════════════════════════════════════════════

def _gen_code() -> str:
    return "".join(random.choices(string.digits, k=6))

def _now() -> str:
    return datetime.utcnow().isoformat()


# ═══════════════════════════════════════════════════════
#  USER MANAGEMENT  (async)
# ═══════════════════════════════════════════════════════

async def present_user(user_id: int) -> bool:
    return bool(await a_users_col.find_one({"_id": user_id}))

async def add_user(user_id: int):
    await a_users_col.insert_one({"_id": user_id, "joined_at": _now()})

async def del_user(user_id: int):
    """Remove a user from the database (blocked / deactivated)."""
    await a_users_col.delete_one({"_id": user_id})

async def full_userbase() -> list:
    return [u["_id"] async for u in a_users_col.find()]


# ═══════════════════════════════════════════════════════
#  FSUB CHANNEL MANAGEMENT  (async)
# ═══════════════════════════════════════════════════════

async def add_fsub_channel(channel_id: int):
    await a_channels_col.update_one(
        {"_id": channel_id},
        {"$set": {"_id": channel_id, "type": "fsub", "added_at": _now()}},
        upsert=True,
    )

async def del_fsub_channel(channel_id: int):
    await a_channels_col.delete_one({"_id": channel_id, "type": "fsub"})
    # Also clean up all req_users for this channel
    await a_req_col.delete_one({"_id": channel_id})

async def get_fsub_channels() -> list:
    return [doc["_id"] async for doc in a_channels_col.find({"type": "fsub"})]

async def fsub_channel_exists(channel_id: int) -> bool:
    return bool(await a_channels_col.find_one({"_id": channel_id, "type": "fsub"}))


# ═══════════════════════════════════════════════════════
#  JOIN REQUEST USERS  (async)
#
#  Schema: { _id: channel_id, user_ids: [user_id, ...] }
#
#  Used for FSub channels with join-request mode.
#  When a user sends a join request → store here.
#  When user leaves → remove from here.
#  is_subscribed checks MEMBER status OR this DB.
# ═══════════════════════════════════════════════════════

async def reqChannel_exist(channel_id: int) -> bool:
    """Returns True if this channel is a fsub channel (all fsub channels use req mode)."""
    return await fsub_channel_exists(channel_id)


async def req_user_exist(channel_id: int, user_id: int) -> bool:
    """Check if user is in the join-request list for this channel."""
    doc = await a_req_col.find_one({"_id": channel_id})
    if not doc:
        return False
    return user_id in doc.get("user_ids", [])


async def req_user(channel_id: int, user_id: int):
    """Add user to join-request list for this channel."""
    await a_req_col.update_one(
        {"_id": channel_id},
        {"$addToSet": {"user_ids": user_id}},
        upsert=True,
    )


async def del_req_user(channel_id: int, user_id: int):
    """Remove user from join-request list for this channel."""
    await a_req_col.update_one(
        {"_id": channel_id},
        {"$pull": {"user_ids": user_id}},
    )


async def del_all_req_users(channel_id: int):
    """Remove all request users for a channel."""
    await a_req_col.delete_one({"_id": channel_id})


# ═══════════════════════════════════════════════════════
#  MANDATORY CHANNEL MANAGEMENT  (async)
# ═══════════════════════════════════════════════════════

async def set_mandatory_channel(channel_id: int):
    await a_settings_col.update_one(
        {"_id": "mandatory_channel"},
        {"$set": {"value": channel_id, "updated_at": _now()}},
        upsert=True,
    )

async def del_mandatory_channel():
    await a_settings_col.delete_one({"_id": "mandatory_channel"})

async def get_mandatory_channel():
    doc = await a_settings_col.find_one({"_id": "mandatory_channel"})
    return doc["value"] if doc else None


# ═══════════════════════════════════════════════════════
#  CODE MANAGEMENT  (async)
# ═══════════════════════════════════════════════════════

async def get_active_code(telegram_id: int):
    return await a_codes_col.find_one({"telegram_id": telegram_id, "is_active": True})


async def create_code(telegram_id: int) -> str:
    """Delete old code + clear its devices, then generate a fresh one."""
    old = await a_codes_col.find_one({"telegram_id": telegram_id, "is_active": True})
    if old:
        await a_devices_col.delete_many({"code": old["code"]})
        await a_codes_col.delete_one({"_id": old["_id"]})

    while True:
        code = _gen_code()
        if not await a_codes_col.find_one({"code": code, "is_active": True}):
            break

    await a_codes_col.insert_one({
        "code":         code,
        "telegram_id":  telegram_id,
        "created_at":   _now(),
        "is_active":    True,
        "total_claims": 0,
    })
    return code


async def revoke_code(telegram_id: int):
    """User-triggered revoke."""
    doc = await a_codes_col.find_one({"telegram_id": telegram_id, "is_active": True})
    if doc:
        await a_devices_col.delete_many({"code": doc["code"]})
        await a_codes_col.delete_one({"_id": doc["_id"]})


async def invalidate_all_codes(telegram_id: int):
    """Auto-revoke when user leaves a channel."""
    async for doc in a_codes_col.find({"telegram_id": telegram_id, "is_active": True}):
        await a_devices_col.delete_many({"code": doc["code"]})
        await a_codes_col.delete_one({"_id": doc["_id"]})


async def get_device_count(code: str) -> int:
    return await a_devices_col.count_documents({"code": code})


# ═══════════════════════════════════════════════════════
#  SYNC FUNCTIONS  (Flask API — no async)
# ═══════════════════════════════════════════════════════

def sync_global_stats() -> dict:
    active_codes = s_codes_col.count_documents({"is_active": True})
    agg          = list(s_codes_col.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_claims"}}}
    ]))
    total_used   = int(agg[0]["total"]) if agg else 0
    active_users = [
        doc["telegram_id"]
        for doc in s_codes_col.find({"is_active": True}, {"telegram_id": 1, "_id": 0})
    ]
    return {
        "active_codes":   active_codes,
        "max_concurrent": MAX_DEVICES,
        "can_generate":   True,
        "total_used":     total_used,
        "active_users":   active_users,
    }


def sync_verify_code(code: str, device_id: str) -> dict:
    doc = s_codes_col.find_one({"code": code, "is_active": True})
    if not doc:
        return {"valid": False, "reason": "Code not found or no longer active"}

    if s_devices_col.find_one({"code": code, "device_id": device_id}):
        dev_count = s_devices_col.count_documents({"code": code})
        return {"valid": True, "telegram_id": doc["telegram_id"],
                "devices_used": dev_count, "devices_max": MAX_DEVICES, "device_slot": "existing"}

    dev_count = s_devices_col.count_documents({"code": code})

    if dev_count >= MAX_DEVICES:
        oldest = s_devices_col.find_one({"code": code}, sort=[("claimed_at", 1)])
        if oldest:
            s_devices_col.delete_one({"_id": oldest["_id"]})
            dev_count -= 1

    s_devices_col.insert_one({"code": code, "device_id": device_id, "ip":ip, "claimed_at": _now()})
    s_codes_col.update_one({"code": code}, {"$inc": {"total_claims": 1}})
    return {"valid": True, "telegram_id": doc["telegram_id"],
            "devices_used": dev_count + 1, "devices_max": MAX_DEVICES, "device_slot": "new"}


def sync_check_code(code: str) -> dict:
    doc = s_codes_col.find_one({"code": code, "is_active": True})
    if not doc:
        return {"valid": False, "reason": "Code not found or inactive"}
    dev_count = s_devices_col.count_documents({"code": code})
    return {"valid": True, "telegram_id": doc["telegram_id"],
            "devices_used": dev_count, "devices_remaining": max(0, MAX_DEVICES - dev_count)}


def sync_revoke_code(code: str = None, telegram_id: int = None):
    if code:
        s_devices_col.delete_many({"code": code})
        s_codes_col.delete_one({"code": code})
    elif telegram_id:
        for doc in s_codes_col.find({"telegram_id": telegram_id, "is_active": True}):
            s_devices_col.delete_many({"code": doc["code"]})
        s_codes_col.delete_many({"telegram_id": telegram_id, "is_active": True})
