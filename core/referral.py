# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 👥 Referral system
#
#   1. Every user has a personal link:  https://t.me/<bot>?start=ref_<their id>
#   2. Someone opens it → if they have NEVER used the bot before, they are saved as "invited by" that user.
#      Old users, the referrer themselves, scam / fake accounts and links of unknown users are ignored.
#   3. The referral is confirmed — and the referrer credited exactly once — when the new user gets past
#      force-sub (right away when force-sub is off). The referrer gets a live progress notification.
#   4. Reaching REFERRAL_COUNT unlocks files forever, or for REFERRAL_EXPIRE seconds per goal.

import time

from config import LOGGER
from core import ui
from database.database import confirm_referral, consume_referrals, present_user
from helper_func import REF_PREFIX

log = LOGGER(__name__)


def parse(payload: str):
    """The referrer's user ID from a ref_<id> start link, or None."""
    if not payload or not payload.startswith(REF_PREFIX):
        return None
    value = payload[len(REF_PREFIX):]
    return int(value) if value.isdigit() else None


async def resolve_referrer(payload: str, user_id: int):
    referrer = parse(payload)
    if not referrer or referrer == user_id:
        return None
    return referrer if await present_user(referrer) else None


async def has_access(user_id: int, doc: dict, settings) -> bool:
    """Has this user reached the referral goal? (With a time limit this may spend referrals to unlock.)"""
    need = settings.referral_count
    if settings.referral_expire <= 0:
        return int(doc.get("referrals") or 0) >= need
    if float(doc.get("ref_unlock_until") or 0) > time.time():
        return True
    return await consume_referrals(user_id, need, settings.referral_expire)


async def confirm(client, user, settings):
    """Confirm this user's pending referral (if any) and notify the person who invited them."""
    referrer_doc = await confirm_referral(user.id)
    if not referrer_doc:
        return
    log.info(f"Referral confirmed: {user.id} → credited to {referrer_doc['_id']}")
    text, markup = ui.referral_notice(client, user, referrer_doc, settings)
    try:
        await client.send_message(referrer_doc["_id"], text, reply_markup=markup, disable_web_page_preview=True)
    except Exception as e:
        log.info(f"Couldn't notify referrer {referrer_doc['_id']}: {e}")

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
