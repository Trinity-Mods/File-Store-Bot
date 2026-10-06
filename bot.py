# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🤖 The bot client. On startup it checks the database channel and the force-sub chats, loads admins and
# live settings, restores pending auto-deletes and starts the health-check web server.

import sys
from datetime import datetime

from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode

from config import ADMINS, API_HASH, APP_ID, CHANNEL_ID, LOGGER, OWNER_ID, PORT, TG_BOT_TOKEN, TG_BOT_WORKERS
from core import __version__, access, delivery, fsub
from database.database import dbclient, ensure_indexes, full_adminbase, ping_database
from plugins import web_server


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
            parse_mode=ParseMode.HTML,
        )
        self.LOGGER = LOGGER
        self.username = None
        self.db_channel = None
        self.uptime = datetime.now()
        self._web_runner = None

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        log = self.LOGGER(__name__)
        usr_bot_me = await self.get_me()
        self.username = usr_bot_me.username
        self.uptime = datetime.now()

        try:
            await ping_database()
        except Exception as e:
            log.warning(e)
            log.warning("Couldn't connect to MongoDB! Double check DB_URL, and in MongoDB Atlas → Network Access "
                        "allow connections from anywhere (0.0.0.0/0).")
            sys.exit(1)
        await ensure_indexes()
        settings = await access.load()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id = db_channel.id, text = "Test Message")
            await test.delete()
        except Exception as e:
            log.warning(e)
            log.warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}")
            sys.exit(1)

        try:
            chats = await fsub.setup(self)
        except fsub.SetupError as e:
            log.warning(e.error)
            log.warning("Bot can't use a Force Sub chat! Make sure the bot is Admin there with the "
                        f"'Invite Users via Link' permission and double check the value. Current value: {e.chat}")
            sys.exit(1)

        for admin_id in await full_adminbase():
            if admin_id not in ADMINS:
                ADMINS.append(admin_id)

        restored = await delivery.restore_jobs(self)

        self._web_runner = web.AppRunner(await web_server())
        await self._web_runner.setup()
        await web.TCPSite(self._web_runner, "0.0.0.0", PORT).start()

        if settings.fsub_on and not chats:
            log.warning("Force-sub is enabled but no FORCE_SUB_CHANNEL is set — that step is skipped.")
        log.info(
            f"File Store Bot v{__version__} is live as @{self.username} | mode: {settings.mode} | "
            f"force-sub chats: {len(chats)} | referral goal: {settings.referral_count} | "
            f"auto-delete jobs restored: {restored}"
        )
        self.LOGGER(__name__).info("Bot made by @the_universal_being!")
        try:
            await self.send_message(
                chat_id=OWNER_ID,
                text=(
                    "<b>Bot has started! 😉</b>\n\n"
                    f"🔁 ᴍᴏᴅᴇ: <b>{access.MODE_LABELS[settings.mode]}</b>\n"
                    f"📢 ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴄʜᴀᴛꜱ: <b>{len(chats)}</b>\n"
                    f"👥 ʀᴇꜰᴇʀʀᴀʟ ɢᴏᴀʟ: <b>{settings.referral_count}</b>\n\n"
                    "<i>ꜱᴇɴᴅ /settings ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴀᴄᴄᴇꜱꜱ ᴍᴏᴅᴇ ʟɪᴠᴇ.</i>"
                ),
            )
        except Exception as e:
            log.warning(f"Couldn't message the owner ({e}). Send /start to the bot from the OWNER_ID account.")

    async def stop(self, *args):
        if self._web_runner:
            await self._web_runner.cleanup()
        await super().stop()
        try:
            await dbclient.close()
        except Exception:
            pass
        self.LOGGER(__name__).info("Bot stopped. Contact @the_universal_being")

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
