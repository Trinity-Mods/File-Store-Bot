# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

import asyncio
import base64
import html
import re
import time

from pyrogram import filters
from pyrogram.errors import FloodWait
from shortzy import Shortzy

from config import ADMINS, LOGGER, SHORTLINK_API_KEY, SHORTLINK_API_URL, VERIFY_EXPIRE
from database.database import db_update_verify_status, db_verify_status, get_user, set_premium

log = LOGGER(__name__)

# Start-link prefixes.
REF_PREFIX = "ref_"
VERIFY_PREFIX = "verify_"
# Safety limit: the most messages a single (batch) link can deliver.
MAX_BATCH = 1000

# Every command the bot understands — the catch-all handlers ignore these.
USER_COMMANDS = ['start', 'ping', 'ch2l', 'refer', 'referral', 'invite', 'auth', 'cancel']
ADMIN_COMMANDS = [
    'users', 'broadcast', 'batch', 'genlink', 'stats', 'sbatch', 'sgen', 'exit', 'add_admin', 'del_admin',
    'admins', 'add_prem', 'restart', 'settings', 'refstats', 'addrefs', 'auth_secret', 'deauth_secret',
]
KNOWN_COMMANDS = USER_COMMANDS + ADMIN_COMMANDS


async def _is_admin(_, __, update):
    user = getattr(update, "from_user", None)
    return bool(user) and user.id in ADMINS

# Live admin filter — it always sees admins added or removed with /add_admin and /del_admin.
admin_filter = filters.create(_is_admin, name="AdminFilter")


# ── link encoding ────────────────────────────────────────────────

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string


def referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start={REF_PREFIX}{user_id}"


# ── database channel messages ────────────────────────────────────

async def get_messages(client, message_ids):
    messages = []
    message_ids = list(message_ids)
    for i in range(0, len(message_ids), 200):
        chunk = message_ids[i:i + 200]
        try:
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=chunk)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=chunk)
        messages.extend(msgs if isinstance(msgs, list) else [msgs])
    return messages


async def get_message_id(client, message):
    """Return the DB-channel message ID from a forwarded post or a post link (0 if it isn't one)."""
    origin = message.forward_origin
    if origin:
        chat = getattr(origin, "chat", None)
        if chat and chat.id == client.db_channel.id:
            return getattr(origin, "message_id", 0) or 0
        return 0
    if message.text:
        matches = re.match(r"https?://t\.me/(?:c/)?([^/\s]+)/(\d+)", message.text.strip())
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        elif client.db_channel.username and channel_id.lower() == client.db_channel.username.lower():
            return msg_id
    return 0


# ── time & text formatting ───────────────────────────────────────

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


def get_exp_time(seconds):
    seconds = int(seconds)
    parts = []
    for name, size in (('day', 86400), ('hour', 3600), ('min', 60), ('sec', 1)):
        if seconds >= size:
            value, seconds = divmod(seconds, size)
            parts.append(f"{value} {name}{'' if value == 1 else 's'}")
    return " ".join(parts) or "0 secs"


class _KeepMissing(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def safe_format(template: str, **values) -> str:
    """Fill {placeholders} in owner-written texts without ever crashing on unknown or broken ones."""
    try:
        return template.format_map(_KeepMissing(values))
    except (ValueError, IndexError, KeyError, AttributeError) as e:
        log.warning(f"Couldn't fill placeholders in a message ({e}). Check your braces {{ }}.")
        return template


def user_placeholders(user) -> dict:
    first = html.escape(user.first_name or "")
    return {
        'first': first,
        'last': html.escape(user.last_name or ""),
        'username': f"@{user.username}" if user.username else first,
        'mention': user.mention,
        'id': user.id,
    }


def progress_bar(done: int, total: int) -> str:
    total = max(int(total), 1)
    length = total if total <= 10 else 10
    filled = min(length, round(length * min(int(done), total) / total))
    return "▰" * filled + "▱" * (length - filled)


# ── shortener ────────────────────────────────────────────────────

async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link


async def shorten(link: str) -> str:
    """Shorten a link with your shortener. If the service is down, the direct link is used instead."""
    try:
        return await get_shortlink(SHORTLINK_API_URL, SHORTLINK_API_KEY, link) or link
    except Exception as e:
        log.warning(f"Shortener failed ({e}) — sending the direct link instead.")
        return link


# ── token verification & premium ─────────────────────────────────

async def get_verify_status(user_id):
    verify = await db_verify_status(user_id)
    return verify


async def update_verify_status(user_id, verify_token="", is_verified=False, verified_time=0, link=""):
    current = await db_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['verified_time'] = verified_time
    current['link'] = link
    await db_update_verify_status(user_id, current)


def _as_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def token_is_valid(verify_status) -> bool:
    """True while a shortener token verification is still fresh (younger than VERIFY_EXPIRE)."""
    if not verify_status or not verify_status.get('is_verified'):
        return False
    return time.time() - _as_float(verify_status.get('verified_time')) <= VERIFY_EXPIRE


def premium_until(user_doc) -> float:
    if not user_doc:
        return 0.0
    until = _as_float(user_doc.get('premium_until'))
    verify = user_doc.get('verify_status') or {}
    if verify.get('is_verified'):
        # Premium given before v2 was stored as a verification time in the future.
        until = max(until, _as_float(verify.get('verified_time')))
    return until


def is_premium(user_doc) -> bool:
    return premium_until(user_doc) > time.time()


PREMIUM_PLANS = {
    1: ("7 days", 86400 * 7),
    2: ("1 month", 86400 * 31),
    3: ("3 months", 86400 * 31 * 3),
    4: ("6 months", 86400 * 31 * 6),
    5: ("1 year", 86400 * 31 * 12),
}


async def increasepremtime(user_id: int, timeforprem: int):
    """Give (or extend) premium. Returns (plan label, premium end timestamp)."""
    label, seconds = PREMIUM_PLANS[timeforprem]
    until = max(time.time(), premium_until(await get_user(user_id))) + seconds
    await set_premium(user_id, until)
    await update_verify_status(user_id, is_verified=True, verified_time=until)
    return label, until

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
