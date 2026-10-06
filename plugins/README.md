# 🔌 plugins — commands & buttons

Pyrofork loads every file in this folder automatically when the bot starts. Each file groups the
Telegram handlers for one area of the bot.

| File | Handles |
| --- | --- |
| [`start.py`](start.py) | `/start` (file links, referral links, token links), `/ch2l`, `/ping` |
| [`access.py`](access.py) | Force-sub **Try Again** · referral **Check Progress** · `/refer` · owner `/settings` panel · `/refstats` · `/addrefs` |
| [`admin.py`](admin.py) | `/users` · `/broadcast` · `/auth` · `/add_admin` · `/del_admin` · `/admins` · `/restart` · `/add_prem` |
| [`channel_post.py`](channel_post.py) | Admins send any file → it's saved in the DB channel and a share link comes back |
| [`link_generator.py`](link_generator.py) | `/genlink` (one post) and `/batch` (a range of posts) |
| [`cbb.py`](cbb.py) | Start-menu buttons: About · Premium · Back · Close |
| [`useless.py`](useless.py) | `/stats` uptime and the auto-reply for users who message the bot directly |
| [`__init__.py`](__init__.py) | The small web server used for health checks |

> ➕ Adding your own command? Create a new `.py` file here and decorate your function with `@Bot.on_message(...)`.
> Also add the command name to `KNOWN_COMMANDS` in [`helper_func.py`](../helper_func.py) so it isn't treated as a file upload.

<sub>© Trinity Mods · <a href="https://github.com/Trinity-Mods">github.com/Trinity-Mods</a> · support: <a href="https://t.me/the_universal_being">@the_universal_being</a></sub>
