# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🎨 Panels — the texts and buttons of every screen, and the helpers that send / edit them.
# Screens can carry a picture (START_PIC, FORCE_PIC, REFERRAL_PIC): it can be a link, a Telegram
# file_id or a local file. If a picture can't be sent the bot falls back to plain text, so a bad
# link never breaks /start.

import asyncio
import html
import random
import re
import time
from urllib.parse import quote

from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    FORCE_MSG, LOGGER, OWNER_TAG, PRICE1, PRICE2, PRICE3, PRICE4, PRICE5, REFERRAL_MSG,
    REFERRAL_SHARE_TEXT, SCREENSHOT_URL, START_MSG, UPI_ID, UPI_IMAGE_URL, USE_PAYMENT,
)
from core import __version__, access, fsub
from helper_func import get_exp_time, progress_bar, referral_link, safe_format, user_placeholders

log = LOGGER(__name__)

REPO_URL = "https://github.com/Trinity-Mods/File-Store-Bot"
CAPTION_LIMIT = 1024
UNLOCK_DURATIONS = [0, 3600, 6 * 3600, 12 * 3600, 86400, 3 * 86400, 7 * 86400, 30 * 86400]

_photo_cache = {}


# ── sending & editing panels ─────────────────────────────────────

def _visible_length(text: str) -> int:
    return len(html.unescape(re.sub(r"<[^>]+>", "", text or "")))


async def _send_photo(client, chat_id, photo, text, markup, reply_to):
    try:
        return await client.send_photo(chat_id, photo, caption=text, reply_markup=markup, reply_to_message_id=reply_to)
    except FloodWait as e:
        await asyncio.sleep(e.value + 1)
        return await client.send_photo(chat_id, photo, caption=text, reply_markup=markup, reply_to_message_id=reply_to)


async def send_panel(client, chat_id, text, markup=None, pic="", reply_to=None):
    """Send a screen, with a picture when one is configured (one is picked at random if several)."""
    sources = pic.split() if pic else []
    if sources and _visible_length(text) > CAPTION_LIMIT:
        log.warning(f"Message is longer than {CAPTION_LIMIT} characters, so it's sent without its picture.")
        sources = []
    if sources:
        source = random.choice(sources)
        attempts = [_photo_cache[source], source] if source in _photo_cache else [source]
        error = None
        for photo in attempts:
            try:
                sent = await _send_photo(client, chat_id, photo, text, markup, reply_to)
            except Exception as e:
                _photo_cache.pop(source, None)
                error = e
                continue
            if sent and sent.photo:
                _photo_cache[source] = sent.photo.file_id
            return sent
        log.warning(f"Couldn't send the picture {source!r} ({error}) — sent the text without it.")
    return await client.send_message(chat_id, text, reply_markup=markup, disable_web_page_preview=True, reply_to_message_id=reply_to)


async def edit_panel(client, message, text, markup=None):
    """Edit a screen in place — works for both text messages and pictures with captions."""
    try:
        if message.media:
            if _visible_length(text) <= CAPTION_LIMIT:
                return await message.edit_caption(text, reply_markup=markup)
            await message.delete()
            return await client.send_message(message.chat.id, text, reply_markup=markup, disable_web_page_preview=True)
        return await message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except MessageNotModified:
        return message


def _button(text, **kwargs):
    return InlineKeyboardButton(text, **kwargs)


def close_button():
    return _button("🔒 ᴄʟᴏꜱᴇ", callback_data="close")


def back_button():
    return _button("⬅️ ʙᴀᴄᴋ", callback_data="home")


# ── start / about / premium ──────────────────────────────────────

def start_panel(user):
    settings = access.current()
    text = safe_format(START_MSG, **user_placeholders(user))
    rows = [[_button("💝 ᴛʀɪɴɪᴛʏ ᴍᴏᴅꜱ", url="https://t.me/trinityXmods")]]
    if settings.referral_on:
        rows.append([_button("👥 ʀᴇꜰᴇʀ & ᴜɴʟᴏᴄᴋ ꜰɪʟᴇꜱ", callback_data="ref:home")])
    row = [_button("💸 ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_prem")] if USE_PAYMENT else []
    row.append(_button("😊 ᴀʙᴏᴜᴛ ᴍᴇ", callback_data="about"))
    rows.append(row)
    rows.append([_button("🔄️ ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ", url=REPO_URL), close_button()])
    return text, InlineKeyboardMarkup(rows)


