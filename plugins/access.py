# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🔐 Force-sub & referral buttons, /refer, /settings (owner), /refstats and /addrefs (admins).

import html

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery, Message

from bot import Bot
from config import ADMINS, OWNER_ID, REFERRAL_PIC
from core import access, fsub, pipeline, referral, ui
from database.database import add_referrals, get_user, referral_counts, register_user, top_referrers
from helper_func import admin_filter


async def _resume(client, query: CallbackQuery, payload: str):
    """Remove the gate message and continue with the link the user originally opened."""
    try:
        await query.message.delete()
    except Exception:
        pass
    await pipeline.process_request(client, query.from_user, payload)


# ── force-sub: "Try Again" ───────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^fsub:(file|home)$"))
async def fsub_retry(client: Bot, query: CallbackQuery):
    user = query.from_user
    settings = access.current()
    missing = await fsub.missing(client, user.id) if fsub.active(settings) and user.id not in ADMINS else []
    if missing:
        await query.answer(f"❌ ʏᴏᴜ ꜱᴛɪʟʟ ʜᴀᴠᴇ {len(missing)} ᴄʜᴀɴɴᴇʟ(ꜱ) ʟᴇꜰᴛ ᴛᴏ ᴊᴏɪɴ!", show_alert=True)
        text, markup = ui.fsub_panel(user, missing, resume=query.data == "fsub:file")
        await ui.edit_panel(client, query.message, text, markup)
        return
    await query.answer("✅ ᴠᴇʀɪꜰɪᴇᴅ — ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴊᴏɪɴɪɴɢ!")
    payload = (await get_user(user.id)).get("pending", "") if query.data == "fsub:file" else ""
    await _resume(client, query, payload)


# ── referral: "Check Progress" / refresh ─────────────────────────

@Bot.on_callback_query(filters.regex(r"^ref:(check|info|home)$"))
async def referral_buttons(client: Bot, query: CallbackQuery):
    user = query.from_user
    settings = access.current()
    context = query.data.split(":", 1)[1]
    await register_user(user.id)
    doc = await get_user(user.id)

    if context == "check":
        if not settings.referral_on or user.id in ADMINS or await referral.has_access(user.id, doc, settings):
            await query.answer("🔓 ᴜɴʟᴏᴄᴋᴇᴅ! ꜱᴇɴᴅɪɴɢ ʏᴏᴜʀ ꜰɪʟᴇꜱ…")
            return await _resume(client, query, doc.get("pending", ""))
        doc = await get_user(user.id)
        have, need = ui.referral_progress(doc, settings)
        await query.answer(f"📊 {min(have, need)}/{need} — ɪɴᴠɪᴛᴇ {need - have} ᴍᴏʀᴇ ᴛᴏ ᴜɴʟᴏᴄᴋ!", show_alert=True)
    elif not settings.referral_on:
        return await query.answer("👥 ᴛʜᴇ ʀᴇꜰᴇʀʀᴀʟ ꜱʏꜱᴛᴇᴍ ɪꜱ ᴛᴜʀɴᴇᴅ ᴏꜰꜰ ʀɪɢʜᴛ ɴᴏᴡ.", show_alert=True)
    else:
        await query.answer()
    text, markup = ui.referral_panel(client, user, doc, settings, context=context)
    await ui.edit_panel(client, query.message, text, markup)


@Bot.on_message(filters.command(['refer', 'referral', 'invite']) & filters.private)
async def refer_command(client: Bot, message: Message):
    settings = access.current()
    if not settings.referral_on:
        return await message.reply("👥 ᴛʜᴇ ʀᴇꜰᴇʀʀᴀʟ ꜱʏꜱᴛᴇᴍ ɪꜱ ᴛᴜʀɴᴇᴅ ᴏꜰꜰ ʀɪɢʜᴛ ɴᴏᴡ.", quote=True)
    await register_user(message.from_user.id)
    doc = await get_user(message.from_user.id)
    text, markup = ui.referral_panel(client, message.from_user, doc, settings, context="info")
    await ui.send_panel(client, message.chat.id, text, markup, pic=REFERRAL_PIC, reply_to=message.id)


# ── owner: /settings ─────────────────────────────────────────────

@Bot.on_message(filters.command('settings') & filters.private & filters.user(OWNER_ID))
async def settings_command(client: Bot, message: Message):
    text, markup = ui.settings_panel(access.current())
    await message.reply(text, reply_markup=markup, quote=True)


