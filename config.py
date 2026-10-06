# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

#  ⚙️  FILE STORE BOT — CONFIGURATION
#
#  Every setting below can be provided in three ways (the first one found wins):
#    1. An environment variable → Heroku / Koyeb / Render / Railway dashboard, or `docker run -e ...`
#    2. A ".env" file           → copy ".env.example" to ".env" and fill it in (VPS / PC)
#    3. The default value       → written right here in this file
#
#  ✔ On/off switches accept TRUE or FALSE (yes/no, on/off and 1/0 work too).
#  ✔ Inside long texts you can write \n for a new line.
#  ✔ Settings marked 🔴 are required — the bot refuses to start without them.

import os
import logging
from logging.handlers import RotatingFileHandler

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ── Helpers that read and validate settings (no need to edit these) ──────────

_TRUE = {"1", "true", "yes", "y", "on", "enable", "enabled"}
_FALSE = {"0", "false", "no", "n", "off", "disable", "disabled"}
_DISABLED = {"none", "null", "off", "false", "no", "0", "disable", "disabled"}


def _raw(*names):
    for name in names:
        value = os.environ.get(name)
        if value is not None:
            return value.strip()
    return None


def _fail(message):
    raise SystemExit(f"❌ CONFIG ERROR: {message}")


def env_text(name, default="", *aliases):
    """A text setting. Left empty → the default is used."""
    value = _raw(name, *aliases)
    if not value:
        return default
    return value.replace("\\n", "\n")


def env_optional(name, default="", *aliases):
    """A text setting that can be switched off with an empty value or none / off."""
    value = _raw(name, *aliases)
    if value is None:
        return default
    if not value or value.lower() in _DISABLED:
        return ""
    return value.replace("\\n", "\n")


def env_url(name, default=""):
    """A link. Links written without https:// (like t.me/username) are fixed automatically."""
    value = env_text(name, default)
    if value and not value.startswith(("http://", "https://", "tg://")):
        value = "https://" + value
    return value


def env_int(name, default=0, *aliases, minimum=None):
    value = _raw(name, *aliases)
    if not value:
        return default
    try:
        number = int(value)
    except ValueError:
        _fail(f"{name} must be a whole number (got {value!r}).")
    if minimum is not None and number < minimum:
        _fail(f"{name} must be at least {minimum} (got {number}).")
    return number


def env_bool(name, default=False, *aliases):
    value = _raw(name, *aliases)
    if not value:
        return default
    if value.lower() in _TRUE:
        return True
    if value.lower() in _FALSE:
        return False
    _fail(f"{name} must be TRUE or FALSE (got {value!r}).")


def env_chat(name):
    """A channel or group: its -100… ID, or the @username of a public one. Empty or 0 → not used."""
    value = _raw(name)
    if not value or value in ("0", "-") or value.lower() in _DISABLED:
        return None
    if value.lstrip("-").isdigit():
        return int(value)
    if "t.me/+" in value or "joinchat" in value or value.startswith("+"):
        _fail(f"{name}: private invite links can't be used here — set the chat ID (starts with -100) instead.")
    if "t.me/" in value:
        value = value.rstrip("/").rsplit("/", 1)[-1]
    return value.lstrip("@")