def about_panel():
    text = (
        f"<b>○ ʙᴏᴛ: <a href='{REPO_URL}'>File Store Bot v{__version__}</a>\n"
        "○ More Bots: <a href='https://github.com/Trinity-Mods'>Trinity Mods</a>\n"
        "○ Language: <a href='https://www.python.org/'>Python 3</a>\n"
        "○ Framework: <a href='https://github.com/Mayuri-Chan/pyrofork'>Pyrofork</a>\n"
        "○ Fueled By: <a href='https://t.me/infohub_updates'>InfoHub Updates</a>\n"
        "○ Server: <a href='https://www.ubuntu.com/'>Private VPS</a></b>"
    )
    return text, InlineKeyboardMarkup([[back_button(), close_button()]])


def premium_panel(user):
    text = (
        f"👋 {user.mention}, here are our Prime Membership plans – {PRICE1}/7 days, {PRICE2}/1 month, "
        f"{PRICE3}/3 months, {PRICE4}/6 months, {PRICE5}/1 year | 💵 UPI ID: <code>{UPI_ID}</code> | "
        f"📸 <a href='{UPI_IMAGE_URL}'>Scan QR Code</a> to pay | 🧾 After payment, send your screenshot | "
        f"💬 For help or alternative payment methods, contact @{OWNER_TAG}"
    )
    rows = [
        [_button("ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ 📸", url=SCREENSHOT_URL)],
        [back_button(), close_button()],
    ]
    return text, InlineKeyboardMarkup(rows)


# ── force-sub ────────────────────────────────────────────────────

def fsub_panel(user, missing, resume: bool):
    """The "join our channels" screen — it only lists the chats this user still has to join."""
    text = safe_format(FORCE_MSG, **user_placeholders(user))
    text += (
        f"\n\n<blockquote>📢 ᴄʜᴀɴɴᴇʟꜱ ʟᴇꜰᴛ ᴛᴏ ᴊᴏɪɴ: <b>{len(missing)}/{len(fsub.CHATS)}</b>\n"
        "✅ ᴊᴏɪɴᴇᴅ ᴛʜᴇᴍ ᴀʟʟ? ᴛᴀᴘ <b>ᴛʀʏ ᴀɢᴀɪɴ</b> ʙᴇʟᴏᴡ.</blockquote>"
    )
    rows = []
    for chat in missing:
        title = chat.title if len(chat.title) <= 28 else chat.title[:27] + "…"
        rows.append([_button(f"📢 ᴊᴏɪɴ • {title}", url=chat.link)])
    rows.append([_button("🔄 ᴛʀʏ ᴀɢᴀɪɴ", callback_data="fsub:file" if resume else "fsub:home")])
    return text, InlineKeyboardMarkup(rows)


# ── referral ─────────────────────────────────────────────────────

def referral_progress(doc, settings):
    """(referrals that count towards the goal, goal)."""
    field = "ref_balance" if settings.referral_expire > 0 else "referrals"
    return int(doc.get(field) or 0), settings.referral_count


def _unlock_text(settings) -> str:
    if settings.referral_expire <= 0:
        return "ʟɪꜰᴇᴛɪᴍᴇ ᴀᴄᴄᴇꜱꜱ ♾️"
    return f"{get_exp_time(settings.referral_expire)} ᴏꜰ ᴀᴄᴄᴇꜱꜱ ᴘᴇʀ ɢᴏᴀʟ"


def share_url(link: str) -> str:
    return f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(REFERRAL_SHARE_TEXT, safe='')}"


