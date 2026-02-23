# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — CALLBACK HANDLER
#
#  FSub channels    → join REQUEST link (stored in DB, counts as joined)
#  Mandatory channel → DIRECT join link (user joins instantly)
# ═══════════════════════════════════════════════════════

from datetime import datetime, timedelta
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from bot import Bot
from config import (
    START_MSG, START_PIC, HELP_PIC, FORCE_PIC, VERIFY_PIC,
    SUPPORT_GROUP, UPDATES_CHANNEL, MAX_DEVICES, FORCE_MSG,
)
from helper_func import get_pic, is_sub, is_subscribed, is_in_mandatory
from database.database import (
    get_active_code, create_code, revoke_code,
    get_device_count, get_fsub_channels, get_mandatory_channel,
)

print("[CBB] ✅ Callback handler loading...")


# ── Keyboard builders ─────────────────────────────────

def _help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP),
            InlineKeyboardButton("📣 Cʜᴀɴɴᴇʟ", url=UPDATES_CHANNEL),
        ],
        [
            InlineKeyboardButton(" Hᴏᴍᴇ",  callback_data="start"),
            InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close"),
        ],
    ])


def _help_text(user_name: str) -> str:
    content = (
        "<b>➪ I ᴀᴍ ᴀ Wᴇʙsɪᴛᴇ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Bᴏᴛ.\n"
        "➪ I ɢᴇɴᴇʀᴀᴛᴇ ᴀ <code>6-ᴅɪɢɪᴛ ᴄᴏᴅᴇ</code> ʏᴏᴜ ᴇɴᴛᴇʀ ᴏɴ ᴛʜᴇ ᴡᴇʙsɪᴛᴇ.\n"
        "➪ Yᴏᴜ ᴍᴜsᴛ ʀᴇᴍᴀɪɴ ɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄᴏᴅᴇ ᴀᴄᴛɪᴠᴇ.\n"
        "━ /start   — Mᴀɪɴ ᴍᴇɴᴜ\n"
        "━ /mycode  — Sʜᴏᴡ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴄᴏᴅᴇ\n"
        "━ /revoke  — Rᴇᴠᴏᴋᴇ ʏᴏᴜʀ ᴄᴏᴅᴇ\n"
        "━ /help    — Tʜɪs ᴍᴇssᴀɢᴇ</b>"
    )
    return (
        f"<b>‼️ Hᴇʟʟᴏ {user_name} ~</b>\n\n"
        f"<blockquote expandable>{content}</blockquote>\n"
        "<b>◈ Sᴛɪʟʟ ʜᴀᴠᴇ ᴅᴏᴜʙᴛs? Cᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ʙᴇʟᴏᴡ.</b>"
    )


# ── Link builders ─────────────────────────────────────

async def _request_link(client, ch_id: int) -> str:
    """
    FSub — creates a JOIN REQUEST link.
    User sends request → on_chat_join_request fires → stored in DB.
    Bot does NOT auto-approve — user stays as requester, DB counts them as joined.
    """
    try:
        inv = await client.create_chat_invite_link(
            ch_id,
            expire_date=datetime.utcnow() + timedelta(hours=24),
            creates_join_request=True,
        )
        return inv.invite_link
    except Exception as e:
        print(f"[CBB] request link error {ch_id}: {e}")
        try:
            chat = await client.get_chat(ch_id)
            if chat.username:
                return f"https://t.me/{chat.username}"
        except Exception:
            pass
        return None


