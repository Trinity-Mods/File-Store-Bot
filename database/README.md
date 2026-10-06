# 🗄️ database — MongoDB storage

[`database.py`](database.py) talks to MongoDB using PyMongo's native asyncio client (the successor of
Motor). Collections are created automatically — just set `DB_URL` and `DB_NAME` in the config.

| Collection | Stores |
| --- | --- |
| `users` | Every user: join date, token / premium status, referral stats, and the file link they're unlocking |
| `admins` | Admins added with `/add_admin` |
| `links` | Click counters for shortener links |
| `settings` | Access settings changed live with `/settings` |
| `auto_delete` | Pending auto-delete jobs, so files still get deleted after a restart |

**Built to be safe under load**

- New users are registered with a single atomic upsert, so one person can only ever count as *one* referral.
- Confirming a referral flips it from `pending` to `confirmed` in one operation, so it's never credited twice.
- Users who block the bot are flagged instead of deleted, which keeps their referral history intact.
- Databases from older versions work as-is — no migration needed.

<sub>© Trinity Mods · <a href="https://github.com/Trinity-Mods">github.com/Trinity-Mods</a> · support: <a href="https://t.me/the_universal_being">@the_universal_being</a></sub>