def referral_panel(client, user, doc, settings, context: str = "gate"):
    """Referral screen. context: "gate" (a file is locked), "info" (/refer) or "home" (from the start menu)."""
    have, need = referral_progress(doc, settings)
    remaining = max(need - have, 0)
    link = referral_link(client.username, user.id)
    if context == "gate":
        intro = safe_format(REFERRAL_MSG, **user_placeholders(user), required=need, count=have, remaining=remaining)
    else:
        intro = f"<b>👥 ʀᴇꜰᴇʀ & ᴜɴʟᴏᴄᴋ</b>\n\nɪɴᴠɪᴛᴇ <b>{need}</b> ɴᴇᴡ ᴜꜱᴇʀꜱ ᴡɪᴛʜ ʏᴏᴜʀ ʟɪɴᴋ ᴛᴏ ᴜɴʟᴏᴄᴋ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴛʜɪꜱ ʙᴏᴛ."

    status = [f"📊 ᴘʀᴏɢʀᴇꜱꜱ: {progress_bar(have, need)} <b>{min(have, need)}/{need}</b>"]
    status.append(f"🎯 ʀᴇᴍᴀɪɴɪɴɢ: <b>{remaining}</b>" if remaining else "✅ <b>ɢᴏᴀʟ ʀᴇᴀᴄʜᴇᴅ!</b>")
    status.append(f"👥 ᴛᴏᴛᴀʟ ɪɴᴠɪᴛᴇᴅ: <b>{int(doc.get('referrals') or 0)}</b>")
    status.append(f"🎁 ʀᴇᴡᴀʀᴅ: {_unlock_text(settings)}")
    unlocked_until = float(doc.get("ref_unlock_until") or 0)
    if settings.referral_expire > 0 and unlocked_until > time.time():
        status.append(f"🔓 ᴜɴʟᴏᴄᴋᴇᴅ ꜰᴏʀ ᴀɴᴏᴛʜᴇʀ <b>{get_exp_time(unlocked_until - time.time())}</b>")

    rule = "ᴏɴʟʏ ɴᴇᴡ ᴜꜱᴇʀꜱ ᴡʜᴏ ʜᴀᴠᴇ ɴᴇᴠᴇʀ ᴜꜱᴇᴅ ᴛʜɪꜱ ʙᴏᴛ ᴀʀᴇ ᴄᴏᴜɴᴛᴇᴅ"
    if fsub.active(settings):
        rule += " — ᴀɴᴅ ᴛʜᴇʏ ᴍᴜꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟꜱ"
    text = (
        f"{intro}\n\n<blockquote>" + "\n".join(status) + "</blockquote>\n\n"
        f"🔗 <b>ʏᴏᴜʀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ:</b>\n<code>{link}</code>\n\n<i>⚠️ {rule}.</i>"
    )

    rows = [[_button("📤 ꜱʜᴀʀᴇ ʟɪɴᴋ", url=share_url(link))]]
    if context == "gate":
        rows[0].append(_button("🔄 ᴄʜᴇᴄᴋ ᴘʀᴏɢʀᴇꜱꜱ", callback_data="ref:check"))
        if USE_PAYMENT:
            rows.append([_button("💎 ꜱᴋɪᴘ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_prem")])
    elif context == "home":
        rows[0].append(_button("🔄 ʀᴇꜰʀᴇꜱʜ", callback_data="ref:home"))
        rows.append([back_button(), close_button()])
    else:
        rows[0].append(_button("🔄 ʀᴇꜰʀᴇꜱʜ", callback_data="ref:info"))
    return text, InlineKeyboardMarkup(rows)


def referral_notice(client, invitee, referrer_doc, settings):
    """Message sent to a referrer the moment one of their invites is confirmed."""
    have, need = referral_progress(referrer_doc, settings)
    name = html.escape(invitee.first_name or "ꜱᴏᴍᴇᴏɴᴇ")
    text = (
        "🎉 <b>ɴᴇᴡ ʀᴇꜰᴇʀʀᴀʟ!</b>\n\n"
        f"<b>{name}</b> ᴊᴜꜱᴛ ᴊᴏɪɴᴇᴅ ᴜꜱɪɴɢ ʏᴏᴜʀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.\n\n"
        f"📊 ᴘʀᴏɢʀᴇꜱꜱ: {progress_bar(have, need)} <b>{min(have, need)}/{need}</b>"
    )
    markup = None
    if have >= need:
        text += "\n\n🔓 <b>ɢᴏᴀʟ ʀᴇᴀᴄʜᴇᴅ!</b> ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜɴʟᴏᴄᴋ ꜰɪʟᴇꜱ"
        text += "." if settings.referral_expire <= 0 else f" ꜰᴏʀ {get_exp_time(settings.referral_expire)}."
        pending = referrer_doc.get("pending")
        if pending:
            markup = InlineKeyboardMarkup([[_button("📥 ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ", url=f"https://t.me/{client.username}?start={pending}")]])
    else:
        text += f"\n🎯 ᴊᴜꜱᴛ <b>{need - have}</b> ᴍᴏʀᴇ ᴛᴏ ɢᴏ!"
    return text, markup