async def _direct_link(client, ch_id: int) -> str:
    """
    Mandatory channel — creates a DIRECT join link.
    User joins instantly → bot can verify MEMBER status right away.
    """
    try:
        chat = await client.get_chat(ch_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        inv = await client.create_chat_invite_link(
            ch_id,
            expire_date=datetime.utcnow() + timedelta(hours=24),
            # No creates_join_request → direct join
        )
        return inv.invite_link
    except Exception as e:
        print(f"[CBB] direct link error {ch_id}: {e}")
        return None


# ── Join button builders ──────────────────────────────

async def _fsub_buttons(client, user_id: int) -> list:
    """Request-join buttons for FSub channels user hasn't joined/requested."""
    buttons  = []
    channels = await get_fsub_channels()
    for ch_id in channels:
        from helper_func import is_sub_fsub
        if not await is_sub_fsub(client, user_id, ch_id):
            try:
                chat = await client.get_chat(ch_id)
                link = await _request_link(client, ch_id)
                if link:
                    buttons.append([InlineKeyboardButton(f"📣 {chat.title}", url=link)])
            except Exception as e:
                print(f"[CBB] FSub button error {ch_id}: {e}")
    return buttons


async def _mandatory_button(client):
    """Direct-join button for the mandatory verification channel."""
    ch_id = await get_mandatory_channel()
    if not ch_id:
        return None
    try:
        chat = await client.get_chat(ch_id)
        link = await _direct_link(client, ch_id)
        if link:
            return InlineKeyboardButton(f"🔐 {chat.title} (Verification)", url=link)
    except Exception as e:
        print(f"[CBB] Mandatory button error: {e}")
    return None


# ── Main callback router ──────────────────────────────

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data    = query.data
    user    = query.from_user
    user_id = user.id

    print(f"[CBB] 📥 {data!r} from {user_id}")

    # ── Close ─────────────────────────────────────────
    if data == "close":
        try:
            await query.message.delete()
        except Exception:
            pass

    # ── Cancel ────────────────────────────────────────
    elif data == "cancel":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass

    # ── Home / Start ──────────────────────────────────
    elif data == "start":
        from plugins.start import start_keyboard
        pic     = get_pic("START_PIC", START_PIC)
        caption = START_MSG.format(
            mention=user.mention,
            first=user.first_name,
            last=user.last_name or "",
            username=f"@{user.username}" if user.username else "ɴ/ᴀ",
            id=user_id,
        )
        try:
            await query.message.delete()
            await client.send_photo(
                chat_id=user_id, photo=pic, caption=caption,
                reply_markup=start_keyboard(), parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[CBB] start fallback: {e}")
            await client.send_message(
                chat_id=user_id, text=caption,
                reply_markup=start_keyboard(), parse_mode=ParseMode.HTML,
            )

    # ── Help ──────────────────────────────────────────
    elif data == "help":
        await query.answer()
        pic  = get_pic("HELP_PIC", HELP_PIC)
        text = _help_text(user.first_name)
        try:
            await query.message.delete()
            await client.send_photo(
                chat_id=user_id, photo=pic, caption=text,
                reply_markup=_help_keyboard(), parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[CBB] help photo failed: {e}")
            await client.send_message(
                chat_id=user_id, text=text,
                reply_markup=_help_keyboard(), parse_mode=ParseMode.HTML,
            )

    # ── FSub Panel ────────────────────────────────────
    elif data == "fsub_panel":
        await query.answer()
        channels = await get_fsub_channels()
        mand_ch  = await get_mandatory_channel()
        lines    = [f"<b> Fᴏʀᴄᴇ-Sᴜʙ Sᴛᴀᴛᴜs ({len(channels)} ᴄʜᴀɴɴᴇʟs):</b>\n"]

        from helper_func import is_sub_fsub
        for ch_id in channels:
            try:
                chat   = await client.get_chat(ch_id)
                joined = await is_sub_fsub(client, user_id, ch_id)
                tick   = "✅" if joined else "❌"
                lines.append(f"<b>{tick} {chat.title}</b>")
            except Exception:
                lines.append(f"<b>⚠️ <code>{ch_id}</code> (Unavailable)</b>")

        if mand_ch:
            try:
                mc   = await client.get_chat(mand_ch)
                tick = "✅" if await is_sub(client, user_id, mand_ch) else "❌"
                lines.append(f"\n<b>🔐 Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Cʜᴀɴɴᴇʟ:</b>")
                lines.append(f"<b>{tick} {mc.title}</b>")
            except Exception:
                pass

        if not channels and not mand_ch:
            lines.append("<i>No channels configured yet.</i>")

        lines.append("\n<i>Jᴏɪɴ ᴀʟʟ ✅ ᴄʜᴀɴɴᴇʟs ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴄᴏᴅᴇ.</i>")

        try:
            await query.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(" Hᴏᴍᴇ", callback_data="start"),
                     InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close")]
                ]),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await query.message.delete()
            await client.send_message(
                chat_id=user_id,
                text="\n".join(lines),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(" Hᴏᴍᴇ", callback_data="start"),
                     InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close")]
                ]),
                parse_mode=ParseMode.HTML,
            )

    # ── Get Code — Step 1: FSub check ─────────────────
    elif data == "getcode":
        await query.answer()
        loading = await query.message.reply("<b><i>⏳ ᴄʜᴇᴄᴋɪɴɢ..</i></b>")

        if not await is_subscribed(client, user_id):
            buttons = await _fsub_buttons(client, user_id)
            buttons.append([
                InlineKeyboardButton("♻️ Tʀʏ Aɢᴀɪɴ", callback_data="getcode"),
                InlineKeyboardButton(" Hᴏᴍᴇ",        callback_data="start"),
            ])
            pic = get_pic("FORCE_PIC", FORCE_PIC)
            await loading.delete()
            try:
                await query.message.delete()
            except Exception:
                pass
            await client.send_photo(
                chat_id=user_id, photo=pic,
                caption=FORCE_MSG.format(
                    mention=user.mention, first=user.first_name,
                    last=user.last_name or "",
                    username=f"@{user.username}" if user.username else "ɴ/ᴀ",
                    id=user_id,
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML,
            )
            return

        # Step 2: Mandatory channel check
        if not await is_in_mandatory(client, user_id):
            mand_btn = await _mandatory_button(client)
            buttons  = []
            if mand_btn:
                buttons.append([mand_btn])
            buttons.append([
                InlineKeyboardButton("✅ Jᴏɪɴᴇᴅ — Gᴇɴᴇʀᴀᴛᴇ ᴍʏ ᴄᴏᴅᴇ", callback_data="generate")
            ])
            buttons.append([
                InlineKeyboardButton(" Hᴏᴍᴇ", callback_data="start"),
                InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close"),
            ])
            await loading.delete()
            # ⚠️ Send new message instead of edit — avoids photo→text edit error
            try:
                await query.message.delete()
            except Exception:
                pass
            await client.send_message(
                chat_id=user_id,
                text=(
                    "<b>🔐 Oɴᴇ Mᴏʀᴇ Sᴛᴇᴘ!\n\n"
                    "➪ Jᴏɪɴ ᴛʜᴇ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Cʜᴀɴɴᴇʟ ʙᴇʟᴏᴡ,\n"
                    "   ᴛʜᴇɴ ᴄʟɪᴄᴋ ✅ Jᴏɪɴᴇᴅ ʙᴜᴛᴛᴏɴ.</b>"
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML,
            )
            return

        # All good → show/generate code
        await loading.delete()
        await _show_or_generate(client, query, user_id)

    # ── Generate (after mandatory join) ───────────────
    elif data == "generate":
        await query.answer()
        if not await is_subscribed(client, user_id):
            await query.answer("❌ Yᴏᴜ ʟᴇғᴛ ᴀ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟ!", show_alert=True)
            return
        if not await is_in_mandatory(client, user_id):
            await query.answer(
                "❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ!\n"
                "Jᴏɪɴ ɪᴛ ᴀɴᴅ ᴄᴏᴍᴇ ʙᴀᴄᴋ.",
                show_alert=True,
            )
            return
        # Delete the "One More Step" message and show code
        try:
            await query.message.delete()
        except Exception:
            pass
        await _send_code(client, user_id)

    # ── Revoke Confirm ────────────────────────────────
    elif data == "revoke_confirm":
        await query.answer()
        await revoke_code(user_id)
        try:
            await query.message.edit_text(
                "<b>♻️ Cᴏᴅᴇ Rᴇᴠᴏᴋᴇᴅ!\n"
                "➪ Cʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ɴᴇᴡ ᴄᴏᴅᴇ.</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Gᴇᴛ Nᴇᴡ Cᴏᴅᴇ", callback_data="getcode")],
                    [InlineKeyboardButton(" Hᴏᴍᴇ", callback_data="start"),
                     InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close")],
                ]),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await query.message.delete()
            await client.send_message(
                chat_id=user_id,
                text="<b>♻️ Cᴏᴅᴇ Rᴇᴠᴏᴋᴇᴅ! Cʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ᴀ ɴᴇᴡ ᴄᴏᴅᴇ.</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Gᴇᴛ Nᴇᴡ Cᴏᴅᴇ", callback_data="getcode")],
                    [InlineKeyboardButton(" Hᴏᴍᴇ", callback_data="start"),
                     InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close")],
                ]),
                parse_mode=ParseMode.HTML,
            )


