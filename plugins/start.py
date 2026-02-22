# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — START PANEL
# ═══════════════════════════════════════════════════════

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from bot import Bot
from config import START_MSG, START_PIC, SUPPORT_GROUP, UPDATES_CHANNEL
from helper_func import get_pic
from database.database import present_user, add_user


def start_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Fᴏʀᴄᴇ Sᴜʙ",       callback_data="fsub_panel"),
            InlineKeyboardButton("❓ Hᴇʟᴘ",              callback_data="help"),
        ],
        [
            InlineKeyboardButton("🔑 Gᴇᴛ Vᴇʀɪғʏ Cᴏᴅᴇ", callback_data="getcode"),
        ],
        [
            InlineKeyboardButton("🌐 Wᴇʙsɪᴛᴇ",          url=UPDATES_CHANNEL),
            InlineKeyboardButton("💬 Sᴜᴘᴘᴏʀᴛ",           url=SUPPORT_GROUP),
        ],
    ])


@Bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Bot, message: Message):
    user    = message.from_user
    user_id = user.id

    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except Exception:
            pass

    pic     = get_pic("START_PIC", START_PIC)
    caption = START_MSG.format(
        mention=user.mention,
        first=user.first_name,
        last=user.last_name or "",
        username=f"@{user.username}" if user.username else "ɴ/ᴀ",
        id=user_id,
    )

    try:
        await message.reply_photo(
            photo=pic,
            caption=caption,
            reply_markup=start_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        print(f"[START] Photo failed: {e}")
        await message.reply_text(
            text=caption,
            reply_markup=start_keyboard(),
            parse_mode=ParseMode.HTML,
        )
