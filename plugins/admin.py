# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — ADMIN CHANNEL MANAGEMENT
#
#  FSub channels:
#    /addfsub  -100xxxxxxxxx   → add a force-sub channel
#    /delfsub  -100xxxxxxxxx   → remove one channel
#    /delfsub  all             → remove ALL channels
#    /listfsub                 → list all fsub channels
#
#  Mandatory (verification) channel:
#    /setmandatory -100xxxxxxxxx  → set the mandatory channel
#    /delmandatory                → remove mandatory channel
#    /showmandatory               → show current mandatory channel
# ═══════════════════════════════════════════════════════

from pyrogram import filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from pyrogram.enums import ParseMode, ChatType, ChatMemberStatus
from bot import Bot
from config import ADMINS
from database.database import (
    add_fsub_channel, del_fsub_channel, get_fsub_channels, fsub_channel_exists,
    set_mandatory_channel, del_mandatory_channel, get_mandatory_channel,
)

admin = filters.user(ADMINS) if ADMINS else filters.user([])


# ── Helpers ───────────────────────────────────────────

async def _validate_and_check_admin(client, channel_id: int) -> tuple:
    """Returns (ok: bool, error_msg: str, chat_obj)."""
    try:
        chat = await client.get_chat(channel_id)
    except Exception as e:
        return False, f"❌ Cannot access <code>{channel_id}</code>\n<i>{e}</i>", None

    if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP, ChatType.GROUP]:
        return False, "❌ Only channels and supergroups are supported.", None

    try:
        me = await client.get_chat_member(channel_id, "me")
        if me.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return False, (
                f"❌ Bot is not an admin in <b>{chat.title}</b>.\n"
                "Make the bot admin first, then try again."
            ), None
    except Exception as e:
        return False, f"❌ Could not verify bot membership:\n<i>{e}</i>", None

    return True, "", chat


async def _get_link(client, channel_id: int) -> str:
    try:
        chat = await client.get_chat(channel_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        link = await client.export_chat_invite_link(channel_id)
        return link
    except Exception:
        return f"<code>{channel_id}</code>"


# ═══════════════════════════════════════════════════════
#  FSUB COMMANDS
# ═══════════════════════════════════════════════════════

@Bot.on_message(filters.command("addfsub") & filters.private & admin)
async def cmd_add_fsub(client: Bot, message: Message):
    temp = await message.reply("<b><i>⏳ ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        return await temp.edit(
            "<b>Usage:</b> <code>/addfsub -100xxxxxxxxx</code>",
            parse_mode=ParseMode.HTML,
        )

    try:
        channel_id = int(args[1].strip())
    except ValueError:
        return await temp.edit("❌ <b>Invalid ID.</b> Must be like <code>-100123456789</code>")

    if await fsub_channel_exists(channel_id):
        return await temp.edit(
            f"ℹ️ <b>Channel <code>{channel_id}</code> is already in the FSub list.</b>",
            parse_mode=ParseMode.HTML,
        )

    ok, err, chat = await _validate_and_check_admin(client, channel_id)
    if not ok:
        return await temp.edit(err, parse_mode=ParseMode.HTML)

    link = await _get_link(client, channel_id)
    await add_fsub_channel(channel_id)

    await temp.edit(
        f"✅ <b>FSub channel added!</b>\n\n"
        f"<b>Name :</b> <a href='{link}'>{chat.title}</a>\n"
        f"<b>ID   :</b> <code>{channel_id}</code>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 List FSub Channels", callback_data="admin_listfsub")]
        ]),
    )


@Bot.on_message(filters.command("delfsub") & filters.private & admin)
async def cmd_del_fsub(client: Bot, message: Message):
    temp = await message.reply("<b><i>⏳ ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        return await temp.edit(
            "<b>Usage:</b>\n"
            "<code>/delfsub -100xxxxxxxxx</code> — remove one\n"
            "<code>/delfsub all</code>            — remove all",
            parse_mode=ParseMode.HTML,
        )

    arg = args[1].strip()

    if arg.lower() == "all":
        channels = await get_fsub_channels()
        if not channels:
            return await temp.edit("ℹ️ <b>No FSub channels to remove.</b>")
        for ch_id in channels:
            await del_fsub_channel(ch_id)
        return await temp.edit(
            f"✅ <b>All {len(channels)} FSub channel(s) removed.</b>",
            parse_mode=ParseMode.HTML,
        )

    try:
        channel_id = int(arg)
    except ValueError:
        return await temp.edit("❌ <b>Invalid ID.</b> Use a number or <code>all</code>.")

    if not await fsub_channel_exists(channel_id):
        return await temp.edit(
            f"❌ <b>Channel <code>{channel_id}</code> not found in FSub list.</b>",
            parse_mode=ParseMode.HTML,
        )

    await del_fsub_channel(channel_id)
    await temp.edit(
        f"✅ <b>Removed <code>{channel_id}</code> from FSub list.</b>",
        parse_mode=ParseMode.HTML,
    )


