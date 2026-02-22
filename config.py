# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — CONFIG
#  Set all values as Render Environment Variables
# ═══════════════════════════════════════════════════════

import os
from typing import List

# ── Telegram ──────────────────────────────────────────
API_ID       = int(os.environ.get("API_ID", 0))
API_HASH     = os.environ.get("API_HASH", "")
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourVerifyBot")

# ── Admins ────────────────────────────────────────────
ADMINS: List[int] = [
    int(x.strip())
    for x in os.environ.get("ADMIN_IDS", "0").split(",")
    if x.strip().isdigit()
]

# ── MongoDB ───────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://user:pass@cluster.mongodb.net")
DB_NAME   = os.environ.get("DB_NAME", "verifybot")

# ── Verification ──────────────────────────────────────
MAX_DEVICES = 2   # max simultaneous devices per code

# ── API / Website ─────────────────────────────────────
API_SECRET = os.environ.get("API_SECRET", "changeme_use_strong_secret")
PORT       = int(os.environ.get("PORT", 10000))

# ── Support Links ─────────────────────────────────────
SUPPORT_GROUP   = os.environ.get("SUPPORT_GROUP",   "https://t.me/YourGroup")
UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "https://t.me/YourChannel")

# ── Pictures (comma-separated for random selection) ───
START_PIC  = os.environ.get("START_PIC",  "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
HELP_PIC   = os.environ.get("HELP_PIC",   "https://telegra.ph/file/e292b12890b8b4b9dcbd1.jpg")
FORCE_PIC  = os.environ.get("FORCE_PIC",  "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
VERIFY_PIC = os.environ.get("VERIFY_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")

# ── Messages ──────────────────────────────────────────
START_MSG = (
    "<b>🔐 Hᴇʏ {mention} ~</b>\n\n"
    "<b>➪ Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Bᴏᴛ!</b>\n\n"
    "<blockquote expandable>"
    "<b>I ɢᴇɴᴇʀᴀᴛᴇ ᴀ <code>6-ᴅɪɢɪᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴄᴏᴅᴇ</code> ᴛʜᴀᴛ\n"
    "ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴏɴ ᴏᴜʀ ᴡᴇʙsɪᴛᴇ ᴛᴏ ᴠᴇʀɪғʏ ʏᴏᴜʀ Tᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ.\n\n"
    "📌 ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:\n"
    "① Jᴏɪɴ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs\n"
    "② Jᴏɪɴ ᴛʜᴇ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴄʜᴀɴɴᴇʟ\n"
    "③ Gᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ᴄᴏᴅᴇ\n"
    "④ Eɴᴛᴇʀ ɪᴛ ᴏɴ ᴏᴜʀ ᴡᴇʙsɪᴛᴇ\n\n"
    "⚠️ 1 ᴄᴏᴅᴇ ᴘᴇʀ ᴜsᴇʀ • Mᴀx 2 ᴅᴇᴠɪᴄᴇs</b>"
    "</blockquote>"
)

FORCE_MSG = (
    "<b>⛔ {mention}, Yᴏᴜ ᴀʀᴇ ɴᴏᴛ sᴜʙsᴄʀɪʙᴇᴅ!</b>\n\n"
    "<b>➪ Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ.\n"
    "Aғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ♻️ Tʀʏ Aɢᴀɪɴ.</b>"
)
