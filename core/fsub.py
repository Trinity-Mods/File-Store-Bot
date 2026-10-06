# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 📢 Force-sub — 0 to 4 channels / groups that users must join.
#
# Why members no longer get stuck on the "join our channels" message:
#   • every chat is checked on its own and only "not a participant" (or left / banned) counts as not joined
#   • restricted group members (muted by an anti-spam bot, etc.) still count as members
#   • a Telegram hiccup (flood wait, lost admin rights, …) never sends a member back to the join screen —
#     the user is let through and the owner gets an alert to fix the chat instead
#   • confirmed memberships are cached for a few minutes, so heavy traffic doesn't trigger flood waits

import asyncio
import html
import time
from dataclasses import dataclass

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant

from config import FORCE_SUB_CHANNELS, LOGGER, OWNER_ID

log = LOGGER(__name__)

MEMBER_CACHE_SECONDS = 300
ALERT_COOLDOWN_SECONDS = 3600
_JOINED = (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER)


@dataclass
class ForceSubChat:
    id: int
    title: str
    link: str


class SetupError(Exception):
    def __init__(self, chat, error):
        super().__init__(f"{chat}: {error}")
        self.chat = chat
        self.error = error


CHATS: list = []
_member_cache: dict = {}
_last_alert: dict = {}


async def _invite_link(client, chat) -> str:
    if chat.username:
        return f"https://t.me/{chat.username}"
    if chat.invite_link:
        return chat.invite_link
    return await client.export_chat_invite_link(chat.id)


async def setup(client) -> list:
    """Resolve the configured force-sub chats and their invite links (called once at startup)."""
    CHATS.clear()
    for ref in FORCE_SUB_CHANNELS:
        try:
            chat = await client.get_chat(ref)
            link = await _invite_link(client, chat)
        except Exception as e:
            raise SetupError(ref, e)
        if any(existing.id == chat.id for existing in CHATS):
            continue
        CHATS.append(ForceSubChat(chat.id, chat.title or str(chat.id), link))
        try:
            me = await client.get_chat_member(chat.id, "me")
            if me.status != ChatMemberStatus.ADMINISTRATOR:
                log.warning(f"I'm not an admin in force-sub chat {chat.title} ({chat.id}) — membership checks may fail there.")
        except Exception as e:
            log.warning(f"Couldn't confirm my admin rights in {chat.title} ({chat.id}): {e}")
    return CHATS


def active(settings) -> bool:
    return settings.fsub_on and bool(CHATS)


def is_fsub_chat(chat_id) -> bool:
    return any(chat.id == chat_id for chat in CHATS)


def forget(user_id: int, chat_id: int = None):
    """Drop cached memberships (used when Telegram tells us a user left a force-sub chat)."""
    for key in [key for key in _member_cache if key[0] == user_id and (chat_id is None or key[1] == chat_id)]:
        _member_cache.pop(key, None)


def _remember(key, now: float):
    if len(_member_cache) > 50000:
        for old in [k for k, expires in _member_cache.items() if expires <= now]:
            _member_cache.pop(old, None)
    _member_cache[key] = now + MEMBER_CACHE_SECONDS


async def _alert_owner(client, chat, error):
    log.error(f"Force-sub check failed in {chat.title} ({chat.id}): {error!r}")
    now = time.monotonic()
    if now - _last_alert.get(chat.id, float("-inf")) < ALERT_COOLDOWN_SECONDS:
        return
    _last_alert[chat.id] = now
    try:
        await client.send_message(
            OWNER_ID,
            f"⚠️ <b>ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴘʀᴏʙʟᴇᴍ</b>\n\n"
            f"ɪ ᴄᴏᴜʟᴅɴ'ᴛ ᴄʜᴇᴄᴋ ᴍᴇᴍʙᴇʀꜱ ᴏꜰ <b>{html.escape(chat.title)}</b> (<code>{chat.id}</code>).\n"
            f"ᴇʀʀᴏʀ: <code>{html.escape(type(error).__name__)}: {html.escape(str(error))[:300]}</code>\n\n"
            f"ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ'ᴍ ꜱᴛɪʟʟ ᴀɴ <b>ᴀᴅᴍɪɴ</b> ᴛʜᴇʀᴇ. ᴜɴᴛɪʟ ɪᴛ'ꜱ ꜰɪxᴇᴅ, ᴜꜱᴇʀꜱ ᴀʀᴇ ʟᴇᴛ ᴛʜʀᴏᴜɢʜ "
            f"ꜰᴏʀ ᴛʜɪꜱ ᴄʜᴀᴛ ꜱᴏ ɴᴏʙᴏᴅʏ ɢᴇᴛꜱ ꜱᴛᴜᴄᴋ.",
        )
    except Exception:
        pass


async def _is_member(client, chat, user_id: int) -> bool:
    key = (user_id, chat.id)
    now = time.monotonic()
    if _member_cache.get(key, 0) > now:
        return True
    try:
        member = await client.get_chat_member(chat.id, user_id)
    except UserNotParticipant:
        return False
    except FloodWait as e:
        log.warning(f"Flood wait of {e.value}s while checking {chat.id} — letting user {user_id} through.")
        return True
    except Exception as e:
        await _alert_owner(client, chat, e)
        return True
    joined = member.status in _JOINED or (member.status == ChatMemberStatus.RESTRICTED and bool(member.is_member))
    if joined:
        _remember(key, now)
    return joined


async def missing(client, user_id: int) -> list:
    """The force-sub chats this user still has to join (empty list = all joined)."""
    if not CHATS:
        return []
    results = await asyncio.gather(*(_is_member(client, chat, user_id) for chat in CHATS))
    return [chat for chat, joined in zip(CHATS, results) if not joined]

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
