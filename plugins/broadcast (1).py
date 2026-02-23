# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — BROADCAST
#
#  Commands (admin only, private chat):
#    /broadcast   — send a message to all users
#    /pbroadcast  — send + pin a message to all users
#    /dbroadcast {seconds} — send + auto-delete after N seconds
# ═══════════════════════════════════════════════════════

import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import ADMINS
from database.database import full_userbase, del_user

admin = filters.user(ADMINS) if ADMINS else filters.user([])

REPLY_ERROR = "<code>Use this command as a reply to any telegram message.</code>"


# ═══════════════════════════════════════════════════════
#  /broadcast — send to all users
# ═══════════════════════════════════════════════════════

@Bot.on_message(filters.private & filters.command("broadcast") & admin)
async def send_text(client: Bot, message: Message):
    if not message.reply_to_message:
        err = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await err.delete()
        return

    broadcast_msg = message.reply_to_message
    query = await full_userbase()
    total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

    pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")

    for chat_id in query:
        try:
            await broadcast_msg.copy(chat_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await broadcast_msg.copy(chat_id)
            successful += 1
        except UserIsBlocked:
            await del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(chat_id)
            deleted += 1
        except Exception:
            unsuccessful += 1
        total += 1

    status = (
        f"<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
        f"Total Users: <code>{total}</code>\n"
        f"Successful: <code>{successful}</code>\n"
        f"Blocked Users: <code>{blocked}</code>\n"
        f"Deleted Accounts: <code>{deleted}</code>\n"
        f"Unsuccessful: <code>{unsuccessful}</code>"
    )
    await pls_wait.edit(status)


# ═══════════════════════════════════════════════════════
#  /pbroadcast — send + pin to all users
# ═══════════════════════════════════════════════════════

@Bot.on_message(filters.private & filters.command("pbroadcast") & admin)
async def send_pin_text(client: Bot, message: Message):
    if not message.reply_to_message:
        err = await message.reply("Reply to a message to broadcast and pin it.")
        await asyncio.sleep(8)
        await err.delete()
        return

    broadcast_msg = message.reply_to_message
    query = await full_userbase()
    total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

    pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")

    for chat_id in query:
        try:
            sent = await broadcast_msg.copy(chat_id)
            await client.pin_chat_message(chat_id=chat_id, message_id=sent.id, both_sides=True)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            sent = await broadcast_msg.copy(chat_id)
            await client.pin_chat_message(chat_id=chat_id, message_id=sent.id, both_sides=True)
            successful += 1
        except UserIsBlocked:
            await del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(chat_id)
            deleted += 1
        except Exception as e:
            print(f"[BROADCAST] Failed for {chat_id}: {e}")
            unsuccessful += 1
        total += 1

    status = (
        f"<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
        f"Total Users: <code>{total}</code>\n"
        f"Successful: <code>{successful}</code>\n"
        f"Blocked Users: <code>{blocked}</code>\n"
        f"Deleted Accounts: <code>{deleted}</code>\n"
        f"Unsuccessful: <code>{unsuccessful}</code>"
    )
    await pls_wait.edit(status)


# ═══════════════════════════════════════════════════════
#  /dbroadcast {seconds} — send + auto-delete after N seconds
# ═══════════════════════════════════════════════════════

@Bot.on_message(filters.private & filters.command("dbroadcast") & admin)
async def delete_broadcast(client: Bot, message: Message):
    if not message.reply_to_message:
        err = await message.reply("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ ᴡɪᴛʜ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ.")
        await asyncio.sleep(8)
        await err.delete()
        return

    try:
        duration = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply(
            "<b>Pʟᴇᴀsᴇ ᴜsᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b>\n"
            "Usage: <code>/dbroadcast {seconds}</code>"
        )
        return

    broadcast_msg = message.reply_to_message
    query = await full_userbase()
    total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

    pls_wait = await message.reply("<i>Broadcast with auto-delete processing....</i>")

    for chat_id in query:
        try:
            sent = await broadcast_msg.copy(chat_id)
            await asyncio.sleep(duration)
            await sent.delete()
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            sent = await broadcast_msg.copy(chat_id)
            await asyncio.sleep(duration)
            await sent.delete()
            successful += 1
        except UserIsBlocked:
            await del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(chat_id)
            deleted += 1
        except Exception:
            unsuccessful += 1
        total += 1

    status = (
        f"<b><u>Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴡɪᴛʜ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
        f"Total Users: <code>{total}</code>\n"
        f"Successful: <code>{successful}</code>\n"
        f"Blocked Users: <code>{blocked}</code>\n"
        f"Deleted Accounts: <code>{deleted}</code>\n"
        f"Unsuccessful: <code>{unsuccessful}</code>"
    )
    await pls_wait.edit(status)