# ── Show or generate code (helper) ───────────────────

async def _show_or_generate(client, query: CallbackQuery, user_id: int):
    """Called from getcode when all checks pass — deletes current msg and sends code."""
    try:
        await query.message.delete()
    except Exception:
        pass
    await _send_code(client, user_id)


async def _send_code(client, user_id: int):
    """Generates or fetches code and sends it as a new message."""
    existing = await get_active_code(user_id)

    if existing:
        code      = existing["code"]
        dev_count = await get_device_count(code)
        created   = existing.get("created_at", "Unknown")[:19]
        txt = (
            "<b>🔑 Yᴏᴜʀ Aᴄᴛɪᴠᴇ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Cᴏᴅᴇ</b>\n\n"
            f"<b>Cᴏᴅᴇ    :</b> <code>{code}</code>\n"
            f"<b>Cʀᴇᴀᴛᴇᴅ :</b> <code>{created} UTC</code>\n"
            f"<b>Dᴇᴠɪᴄᴇs :</b> <code>{dev_count}/{MAX_DEVICES}</code>\n\n"
            "<blockquote expandable>"
            "<b>➪ Eɴᴛᴇʀ ᴛʜɪs ᴄᴏᴅᴇ ᴏɴ ᴛʜᴇ ᴡᴇʙsɪᴛᴇ ᴛᴏ ᴠᴇʀɪғʏ.\n"
            "➪ Kᴇᴇᴘ ʏᴏᴜʀsᴇʟғ ɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴋᴇᴇᴘ ɪᴛ ᴀᴄᴛɪᴠᴇ.\n"
            f"➪ Wᴏʀᴋs ᴏɴ ᴜᴘ ᴛᴏ {MAX_DEVICES} ᴅᴇᴠɪᴄᴇs ᴀᴛ ᴏɴᴄᴇ.</b>"
            "</blockquote>"
        )
    else:
        code = await create_code(user_id)
        txt  = (
            "<b>✅ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Cᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴇᴅ!</b>\n\n"
            f"<b>🔑 Yᴏᴜʀ Cᴏᴅᴇ:</b>\n<code>{code}</code>\n\n"
            "<blockquote expandable>"
            "<b>➪ Eɴᴛᴇʀ ᴛʜɪs ᴏɴ ᴛʜᴇ ᴡᴇʙsɪᴛᴇ ᴛᴏ ᴠᴇʀɪғʏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.\n"
            "➪ Cᴏᴅᴇ ɪs ᴠᴀʟɪᴅ ᴡʜɪʟᴇ ʏᴏᴜ ᴀʀᴇ ɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs.\n"
            f"➪ Wᴏʀᴋs ᴏɴ ᴜᴘ ᴛᴏ {MAX_DEVICES} ᴅᴇᴠɪᴄᴇs sɪᴍᴜʟᴛᴀɴᴇᴏᴜsʟʏ.</b>"
            "</blockquote>"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("♻️ Rᴇᴠᴏᴋᴇ & Rᴇɢᴇɴ", callback_data="revoke_confirm")],
        [InlineKeyboardButton(" Hᴏᴍᴇ", callback_data="start"),
         InlineKeyboardButton("✖️ Cʟᴏsᴇ", callback_data="close")],
    ])

    pic = get_pic("VERIFY_PIC", VERIFY_PIC)
    try:
        await client.send_photo(
            chat_id=user_id, photo=pic, caption=txt,
            reply_markup=keyboard, parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        print(f"[CBB] verify photo failed: {e}")
        await client.send_message(
            chat_id=user_id, text=txt,
            reply_markup=keyboard, parse_mode=ParseMode.HTML,
        )


print("[CBB] ✅ Callback handler loaded!")
