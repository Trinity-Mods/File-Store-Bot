# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🚦 The journey of every /start link:
#
#   1. 📢 force-sub   → join the channels           (ACCESS_MODE fsub / dual)
#   2. 👥 referral    → invite REFERRAL_COUNT users  (ACCESS_MODE referral / dual)
#   3. 🔗 shortener   → token or per-link shortener  (USE_SHORTLINK)
#   4. 📁 files       → delivered, then auto-deleted after TIME seconds
#
# Admins skip every step, premium users skip steps 2 and 3. When a step stops a user, the link they
# opened is remembered — finishing the step ("Try Again", "Check Progress", verifying the token) sends
# the files straight away.

import random
import string
import time
from dataclasses import dataclass, field

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    ADMINS, FORCE_PIC, LOGGER, REFERRAL_PIC, START_PIC, TUT_VID, USE_PAYMENT, USE_SHORTLINK, U_S_E_P, VERIFY_EXPIRE,
)
from core import access, delivery, fsub, referral, ui
from database.database import clear_pending, get_clicks, get_user, increment_clicks, set_pending
from helper_func import (
    MAX_BATCH, REF_PREFIX, VERIFY_PREFIX, decode, encode, get_exp_time, is_premium, shorten, token_is_valid,
    update_verify_status,
)

log = LOGGER(__name__)

# Prefixes marking a link that already went through the shortener ("sv-" keeps batch links under Telegram's
# 64-character start limit; "sav-ory-" links from older versions keep working).
_SHORTENED_PREFIXES = ("sav-ory-", "sv-")

VERIFY_PROMPT = (
    "ʏᴏᴜʀ ᴛᴏᴋᴇɴ ʜᴀꜱ ᴇxᴘɪʀᴇᴅ! ❌❌\n\n<b><u>ɴᴏᴛᴇ:</u></b> ᴛᴏ ɪᴍᴘʀᴏᴠᴇ ᴛʜᴇ ʙᴏᴛ'ꜱ ᴇꜰꜰɪᴄɪᴇɴᴄʏ, ᴏɴʟʏ ᴠᴇʀɪꜰɪᴇᴅ ᴜꜱᴇʀꜱ "
    "ᴄᴀɴ ᴀᴄᴄᴇꜱꜱ ꜰɪʟᴇꜱ. ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ɪꜱ ʀᴇQᴜɪʀᴇᴅ <u>ᴏɴᴄᴇ ᴇᴠᴇʀʏ {duration}</u> ꜰᴏʀ ᴜɴɪɴᴛᴇʀʀᴜᴘᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴀʟʟ ᴏᴜʀ ʟɪɴᴋꜱ.\n\n"
    "ᴄʟɪᴄᴋ ᴛʜᴇ 'ᴠᴇʀɪꜰʏ' ʙᴜᴛᴛᴏɴ ᴛᴏ ꜱᴛᴀʀᴛ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ. ɪꜰ ʏᴏᴜ'ʀᴇ ᴜɴꜱᴜʀᴇ ʜᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ, ᴄʟɪᴄᴋ 'ʜᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ' "
    "ʙᴜᴛᴛᴏɴ ꜰᴏʀ ᴀ ᴅᴇᴛᴀɪʟᴇᴅ ᴠɪᴅᴇᴏ ɢᴜɪᴅᴇ."
)
VERIFIED_TEXT = (
    "ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ ʙᴜᴅᴅʏ!! 🎉\n\nʏᴏᴜʀ ᴛᴏᴋᴇɴ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴄᴇɪᴠᴇᴅ ᴀɴᴅ ᴠᴇʀɪꜰɪᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!\n\n"
    "<i>ʏᴏᴜ ᴡɪʟʟ ʜᴀᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴍᴇ ꜰᴏʀ ᴛʜᴇ ɴᴇxᴛ {duration}!</i>\n\nʜᴀᴠᴇ ᴀ ɢᴏᴏᴅ ᴅᴀʏ ᴀʜᴇᴀᴅ! 🚀"
)
INVALID_TOKEN_TEXT = (
    "ᴇʜʜ, ᴛʜᴇ ᴛᴏᴋᴇɴ ʀᴇᴄᴇɪᴠᴇᴅ ɪꜱ ᴀɴ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ᴏɴᴇ. ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʙʏ ꜱᴇɴᴅɪɴɢ ᴍᴇ ᴛʜᴇ /start ᴄᴏᴍᴍᴀɴᴅ"
)
SHORTLINK_TEXT = (
    "ʜᴇʟʟᴏ ᴛʜᴇʀᴇ!\n\nᴛᴏ ɢᴇᴛ ᴛʜᴇ ꜰɪʟᴇꜱ ᴛʜᴀᴛ ʏᴏᴜ'ʀᴇ ʟᴏᴏᴋɪɴɢ ꜰᴏʀ, ʜɪᴛ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ' ʙᴜᴛᴛᴏɴ.\n"
    "ɪꜰ ʏᴏᴜ ᴅᴏɴ'ᴛ ᴋɴᴏᴡ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴛʜᴇ ꜰɪʟᴇꜱ, ʜɪᴛ ᴛʜᴇ 'ᴅᴏᴡɴʟᴏᴀᴅ ᴛᴜᴛᴏʀɪᴀʟ' ʙᴜᴛᴛᴏɴ.\n\n"
    "<blockquote>ᴛɪʟʟ ɴᴏᴡ, {clicks} ᴜꜱᴇʀꜱ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ ᴛʜᴇ ꜰɪʟᴇ(ꜱ) ᴀʟʀᴇᴀᴅʏ!</blockquote>\n\nɢᴏ ᴀʜᴇᴀᴅ ᴀɴᴅ ʟɪᴠᴇ ʏᴏᴜʀ ᴅʀᴇᴀᴍꜱ ʙᴜᴅᴅʏ!"
)


