# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 📦 File delivery & auto-delete.
# Auto-delete jobs run in the background (the bot keeps answering everyone meanwhile) and are saved in
# MongoDB, so files still get deleted on time after a restart.

import asyncio
import html
import time

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import CUSTOM_CAPTION, LOGGER, PROTECT_CONTENT, TIME
from database.database import add_delete_job, pending_delete_jobs, remove_delete_job
from helper_func import get_exp_time, get_messages, safe_format

log = LOGGER(__name__)

WAIT_TEXT = "ɢɪᴠᴇ ᴍᴇ ᴀ ꜱᴇᴄᴏɴᴅ ʜᴇʀᴇ...⏳"
ERROR_TEXT = "ᴇʜʜ, ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ! 🥲"
NOT_FOUND_TEXT = "ᴇʜʜ, ᴛʜɪꜱ ʟɪɴᴋ ɪꜱ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴛʜᴇ ꜰɪʟᴇ(ꜱ) ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ. 🥲"
REMINDER_TEXT = (
    "❗❕ <u>ʀᴇᴍɪɴᴅᴇʀ</u> ❗❕\n\n<b>ᴛʜᴇ ꜱᴇɴᴛ ꜰɪʟᴇ(ꜱ) ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ɪɴ {time}.</b>\n\n"
    "<i>ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇᴍ ᴛᴏ ʏᴏᴜʀ ᴘᴇʀꜱᴏɴᴀʟ ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰɪʀꜱᴛ ᴀɴᴅ ᴛʜᴇɴ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇᴍ ᴛʜᴇʀᴇ.</i>"
)
DELETED_TEXT = (
    "<b>ᴛʜᴇ ꜱᴇɴᴛ ꜰɪʟᴇ(ꜱ) ʜᴀᴠᴇ ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ. "
    "ʜᴏᴘᴇ ʏᴏᴜ ʜᴀᴠᴇ ꜰᴏʀᴡᴀʀᴅᴇᴅ ᴛʜᴇᴍ ᴛᴏ ʏᴏᴜʀ ᴘᴇʀꜱᴏɴᴀʟ ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ʙʏ ɴᴏᴡ! 🌚</b>"
)

_tasks = set()


def _caption(msg) -> str:
    original = msg.caption.html if msg.caption else ""
    media = msg.document or msg.video or msg.audio or msg.animation
    if CUSTOM_CAPTION and media:
        return safe_format(
            CUSTOM_CAPTION,
            previouscaption=original,
            filename=html.escape(getattr(media, "file_name", None) or ""),
        )
    return original


async def _copy(msg, chat_id: int):
    caption = _caption(msg)
    for _ in range(3):
        try:
            return await msg.copy(
                chat_id=chat_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=None,
                protect_content=PROTECT_CONTENT,
            )
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
    return None


async def deliver(client, chat_id: int, ids: list, payload: str = "", reply_to: int = None) -> int:
    """Copy the stored file(s) to the user. Returns how many messages were delivered."""
    waiting = await client.send_message(chat_id, WAIT_TEXT, reply_to_message_id=reply_to)
    try:
        messages = await get_messages(client, ids)
    except Exception as e:
        log.error(f"Couldn't fetch messages {ids[:5]}… from the DB channel: {e}")
        await waiting.edit_text(ERROR_TEXT)
        return 0

    sent = []
    for msg in messages:
        if not msg or msg.empty or msg.service:
            continue
        try:
            copied = await _copy(msg, chat_id)
        except Exception as e:
            log.warning(f"Couldn't deliver message {msg.id} to {chat_id}: {e}")
            continue
        if copied:
            sent.append(copied.id)
        await asyncio.sleep(0.5)

    try:
        await waiting.delete()
    except Exception:
        pass
    if not sent:
        await client.send_message(chat_id, NOT_FOUND_TEXT, reply_to_message_id=reply_to)
        return 0
    if TIME > 0:
        notice = await client.send_message(chat_id, REMINDER_TEXT.format(time=get_exp_time(TIME)))
        await schedule_delete(client, chat_id, sent, notice.id, payload)
    return len(sent)


def _spawn(coroutine):
    task = asyncio.create_task(coroutine)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def schedule_delete(client, chat_id: int, message_ids: list, notice_id: int = None, payload: str = ""):
    job = {
        "chat_id": chat_id,
        "message_ids": list(message_ids),
        "notice_id": notice_id,
        "payload": payload,
        "run_at": time.time() + TIME,
    }
    try:
        job["_id"] = await add_delete_job(**job)
    except Exception as e:
        log.warning(f"Couldn't save the auto-delete job (it still runs, but won't survive a restart): {e}")
    _spawn(_run_job(client, job))


async def _run_job(client, job: dict):
    delay = float(job.get("run_at") or 0) - time.time()
    if delay > 0:
        await asyncio.sleep(delay)
    chat_id = job["chat_id"]
    ids = list(job.get("message_ids") or [])
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        try:
            await client.delete_messages(chat_id, chunk)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            try:
                await client.delete_messages(chat_id, chunk)
            except Exception as error:
                log.warning(f"Auto-delete failed in {chat_id}: {error}")
        except Exception as e:
            log.warning(f"Auto-delete failed in {chat_id}: {e}")
    if job.get("notice_id"):
        markup = None
        if job.get("payload") and client.username:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton(
                "♻️ ɢᴇᴛ ꜰɪʟᴇꜱ ᴀɢᴀɪɴ", url=f"https://t.me/{client.username}?start={job['payload']}"
            )]])
        try:
            await client.edit_message_text(chat_id, job["notice_id"], DELETED_TEXT, reply_markup=markup)
        except Exception:
            pass
    if job.get("_id") is not None:
        try:
            await remove_delete_job(job["_id"])
        except Exception:
            pass


async def restore_jobs(client) -> int:
    """Re-schedule auto-delete jobs that were waiting when the bot last stopped."""
    try:
        jobs = await pending_delete_jobs()
    except Exception as e:
        log.warning(f"Couldn't load saved auto-delete jobs: {e}")
        return 0
    for job in jobs:
        _spawn(_run_job(client, job))
    return len(jobs)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