def env_ids(name, default=""):
    value = _raw(name)
    value = default if value is None else value
    ids = []
    for part in value.replace(",", " ").split():
        try:
            ids.append(int(part))
        except ValueError:
            _fail(f"{name} must only contain numeric Telegram user IDs (got {part!r}).")
    return ids


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🔴 REQUIRED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 🔴 Bot token — create a bot with https://t.me/BotFather and paste its token here.
TG_BOT_TOKEN = env_text("TG_BOT_TOKEN", "")
# 🔴 API ID and API hash of your Telegram app — get both from https://my.telegram.org/apps
APP_ID = env_int("APP_ID", 0)
API_HASH = env_text("API_HASH", "")
# 🔴 ID of your private "database" channel where files are stored (it starts with -100).
#    Add the bot to that channel as an admin.
CHANNEL_ID = env_int("CHANNEL_ID", 0)
# 🔴 Your personal Telegram user ID (send /id to https://t.me/MissRose_bot to get it).
OWNER_ID = env_int("OWNER_ID", 0)
# 🔴 MongoDB connection URL — a free cluster from https://www.mongodb.com/atlas works great.
DB_URL = env_text("DB_URL", "")
# Name of the MongoDB database (created automatically).
DB_NAME = env_text("DB_NAME", "FileStoreBot")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  👑 OWNER & ADMINS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Your public Telegram username (without @). Users are sent here for support and payment screenshots.
OWNER_TAG = env_text("OWNER_TAG", "the_universal_being").lstrip("@")
# Extra admins — Telegram user IDs separated by spaces. Admins can store files, create links and broadcast.
# Example: 6011680723 1234567890   (the owner is always an admin)
ADMINS = env_ids("ADMINS", "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🔐 ACCESS CONTROL — HOW USERS UNLOCK FILES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   fsub      → users must join your force-sub channels before getting files (default)
#   referral  → users must invite REFERRAL_COUNT new users to the bot
#   dual      → users must join the channels FIRST, then complete the referrals
#   off       → no restrictions — anyone with a link gets the file
# 💡 You can also switch modes live from Telegram: send /settings to the bot (owner only).

ACCESS_MODE = env_text("ACCESS_MODE", "fsub").lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  📢 FORCE-SUB CHANNELS — USE 0, 1, 2, 3 OR 4 OF THEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fill only the slots you need and leave the rest empty (or 0). With no channels, force-sub is skipped.
# Use the chat ID (-100…) of a channel / group, or the @username of a public one.
# The bot must be an admin there with the "Invite users via link" permission.

FORCE_SUB_CHANNEL = env_chat("FORCE_SUB_CHANNEL")
FORCE_SUB_CHANNEL2 = env_chat("FORCE_SUB_CHANNEL2")
FORCE_SUB_CHANNEL3 = env_chat("FORCE_SUB_CHANNEL3")
FORCE_SUB_CHANNEL4 = env_chat("FORCE_SUB_CHANNEL4")
# Text shown above the join buttons. Placeholders: {first} {last} {username} {mention} {id}
FORCE_MSG = env_text("FORCE_MSG", "ʜᴇʟʟᴏ ᴛʜᴇʀᴇ {mention}!!👋\n\n<b>ɪɴ ᴏʀᴅᴇʀ ᴛᴏ ɢᴇᴛ ᴛʜᴇ ꜰɪʟᴇꜱ, ʏᴏᴜ ᴀʀᴇ ʀᴇQᴜᴇꜱᴛᴇᴅ ᴛᴏ ꜱᴜᴘᴘᴏʀᴛ ᴜꜱ ʙʏ ᴊᴏɪɴɪɴɢ ᴛʜᴇ ᴄʜᴀɴɴᴇʟꜱ ᴀɴᴅ ɢʀᴏᴜᴘꜱ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ:</b>")
# Optional picture for the force-sub message (same formats as START_PIC).
FORCE_PIC = env_optional("FORCE_PIC", "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  👥 REFERRAL SYSTEM — USED WHEN ACCESS_MODE IS "referral" OR "dual"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Each user gets a personal invite link. A referral is counted only for people who have NEVER used
# this bot before (fresh users) — in dual mode they must also join your force-sub channels.

# How many new users someone must invite to unlock files.
REFERRAL_COUNT = env_int("REFERRAL_COUNT", 3, minimum=1)
# How long files stay unlocked after reaching the goal, in seconds. 0 = unlocked forever.
# Example: 86400 = 24 hours. With a time limit every unlock uses up REFERRAL_COUNT referrals,
# so users keep inviting new people to unlock again.
REFERRAL_EXPIRE = env_int("REFERRAL_EXPIRE", 0, minimum=0)
# Text on the referral screen. Placeholders: {first} {mention} {id} {required} {count} {remaining}
REFERRAL_MSG = env_text("REFERRAL_MSG", "ʜᴇʟʟᴏ ᴛʜᴇʀᴇ {mention}!! 👋\n\n<b>ᴛʜɪꜱ ꜰɪʟᴇ ɪꜱ ʟᴏᴄᴋᴇᴅ 🔐 — ɪɴᴠɪᴛᴇ {required} ɴᴇᴡ ᴜꜱᴇʀꜱ ᴛᴏ ᴛʜɪꜱ ʙᴏᴛ ᴡɪᴛʜ ʏᴏᴜʀ ᴘᴇʀꜱᴏɴᴀʟ ʟɪɴᴋ ᴛᴏ ᴜɴʟᴏᴄᴋ ɪᴛ!</b>")
# Text pre-filled when users tap "Share Link" (their invite link is attached automatically).
REFERRAL_SHARE_TEXT = env_text("REFERRAL_SHARE_TEXT", "📂 Get any file instantly on Telegram — join me with my invite link! 🚀")
# Optional picture for the referral screen (same formats as START_PIC).
REFERRAL_PIC = env_optional("REFERRAL_PIC", "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🏠 START MESSAGE & START IMAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Message sent on /start. Placeholders: {first} {last} {username} {mention} {id}
START_MSG = env_text("START_MESSAGE", "ʜᴇʟʟᴏ ᴛʜᴇʀᴇ {mention}!!🌚\n\nɪ ᴀᴍ ᴅᴇꜱɪɢɴᴇᴅ ᴛᴏ ꜱʜᴀʀᴇ ꜰɪʟᴇꜱ ᴛʜʀᴏᴜɢʜ ꜱᴘᴇᴄɪᴀʟ ʟɪɴᴋꜱ!! 🪄\n\nɪ ᴀᴍ ᴅᴇꜱɪɢɴᴇᴅ ʙʏ @trinityXmods ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ. 🎀", "START_MSG")
# Picture sent together with the start message. You can use:
#   • a direct image link      → https://telegra.ph/file/xxxx.jpg  (telegra.ph, envs.sh, imgbb, GitHub raw …)
#   • a Telegram photo file_id → AgACAgUAAxkBAAI…
#   • an image inside the repo → assets/start.jpg
# Put several (separated by spaces) and one is picked at random each time. Leave empty for a text-only start.
# Telegram allows 1024 characters under a picture — longer start messages are sent without it.
# Ready-made example: https://raw.githubusercontent.com/Trinity-Mods/File-Store-Bot/main/assets/start.jpg
START_PIC = env_optional("START_PIC", "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  📁 FILE DELIVERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Caption added to delivered documents, videos and audio. Placeholders: {filename} {previouscaption}
# Set it to "none" to keep the original captions.
CUSTOM_CAPTION = env_optional("CUSTOM_CAPTION", "ʙᴏᴛ ᴅᴇꜱɪɢɴᴇᴅ ᴡɪᴛʜ ❤️ ʙʏ <b>Trinity Mods</b>\n\n🌐 ɢɪᴛʜᴜʙ: https://github.com/Trinity-Mods\n\n📦 ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ: https://github.com/Trinity-Mods/File-Store-Bot\n\n📢 ᴛᴇʟᴇɢʀᴀᴍ: https://t.me/trinityXmods")
# TRUE = users can't forward or save the files they receive.
PROTECT_CONTENT = env_bool("PROTECT_CONTENT", False)
# Delete delivered files from the user's chat after this many seconds (0 = keep forever). 600 = 10 minutes.
TIME = env_int("TIME", 600, minimum=0)
# TRUE = don't add a "Share URL" button under posts in the database channel.
DISABLE_CHANNEL_BUTTON = env_bool("DISABLE_CHANNEL_BUTTON", True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🔗 SHORTENER & TOKEN VERIFICATION — EARN FROM YOUR LINKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# TRUE = turn on the shortener system.
USE_SHORTLINK = env_bool("USE_SHORTLINK", False)
# Your shortener's website (without https://) and its API key.
SHORTLINK_API_URL = env_text("SHORTLINK_API_URL", "gplinks.com")
SHORTLINK_API_KEY = env_text("SHORTLINK_API_KEY", "")
# TRUE  → every file link goes through the shortener (each link is unlocked separately)
# FALSE → users verify a token through the shortener once every VERIFY_EXPIRE seconds
U_S_E_P = env_bool("U_S_E_P", True) and USE_SHORTLINK
# How long a verified token stays valid, in seconds. 43200 = 12 hours, 86400 = 24 hours.
VERIFY_EXPIRE = env_int("VERIFY_EXPIRE", 43200, minimum=60)
# Tutorial video that shows users how to get through your shortener.
TUT_VID = env_url("TUT_VID", "https://t.me/trinityXmods/53")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  💎 PREMIUM — WORKS TOGETHER WITH USE_SHORTLINK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Premium users skip the shortener AND the referral requirement. Admins add them with /add_prem.

USE_PAYMENT = env_bool("USE_PAYMENT", True) and USE_SHORTLINK
# Your UPI ID and a direct link to your UPI QR code image.
UPI_ID = env_text("UPI_ID", "sendrajbooks@fam")
UPI_IMAGE_URL = env_url("UPI_IMAGE_URL", "https://envs.sh/Vpg.jpg")
# Where users send their payment screenshot (defaults to your OWNER_TAG chat).
SCREENSHOT_URL = env_url("SCREENSHOT_URL", f"https://t.me/{OWNER_TAG}")
# Plan prices — change only the amounts / currency.
PRICE1 = env_text("PRICE1", "₹200")    # 7 days
PRICE2 = env_text("PRICE2", "₹500")    # 1 month
PRICE3 = env_text("PRICE3", "₹800")    # 3 months
PRICE4 = env_text("PRICE4", "₹1500")   # 6 months
PRICE5 = env_text("PRICE5", "₹2850")   # 1 year


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  💬 OTHER TEXTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Reply sent when a normal user messages the bot directly ("none" = stay silent).
USER_REPLY_TEXT = env_optional("USER_REPLY_TEXT", "ʜɪ, ɪ ᴀᴍ ᴍᴀᴅᴇ ʙʏ @trinityXmods\n\nᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ᴅɪʀᴇᴄᴛʟʏ ʙʏ ꜱᴇɴᴅɪɴɢ ꜰɪʟᴇꜱ — ᴏᴛʜᴇʀꜱ ᴄᴀɴɴᴏᴛ ꜱᴇɴᴅ ᴀɴʏᴛʜɪɴɢ ʜᴇʀᴇ.\n\n📦 ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ: https://github.com/Trinity-Mods/File-Store-Bot")
# Text of the /stats command. Placeholder: {uptime}
BOT_STATS_TEXT = env_text("BOT_STATS_TEXT", "<b>BOT UPTIME</b>\n{uptime}", "BOTS_STATS_TEXT")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🛠️ ADVANCED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Port of the small web server used for health checks (Koyeb, Render, Heroku, uptime monitors).
PORT = env_int("PORT", 8080)
# Number of updates the bot handles at the same time.
TG_BOT_WORKERS = env_int("TG_BOT_WORKERS", 50, minimum=1)


# ── No modifications are required beyond this point. Proceed only if you know what you're doing. ──

_MODE_ALIASES = {
    "forcesub": "fsub", "force_sub": "fsub", "force-sub": "fsub", "channel": "fsub", "channels": "fsub",
    "refer": "referral", "ref": "referral", "referrals": "referral",
    "both": "dual", "fsub+referral": "dual", "referral+fsub": "dual",
    "none": "off", "open": "off", "free": "off", "disabled": "off",
}
ACCESS_MODE = _MODE_ALIASES.get(ACCESS_MODE, ACCESS_MODE)
if ACCESS_MODE not in ("off", "fsub", "referral", "dual"):
    _fail(f"ACCESS_MODE must be one of: fsub, referral, dual, off (got {ACCESS_MODE!r}).")

# Every configured force-sub chat, in order, without duplicates (0 – 4 entries).
FORCE_SUB_CHANNELS = list(dict.fromkeys(
    chat for chat in (FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, FORCE_SUB_CHANNEL3, FORCE_SUB_CHANNEL4) if chat
))

_missing = [name for name, value in (
    ("TG_BOT_TOKEN", TG_BOT_TOKEN), ("APP_ID", APP_ID), ("API_HASH", API_HASH),
    ("CHANNEL_ID", CHANNEL_ID), ("OWNER_ID", OWNER_ID), ("DB_URL", DB_URL),
) if not value]
if _missing:
    _fail("missing required setting(s): " + ", ".join(_missing)
          + ". Set them as environment variables, in a .env file, or directly in config.py.")

# Admins listed in the config (the owner and these can't be removed with /del_admin).
CONFIG_ADMINS = list(ADMINS)
if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)


LOG_FILE_NAME = "logs.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
