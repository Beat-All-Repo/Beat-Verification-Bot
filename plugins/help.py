# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — HELP / MYCODE / REVOKE COMMANDS
# ═══════════════════════════════════════════════════════

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from bot import Bot
from config import HELP_PIC, SUPPORT_GROUP, UPDATES_CHANNEL, MAX_DEVICES
from helper_func import get_pic
from database.database import get_active_code, get_device_count, revoke_code


def _help_text(user_name: str) -> str:
    content = (
        "<b>➪ I ᴀᴍ ᴀ Wᴇʙsɪᴛᴇ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Bᴏᴛ.\n\n"
        "➪ I ɢᴇɴᴇʀᴀᴛᴇ ᴀ <code>6-ᴅɪɢɪᴛ ᴄᴏᴅᴇ</code> ʏᴏᴜ ᴇɴᴛᴇʀ ᴏɴ ᴛʜᴇ ᴡᴇʙsɪᴛᴇ.\n\n"
        "➪ Yᴏᴜ ᴍᴜsᴛ ʀᴇᴍᴀɪɴ ɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄᴏᴅᴇ ᴀᴄᴛɪᴠᴇ.\n\n"
        "━ /start      — Mᴀɪɴ ᴍᴇɴᴜ\n"
        "━ /mycode     — Sʜᴏᴡ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴄᴏᴅᴇ\n"
        "━ /revoke     — Rᴇᴠᴏᴋᴇ ʏᴏᴜʀ ᴄᴏᴅᴇ\n"
        "━ /help       — Tʜɪs ᴍᴇssᴀɢᴇ</b>"
    )
    return (
        f"<b>‼️ Hᴇʟʟᴏ {user_name} ~</b>\n\n"
        f"<blockquote expandable>{content}</blockquote>\n"
        "<b>◈ Sᴛɪʟʟ ʜᴀᴠᴇ ᴅᴏᴜʙᴛs? Cᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ʙᴇʟᴏᴡ.</b>"
    )


def _help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Sᴜᴘᴘᴏʀᴛ",  url=SUPPORT_GROUP),
            InlineKeyboardButton("📣 Cʜᴀɴɴᴇʟ",  url=UPDATES_CHANNEL),
        ],
        [
            InlineKeyboardButton("🔑 Gᴇᴛ Cᴏᴅᴇ", callback_data="getcode"),
            InlineKeyboardButton("✖️ Cʟᴏsᴇ",    callback_data="close"),
        ],
    ])


@Bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Bot, message: Message):
    pic  = get_pic("HELP_PIC", HELP_PIC)
    text = _help_text(message.from_user.first_name)
    try:
        await message.reply_photo(
            photo=pic, caption=text,
            reply_markup=_help_keyboard(),
            parse_mode=ParseMode.HTML, quote=True,
        )
    except Exception as e:
        print(f"[HELP] Photo failed: {e}")
        await message.reply_text(
            text=text, reply_markup=_help_keyboard(),
            parse_mode=ParseMode.HTML, quote=True,
        )


@Bot.on_message(filters.command("mycode") & filters.private)
async def mycode_command(client: Bot, message: Message):
    user_id = message.from_user.id
    doc     = await get_active_code(user_id)

    if not doc:
        return await message.reply_text(
            "<b>❌ Yᴏᴜ ʜᴀᴠᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏᴅᴇ.\n\n"
            "➪ ᴜsᴇ /start ᴀɴᴅ ᴄʟɪᴄᴋ 🔑 Gᴇᴛ Vᴇʀɪғʏ Cᴏᴅᴇ.</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Gᴇᴛ Cᴏᴅᴇ", callback_data="getcode")]
            ]),
            quote=True,
        )

    code      = doc["code"]
    dev_count = await get_device_count(code)
    created   = doc.get("created_at", "Unknown")[:19]

    await message.reply_text(
        "<b>🔑 Yᴏᴜʀ Aᴄᴛɪᴠᴇ Cᴏᴅᴇ:</b>\n\n"
        f"<b>Cᴏᴅᴇ    :</b> <code>{code}</code>\n"
        f"<b>Cʀᴇᴀᴛᴇᴅ :</b> <code>{created} UTC</code>\n"
        f"<b>Dᴇᴠɪᴄᴇs :</b> <code>{dev_count}/{MAX_DEVICES}</code>\n\n"
        "<b><i>ᴜsᴇ /revoke ᴛᴏ ʀᴇsᴇᴛ ʏᴏᴜʀ ᴄᴏᴅᴇ.</i></b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("♻️ Rᴇᴠᴏᴋᴇ Cᴏᴅᴇ", callback_data="revoke_confirm")]
        ]),
        quote=True,
    )


@Bot.on_message(filters.command("revoke") & filters.private)
async def revoke_command(client: Bot, message: Message):
    user_id = message.from_user.id
    doc     = await get_active_code(user_id)

    if not doc:
        return await message.reply_text(
            "<b>ℹ️ Yᴏᴜ ʜᴀᴠᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏᴅᴇ ᴛᴏ ʀᴇᴠᴏᴋᴇ.</b>",
            parse_mode=ParseMode.HTML, quote=True,
        )

    await message.reply_text(
        f"<b>⚠️ Yᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴄᴏᴅᴇ:</b> <code>{doc['code']}</code>\n\n"
        "<b>Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇᴠᴏᴋᴇ ɪᴛ?</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yᴇs, Rᴇᴠᴏᴋᴇ", callback_data="revoke_confirm"),
                InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ",       callback_data="cancel"),
            ]
        ]),
        quote=True,
    )
