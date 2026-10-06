# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🗄️ MongoDB layer — built on PyMongo's native asyncio client (the successor of Motor).
#
#   users        → every user of the bot, their token / premium status and referral stats
#   admins       → admins added with /add_admin
#   links        → click counters for shortener links
#   settings     → access settings changed live with /settings
#   auto_delete  → pending auto-delete jobs, so deletions survive restarts

import time

from pymongo import AsyncMongoClient, DESCENDING, ReturnDocument

from config import ADMINS, DB_URL, DB_NAME, LOGGER

log = LOGGER(__name__)

dbclient = AsyncMongoClient(DB_URL, appname="FileStoreBot")
database = dbclient[DB_NAME]

user_data = database['users']
admin_data = database['admins']
link_data = database['links']
settings_data = database['settings']
delete_queue = database['auto_delete']

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}


def _now() -> float:
    return time.time()


async def ping_database():
    """Raises if MongoDB can't be reached (wrong DB_URL, network access not allowed, …)."""
    await dbclient.admin.command("ping")


async def ensure_indexes():
    """Create the indexes used by referral stats, click counters and auto-delete jobs."""
    for collection, keys, options in (
        (user_data, [("referrals", DESCENDING)], {}),
        (user_data, [("ref_status", 1)], {"sparse": True}),
        (link_data, [("hash", 1)], {}),
        (delete_queue, [("run_at", 1)], {}),
    ):
        try:
            await collection.create_index(keys, **options)
        except Exception as e:
            log.warning(f"Couldn't create index {keys} on {collection.name}: {e}")


# ── users ────────────────────────────────────────────────────────

async def register_user(user_id: int, referrer: int = None) -> bool:
    """Add the user if they are new. Returns True only for brand-new users.

    The check-and-insert is one atomic upsert, so even if a user taps /start many times at once
    they can only ever be "new" — and credited to a referrer — a single time.
    """
    on_insert = {
        'verify_status': dict(default_verify),
        'joined_at': _now(),
        'referrals': 0,
        'ref_balance': 0,
    }
    if referrer:
        on_insert['referred_by'] = referrer
        on_insert['ref_status'] = "pending"
    result = await user_data.update_one(
        {'_id': user_id},
        {'$setOnInsert': on_insert, '$set': {'last_seen': _now()}, '$unset': {'blocked': ""}},
        upsert=True,
    )
    return result.upserted_id is not None


async def add_user(user_id: int):
    await register_user(user_id)


async def present_user(user_id: int) -> bool:
    found = await user_data.find_one({'_id': user_id}, {'_id': 1})
    return bool(found)


async def get_user(user_id: int) -> dict:
    return await user_data.find_one({'_id': user_id}) or {}


async def full_userbase(include_blocked: bool = False) -> list:
    query = {} if include_blocked else {'blocked': {'$ne': True}}
    return [doc['_id'] async for doc in user_data.find(query, {'_id': 1})]


async def mark_blocked(user_id: int):
    """Flag users who blocked the bot. Their data (and referrals) is kept in case they come back."""
    await user_data.update_one({'_id': user_id}, {'$set': {'blocked': True}})


async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})


async def user_counts() -> dict:
    total = await user_data.count_documents({})
    blocked = await user_data.count_documents({'blocked': True})
    return {'total': total, 'blocked': blocked, 'active': total - blocked}


async def set_pending(user_id: int, payload: str):
    """Remember the file link a user is trying to open, so it can be delivered once they unlock it."""
    await user_data.update_one({'_id': user_id}, {'$set': {'pending': payload}})


async def clear_pending(user_id: int):
    await user_data.update_one({'_id': user_id}, {'$unset': {'pending': ""}})


# ── token verification & premium ─────────────────────────────────

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id}, {'verify_status': 1})
    if user:
        return {**default_verify, **(user.get('verify_status') or {})}
    return dict(default_verify)


async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}}, upsert=True)


async def set_premium(user_id: int, until: float):
    await user_data.update_one({'_id': user_id}, {'$set': {'premium_until': until}}, upsert=True)


# ── referrals ────────────────────────────────────────────────────