@Bot.on_message(filters.command("listfsub") & filters.private & admin)
async def cmd_list_fsub(client: Bot, message: Message):
    temp     = await message.reply("<b><i>⏳ ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    channels = await get_fsub_channels()

    if not channels:
        return await temp.edit(
            "<b>📋 FSub Channels: None</b>\n\n<i>Add one with /addfsub -100xxxxxxxxx</i>",
            parse_mode=ParseMode.HTML,
        )

    lines = [f"<b>📋 FSub Channels ({len(channels)}):</b>\n"]
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            link = await _get_link(client, ch_id)
            lines.append(f"• <a href='{link}'>{chat.title}</a>  <code>{ch_id}</code>")
        except Exception:
            lines.append(f"• <code>{ch_id}</code> — <i>unavailable</i>")

    await temp.edit(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Remove All", callback_data="admin_delfsub_all")]
        ]),
    )


# ═══════════════════════════════════════════════════════
#  MANDATORY CHANNEL COMMANDS
# ═══════════════════════════════════════════════════════

@Bot.on_message(filters.command("setmandatory") & filters.private & admin)
async def cmd_set_mandatory(client: Bot, message: Message):
    temp = await message.reply("<b><i>⏳ ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        return await temp.edit(
            "<b>Usage:</b> <code>/setmandatory -100xxxxxxxxx</code>",
            parse_mode=ParseMode.HTML,
        )

    try:
        channel_id = int(args[1].strip())
    except ValueError:
        return await temp.edit("❌ <b>Invalid channel ID.</b>")

    ok, err, chat = await _validate_and_check_admin(client, channel_id)
    if not ok:
        return await temp.edit(err, parse_mode=ParseMode.HTML)

    link = await _get_link(client, channel_id)
    await set_mandatory_channel(channel_id)

    await temp.edit(
        f"✅ <b>Mandatory verification channel set!</b>\n\n"
        f"<b>Name :</b> <a href='{link}'>{chat.title}</a>\n"
        f"<b>ID   :</b> <code>{channel_id}</code>\n\n"
        "<i>Users must join this channel to generate a code.</i>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@Bot.on_message(filters.command("delmandatory") & filters.private & admin)
async def cmd_del_mandatory(client: Bot, message: Message):
    current = await get_mandatory_channel()
    if not current:
        return await message.reply(
            "ℹ️ <b>No mandatory channel is currently set.</b>",
            parse_mode=ParseMode.HTML, quote=True,
        )
    await del_mandatory_channel()
    await message.reply(
        "✅ <b>Mandatory channel removed.</b>\n"
        "<i>Users no longer need to join a mandatory channel to get a code.</i>",
        parse_mode=ParseMode.HTML, quote=True,
    )


@Bot.on_message(filters.command("showmandatory") & filters.private & admin)
async def cmd_show_mandatory(client: Bot, message: Message):
    temp  = await message.reply("<b><i>⏳ ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    ch_id = await get_mandatory_channel()

    if not ch_id:
        return await temp.edit(
            "<b>🔐 Mandatory Channel: Not set</b>\n\n"
            "<i>Set one with /setmandatory -100xxxxxxxxx</i>",
            parse_mode=ParseMode.HTML,
        )

    try:
        chat = await client.get_chat(ch_id)
        link = await _get_link(client, ch_id)
        await temp.edit(
            f"<b>🔐 Mandatory Verification Channel:</b>\n\n"
            f"<b>Name :</b> <a href='{link}'>{chat.title}</a>\n"
            f"<b>ID   :</b> <code>{ch_id}</code>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Remove", callback_data="admin_delmandatory")]
            ]),
        )
    except Exception:
        await temp.edit(
            f"<b>🔐 Mandatory Channel:</b> <code>{ch_id}</code>\n"
            "<i>⚠️ Bot may have been removed from this channel</i>",
            parse_mode=ParseMode.HTML,
        )


# ═══════════════════════════════════════════════════════
#  ADMIN BUTTON CALLBACKS
# ═══════════════════════════════════════════════════════

@Bot.on_callback_query(filters.regex(r"^admin_") & admin)
async def admin_callbacks(client: Bot, query: CallbackQuery):
    data = query.data

    if data == "admin_listfsub":
        await query.answer()
        channels = await get_fsub_channels()
        if not channels:
            return await query.answer("No FSub channels configured.", show_alert=True)
        lines = [f"<b>📋 FSub Channels ({len(channels)}):</b>\n"]
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                link = await _get_link(client, ch_id)
                lines.append(f"• <a href='{link}'>{chat.title}</a>  <code>{ch_id}</code>")
            except Exception:
                lines.append(f"• <code>{ch_id}</code> — <i>unavailable</i>")
        await query.message.edit_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    elif data == "admin_delfsub_all":
        await query.answer()
        channels = await get_fsub_channels()
        for ch_id in channels:
            await del_fsub_channel(ch_id)
        await query.message.edit_text(
            f"✅ <b>Removed all {len(channels)} FSub channel(s).</b>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "admin_delmandatory":
        await query.answer()
        await del_mandatory_channel()
        await query.message.edit_text(
            "✅ <b>Mandatory channel removed.</b>",
            parse_mode=ParseMode.HTML,
        )