@dataclass
class Request:
    kind: str                 # "start", "file", "verify" or "invalid"
    payload: str = ""
    base: str = ""            # the decoded "get-…" part of a file link
    ids: list = field(default_factory=list)
    shortened: bool = False   # True for links that already went through the shortener
    token: str = ""

    @property
    def is_file(self) -> bool:
        return self.kind == "file"


async def parse_request(client, payload: str) -> Request:
    """Understand a /start payload. Supports every link format this bot has ever generated."""
    if not payload or payload.startswith(REF_PREFIX):
        return Request("start")
    if payload.startswith(VERIFY_PREFIX):
        return Request("verify", payload, token=payload[len(VERIFY_PREFIX):])
    try:
        decoded = await decode(payload)
    except Exception:
        return Request("invalid", payload)
    shortened = False
    for prefix in _SHORTENED_PREFIXES:
        if decoded.startswith(prefix):
            shortened, decoded = True, decoded[len(prefix):]
            break
    parts = decoded.split("-")
    if parts[0] != "get" or len(parts) not in (2, 3):
        return Request("invalid", payload)
    try:
        numbers = [int(part) // abs(client.db_channel.id) for part in parts[1:]]
    except ValueError:
        return Request("invalid", payload)
    if len(numbers) == 1:
        ids = numbers
    else:
        start, end = numbers
        step = 1 if start <= end else -1
        ids = list(range(start, end + step, step))[:MAX_BATCH]
    if not ids or min(ids) <= 0:
        return Request("invalid", payload)
    return Request("file", payload, base=decoded, ids=ids, shortened=shortened)


def _token_mode() -> bool:
    return USE_SHORTLINK and not U_S_E_P


async def send_start(client, user, reply_to=None):
    text, markup = ui.start_panel(user)
    await ui.send_panel(client, user.id, text, markup, pic=START_PIC, reply_to=reply_to)


async def _send_verify_prompt(client, user, reply_to=None):
    token = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    await update_verify_status(user.id, verify_token=token)
    link = await shorten(f"https://t.me/{client.username}?start={VERIFY_PREFIX}{token}")
    buttons = [
        [InlineKeyboardButton("ᴠᴇʀɪꜰʏ 🎀", url=link)],
        [InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ 🥲', url=TUT_VID)],
    ]
    if USE_PAYMENT:
        buttons.append([InlineKeyboardButton("ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ 💸", callback_data="buy_prem")])
    await client.send_message(
        user.id,
        VERIFY_PROMPT.format(duration=get_exp_time(VERIFY_EXPIRE)),
        reply_markup=InlineKeyboardMarkup(buttons),
        reply_to_message_id=reply_to,
    )


async def _handle_verify(client, user, doc, request, reply_to=None):
    if not _token_mode():
        return await send_start(client, user, reply_to)
    verify = doc.get("verify_status") or {}
    if not request.token or verify.get("verify_token") != request.token:
        await client.send_message(user.id, INVALID_TOKEN_TEXT, reply_to_message_id=reply_to)
        return
    # One-time token: it is cleared on use, so an old verify link can't be reused later.
    await update_verify_status(user.id, is_verified=True, verified_time=time.time())
    await client.send_message(user.id, VERIFIED_TEXT.format(duration=get_exp_time(VERIFY_EXPIRE)), reply_to_message_id=reply_to)
    pending = doc.get("pending")
    if pending:
        await process_request(client, user, pending)


async def _send_shortlink_panel(client, user, request, reply_to=None):
    shortened_payload = await encode(f"sv-{request.base}")
    clicks = await get_clicks(shortened_payload)
    link = await shorten(f"https://t.me/{client.username}?start={shortened_payload}")
    buttons = [
        [InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 🎀", url=link)],
        [InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ᴛᴜᴛᴏʀɪᴀʟ 🎥', url=TUT_VID)],
    ]
    if USE_PAYMENT:
        buttons.append([InlineKeyboardButton("ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ 💸", callback_data="buy_prem")])
    await client.send_message(
        user.id,
        SHORTLINK_TEXT.format(clicks=clicks),
        reply_markup=InlineKeyboardMarkup(buttons),
        reply_to_message_id=reply_to,
    )


async def process_request(client, user, payload: str = "", reply_to: int = None):
    """Walk a user through force-sub ➜ referral ➜ shortener ➜ files for the link they opened."""
    settings = access.current()
    request = await parse_request(client, payload)
    is_admin = user.id in ADMINS
    doc = await get_user(user.id)

    # 1️⃣ force-sub
    if not is_admin and fsub.active(settings):
        missing = await fsub.missing(client, user.id)
        if missing:
            if request.is_file:
                await set_pending(user.id, payload)
            text, markup = ui.fsub_panel(user, missing, resume=request.is_file)
            await ui.send_panel(client, user.id, text, markup, pic=FORCE_PIC, reply_to=reply_to)
            return

    # Invited users count for their referrer once they are past force-sub.
    if settings.referral_on and doc.get("ref_status") == "pending":
        await referral.confirm(client, user, settings)

    premium = is_premium(doc)

    if request.kind == "verify":
        return await _handle_verify(client, user, doc, request, reply_to)

    if not request.is_file:
        if _token_mode() and not is_admin and not premium and not token_is_valid(doc.get("verify_status")):
            return await _send_verify_prompt(client, user, reply_to)
        return await send_start(client, user, reply_to)

    # 2️⃣ referral
    if settings.referral_on and not is_admin and not premium:
        if not await referral.has_access(user.id, doc, settings):
            await set_pending(user.id, payload)
            text, markup = ui.referral_panel(client, user, doc, settings, context="gate")
            await ui.send_panel(client, user.id, text, markup, pic=REFERRAL_PIC, reply_to=reply_to)
            return

    # 3️⃣ shortener
    if USE_SHORTLINK and not is_admin and not premium:
        if _token_mode():
            if not token_is_valid(doc.get("verify_status")):
                await set_pending(user.id, payload)
                return await _send_verify_prompt(client, user, reply_to)
        elif not request.shortened:
            return await _send_shortlink_panel(client, user, request, reply_to)

    # 4️⃣ files
    if request.shortened:
        await increment_clicks(payload)
    if doc.get("pending"):
        await clear_pending(user.id)
    await delivery.deliver(client, user.id, request.ids, payload, reply_to)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
