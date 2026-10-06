# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 📊 /stats (uptime) and the auto-reply for normal users who message the bot directly.

from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from bot import Bot
from config import BOT_STATS_TEXT, USER_REPLY_TEXT
from helper_func import KNOWN_COMMANDS, admin_filter, get_readable_time, safe_format


@Bot.on_message(filters.command('stats') & admin_filter)
async def stats(bot: Bot, message: Message):
    delta = datetime.now() - bot.uptime
    uptime = get_readable_time(int(delta.total_seconds()))
    await message.reply(safe_format(BOT_STATS_TEXT, uptime=uptime))


@Bot.on_message(filters.private & ~admin_filter & ~filters.command(KNOWN_COMMANDS))
async def useless(_, message: Message):
    if USER_REPLY_TEXT:
        await message.reply(USER_REPLY_TEXT)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