@Bot.on_callback_query(filters.regex(r"^set:"))
async def settings_buttons(client: Bot, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("⛔ ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴄʜᴀɴɢᴇ ᴛʜᴇꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ.", show_alert=True)
    action = query.data.split(":", 1)[1]
    settings = access.current()

    if action == "close":
        await query.answer()
        return await query.message.delete()
    if action == "noop":
        return await query.answer(f"🎯 ᴜꜱᴇʀꜱ ᴍᴜꜱᴛ ɪɴᴠɪᴛᴇ {settings.referral_count} ɴᴇᴡ ᴜꜱᴇʀꜱ.")
    if action == "fsub":
        if not settings.fsub_on and not fsub.CHATS:
            return await query.answer(
                "⚠️ ɴᴏ ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴄʜᴀɴɴᴇʟꜱ ᴀʀᴇ ꜱᴇᴛ. ᴀᴅᴅ FORCE_SUB_CHANNEL ɪɴ ᴛʜᴇ ᴄᴏɴꜰɪɢ ꜰɪʀꜱᴛ, ᴛʜᴇɴ ʀᴇꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ.",
                show_alert=True,
            )
        settings = await access.update(mode=access.mode_for(not settings.fsub_on, settings.referral_on))
    elif action == "ref":
        settings = await access.update(mode=access.mode_for(settings.fsub_on, not settings.referral_on))
    elif action in ("inc", "dec"):
        step = 1 if action == "inc" else -1
        settings = await access.update(referral_count=max(1, min(1000, settings.referral_count + step)))
    elif action == "exp":
        settings = await access.update(referral_expire=ui.next_duration(settings.referral_expire))
    elif action == "reset":
        settings = await access.reset()
    await query.answer("✅ ꜱᴀᴠᴇᴅ")
    text, markup = ui.settings_panel(settings)
    await ui.edit_panel(client, query.message, text, markup)


# ── admins: /refstats · /addrefs ─────────────────────────────────

@Bot.on_message(filters.command('refstats') & filters.private & admin_filter)
async def referral_stats(client: Bot, message: Message):
    counts = await referral_counts()
    top = await top_referrers(10)
    names = {}
    try:
        users = await client.get_users([doc['_id'] for doc in top]) if top else []
        names = {u.id: html.escape(u.first_name or str(u.id)) for u in (users if isinstance(users, list) else [users])}
    except Exception:
        pass
    medals = ["🥇", "🥈", "🥉"]
    lines = [
        f"{medals[i] if i < 3 else '🏅'} <a href='tg://user?id={doc['_id']}'>{names.get(doc['_id'], doc['_id'])}</a>"
        f" — <b>{doc.get('referrals', 0)}</b>"
        for i, doc in enumerate(top)
    ]
    settings = access.current()
    text = (
        "<b>👥 ʀᴇꜰᴇʀʀᴀʟ ꜱᴛᴀᴛꜱ</b>\n\n"
        f"✅ ᴄᴏɴꜰɪʀᴍᴇᴅ ʀᴇꜰᴇʀʀᴀʟꜱ: <b>{counts['confirmed']}</b>\n"
        f"⏳ ᴡᴀɪᴛɪɴɢ (ɴᴏᴛ ᴊᴏɪɴᴇᴅ ʏᴇᴛ): <b>{counts['pending']}</b>\n"
        f"🎯 ɢᴏᴀʟ: <b>{settings.referral_count}</b> · ꜱʏꜱᴛᴇᴍ: <b>{'ᴏɴ' if settings.referral_on else 'ᴏꜰꜰ'}</b>\n\n"
        "<b>🏆 ᴛᴏᴘ ʀᴇꜰᴇʀʀᴇʀꜱ</b>\n" + ("\n".join(lines) if lines else "<i>ɴᴏ ʀᴇꜰᴇʀʀᴀʟꜱ ʏᴇᴛ.</i>")
    )
    await message.reply(text, quote=True, disable_web_page_preview=True)


@Bot.on_message(filters.command('addrefs') & filters.private & admin_filter)
async def add_referrals_command(client: Bot, message: Message):
    args = message.command[1:]
    try:
        user_id, amount = int(args[0]), int(args[1])
    except (IndexError, ValueError):
        return await message.reply(
            "<b>ᴜꜱᴀɢᴇ:</b> <code>/addrefs USER_ID AMOUNT</code>\n"
            "ᴇxᴀᴍᴘʟᴇ: <code>/addrefs 123456789 2</code> (ᴜꜱᴇ ᴀ ɴᴇɢᴀᴛɪᴠᴇ ᴀᴍᴏᴜɴᴛ ᴛᴏ ʀᴇᴍᴏᴠᴇ)",
            quote=True,
        )
    doc = await add_referrals(user_id, amount)
    if not doc:
        return await message.reply("❌ ᴛʜɪꜱ ᴜꜱᴇʀ ʜᴀꜱɴ'ᴛ ꜱᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ʏᴇᴛ.", quote=True)
    await message.reply(
        f"✅ ᴅᴏɴᴇ! <code>{user_id}</code> ɴᴏᴡ ʜᴀꜱ <b>{doc.get('referrals', 0)}</b> ʀᴇꜰᴇʀʀᴀʟ(ꜱ) "
        f"(<b>{doc.get('ref_balance', 0)}</b> ᴀᴠᴀɪʟᴀʙʟᴇ).",
        quote=True,
    )
    if amount > 0:
        try:
            await client.send_message(user_id, f"🎁 ᴀɴ ᴀᴅᴍɪɴ ᴄʀᴇᴅɪᴛᴇᴅ ʏᴏᴜ <b>+{amount}</b> ʀᴇꜰᴇʀʀᴀʟ(ꜱ)! ꜱᴇɴᴅ /refer ᴛᴏ ꜱᴇᴇ ʏᴏᴜʀ ᴘʀᴏɢʀᴇꜱꜱ.")
        except Exception:
            pass


# ── keep force-sub checks fresh when someone leaves a channel ────

async def _in_fsub_chat(_, __, update):
    return bool(update.chat) and fsub.is_fsub_chat(update.chat.id)


@Bot.on_chat_member_updated(filters.create(_in_fsub_chat))
async def fsub_member_left(client: Bot, update):
    member = update.new_chat_member or update.old_chat_member
    if not member or not member.user:
        return
    new = update.new_chat_member
    still_member = bool(new) and (
        new.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER)
        or (new.status == ChatMemberStatus.RESTRICTED and bool(new.is_member))
    )
    if not still_member:
        fsub.forget(member.user.id, update.chat.id)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