# ── owner settings panel (/settings) ─────────────────────────────

def _duration_label(seconds: int) -> str:
    return "ʟɪꜰᴇᴛɪᴍᴇ ♾️" if seconds <= 0 else get_exp_time(seconds)


def next_duration(seconds: int) -> int:
    later = [value for value in UNLOCK_DURATIONS if value > seconds]
    return later[0] if later else UNLOCK_DURATIONS[0]


def settings_panel(settings):
    on, off = "✅ ᴏɴ", "❌ ᴏꜰꜰ"
    channels = len(fsub.CHATS)
    steps = ["🔗 ꜰɪʟᴇ ʟɪɴᴋ"]
    if fsub.active(settings):
        steps.append("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟꜱ")
    if settings.referral_on:
        steps.append(f"👥 ɪɴᴠɪᴛᴇ {settings.referral_count}")
    steps.append("📁 ꜰɪʟᴇꜱ")
    text = (
        "<b>⚙️ ᴀᴄᴄᴇꜱꜱ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ</b>\n\n"
        f"🔁 ᴍᴏᴅᴇ: <b>{access.MODE_LABELS[settings.mode]}</b>\n"
        f"📢 ꜰᴏʀᴄᴇ-ꜱᴜʙ: <b>{on if settings.fsub_on else off}</b> · {channels} ᴄʜᴀᴛ(ꜱ) ɪɴ ᴄᴏɴꜰɪɢ\n"
        f"👥 ʀᴇꜰᴇʀʀᴀʟ: <b>{on if settings.referral_on else off}</b> · ɢᴏᴀʟ <b>{settings.referral_count}</b>\n"
        f"⏳ ᴜɴʟᴏᴄᴋ ʟᴀꜱᴛꜱ: <b>{_duration_label(settings.referral_expire)}</b>\n\n"
        f"<blockquote>{' ➜ '.join(steps)}</blockquote>\n"
    )
    if settings.fsub_on and not channels:
        text += "\n⚠️ <i>ꜰᴏʀᴄᴇ-ꜱᴜʙ ɪꜱ ᴏɴ ʙᴜᴛ ɴᴏ ᴄʜᴀɴɴᴇʟꜱ ᴀʀᴇ ꜱᴇᴛ — ᴀᴅᴅ FORCE_SUB_CHANNEL ɪɴ ᴛʜᴇ ᴄᴏɴꜰɪɢ.</i>\n"
    text += "\n<i>ᴄʜᴀɴɢᴇꜱ ᴀᴘᴘʟʏ ɪɴꜱᴛᴀɴᴛʟʏ ᴀɴᴅ ꜱᴜʀᴠɪᴠᴇ ʀᴇꜱᴛᴀʀᴛꜱ.</i>"
    if settings.overrides:
        text += "\n<i>✏️ ꜱᴏᴍᴇ ᴠᴀʟᴜᴇꜱ ᴅɪꜰꜰᴇʀ ꜰʀᴏᴍ config.py — ᴛᴀᴘ ʀᴇꜱᴇᴛ ᴛᴏ ᴜɴᴅᴏ.</i>"

    rows = [
        [
            _button(f"📢 ꜰᴏʀᴄᴇ-ꜱᴜʙ: {'✅' if settings.fsub_on else '❌'}", callback_data="set:fsub"),
            _button(f"👥 ʀᴇꜰᴇʀʀᴀʟ: {'✅' if settings.referral_on else '❌'}", callback_data="set:ref"),
        ],
        [
            _button("➖", callback_data="set:dec"),
            _button(f"🎯 ɢᴏᴀʟ: {settings.referral_count}", callback_data="set:noop"),
            _button("➕", callback_data="set:inc"),
        ],
        [_button(f"⏳ ᴜɴʟᴏᴄᴋ: {_duration_label(settings.referral_expire)}", callback_data="set:exp")],
        [_button("♻️ ʀᴇꜱᴇᴛ ᴛᴏ ᴄᴏɴꜰɪɢ", callback_data="set:reset"), _button("✖️ ᴄʟᴏꜱᴇ", callback_data="set:close")],
    ]
    return text, InlineKeyboardMarkup(rows)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