async def confirm_referral(user_id: int):
    """Turn a user's pending referral into a confirmed one and credit their referrer — exactly once.

    Returns the referrer's updated document, or None when there was nothing to confirm.
    """
    invitee = await user_data.find_one_and_update(
        {'_id': user_id, 'ref_status': "pending"},
        {'$set': {'ref_status': "confirmed", 'ref_confirmed_at': _now()}},
        projection={'referred_by': 1},
    )
    if not invitee or not invitee.get('referred_by'):
        return None
    return await user_data.find_one_and_update(
        {'_id': invitee['referred_by']},
        {'$inc': {'referrals': 1, 'ref_balance': 1}},
        return_document=ReturnDocument.AFTER,
    )


async def consume_referrals(user_id: int, required: int, duration: int) -> bool:
    """Spend `required` referrals to unlock access for `duration` seconds (atomic, never double-spends)."""
    now = _now()
    result = await user_data.update_one(
        {'_id': user_id, 'ref_balance': {'$gte': required}, 'ref_unlock_until': {'$not': {'$gt': now}}},
        {'$inc': {'ref_balance': -required}, '$set': {'ref_unlock_until': now + duration}},
    )
    return result.modified_count == 1


async def add_referrals(user_id: int, amount: int):
    """Manually credit (or remove, with a negative amount) referrals. Never goes below zero."""
    doc = await user_data.find_one_and_update(
        {'_id': user_id},
        {'$inc': {'referrals': amount, 'ref_balance': amount}},
        return_document=ReturnDocument.AFTER,
    )
    if doc:
        fix = {key: 0 for key in ('referrals', 'ref_balance') if doc.get(key, 0) < 0}
        if fix:
            await user_data.update_one({'_id': user_id}, {'$set': fix})
            doc.update(fix)
    return doc


async def top_referrers(limit: int = 10) -> list:
    cursor = user_data.find({'referrals': {'$gt': 0}}, {'referrals': 1}).sort('referrals', DESCENDING).limit(limit)
    return [doc async for doc in cursor]


async def referral_counts() -> dict:
    return {
        'confirmed': await user_data.count_documents({'ref_status': "confirmed"}),
        'pending': await user_data.count_documents({'ref_status': "pending"}),
    }


# ── admins ───────────────────────────────────────────────────────
# Older versions stored admin IDs as text, so both forms are matched.

def _id_forms(user_id) -> list:
    return [int(user_id), str(int(user_id))]


async def present_admin(user_id) -> bool:
    found = await admin_data.find_one({'_id': {'$in': _id_forms(user_id)}})
    return bool(found)


async def add_admin(user_id):
    user_id = int(user_id)
    await admin_data.update_one({'_id': user_id}, {'$setOnInsert': {'added_at': _now()}}, upsert=True)
    if user_id not in ADMINS:
        ADMINS.append(user_id)


async def del_admin(user_id):
    user_id = int(user_id)
    await admin_data.delete_many({'_id': {'$in': _id_forms(user_id)}})
    while user_id in ADMINS:
        ADMINS.remove(user_id)


async def full_adminbase() -> list:
    ids = []
    async for doc in admin_data.find({}, {'_id': 1}):
        try:
            ids.append(int(doc['_id']))
        except (TypeError, ValueError):
            continue
    return ids


# ── shortener click counters ─────────────────────────────────────

async def increment_clicks(hash: str):
    await link_data.update_one({'hash': hash}, {'$inc': {'clicks': 1}}, upsert=True)


async def get_clicks(hash: str) -> int:
    data = await link_data.find_one({'hash': hash})
    return int(data.get('clicks', 0)) if data else 0


# ── live settings (/settings) ────────────────────────────────────

async def get_settings(key: str) -> dict:
    return await settings_data.find_one({'_id': key}) or {}


async def save_settings(key: str, values: dict):
    await settings_data.update_one({'_id': key}, {'$set': values}, upsert=True)


async def clear_settings(key: str):
    await settings_data.delete_one({'_id': key})


# ── auto-delete jobs ─────────────────────────────────────────────

async def add_delete_job(chat_id: int, message_ids: list, run_at: float, notice_id: int = None, payload: str = ""):
    result = await delete_queue.insert_one({
        'chat_id': chat_id,
        'message_ids': list(message_ids),
        'notice_id': notice_id,
        'payload': payload,
        'run_at': run_at,
    })
    return result.inserted_id


async def remove_delete_job(job_id):
    await delete_queue.delete_one({'_id': job_id})


async def pending_delete_jobs() -> list:
    return [doc async for doc in delete_queue.find({})]

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
