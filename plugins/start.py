# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🏠 /start (file links, referral links, token links) · /ch2l · /ping

import time

from pyrogram import filters
from pyrogram.errors import ListenerTimeout
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import Bot
from config import LOGGER
from core import access, pipeline, referral
from database.database import register_user
from helper_func import REF_PREFIX

log = LOGGER(__name__)


@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user = message.from_user
    if not user or user.is_bot:
        return
    payload = message.command[1] if len(message.command) > 1 else ""

    referrer = None
    if payload.startswith(REF_PREFIX) and access.current().referral_on and not (user.is_scam or user.is_fake):
        referrer = await referral.resolve_referrer(payload, user.id)
    # Atomic: a user is "new" only once, so a referral can never be counted twice.
    is_new = await register_user(user.id, referrer=referrer)
    if is_new and referrer:
        log.info(f"New user {user.id} arrived through the referral link of {referrer}")

    await pipeline.process_request(client, user, payload, reply_to=message.id)


@Bot.on_message(filters.command('ch2l') & filters.private)
async def gen_link_encoded(client: Bot, message: Message):
    try:
        code = await client.ask(
            chat_id=message.from_user.id,
            text="ᴇɴᴛᴇʀ ᴛʜᴇ ᴄᴏᴅᴇ ʜᴇʀᴇ... 🔢\n\n/cancel ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴏᴘᴇʀᴀᴛɪᴏɴ",
            timeout=60,
        )
    except ListenerTimeout:
        return await message.reply("⏳ ᴛɪᴍᴇ'ꜱ ᴜᴘ! ꜱᴇɴᴅ /ch2l ᴀɢᴀɪɴ ᴡʜᴇɴ ʏᴏᴜ'ʀᴇ ʀᴇᴀᴅʏ.", quote=True)
    if not code.text or code.text.strip() == "/cancel":
        return await code.reply("Cancelled 😉!")
    link = f"https://t.me/{client.username}?start={code.text.strip()}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🎉 Click Here ", url=link)]])
    await code.reply_text("<b>🧑‍💻 Here is your generated link</b>", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.command('ping') & filters.private)
async def check_ping_command(client: Bot, message: Message):
    start_t = time.time()
    rm = await message.reply_text("Pinging....", quote=True)
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rm.edit(f"Ping 🔥!\n{time_taken_s:.3f} ms")

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
