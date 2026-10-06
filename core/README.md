# 🧠 core — the engine of File Store Bot

Everything that decides **who gets which file, and when** lives here. These files contain no Telegram
handlers — the commands and buttons that call them are in [`../plugins`](../plugins).

| File | What it does |
| --- | --- |
| [`access.py`](access.py) | The active access mode (`fsub` · `referral` · `dual` · `off`) and the live changes made with `/settings` |
| [`fsub.py`](fsub.py) | Force-sub chats (0 – 4): invite links and reliable membership checks that never trap real members |
| [`referral.py`](referral.py) | Referral links, fresh-user counting, unlocking and live notifications to referrers |
| [`pipeline.py`](pipeline.py) | The journey of every `/start` link: force-sub ➜ referral ➜ shortener ➜ files |
| [`delivery.py`](delivery.py) | Sends the files and auto-deletes them later — jobs are saved, so restarts don't skip a deletion |
| [`ui.py`](ui.py) | Every screen and button layout, plus the pictures for the start, force-sub and referral messages |

> 💡 You don't need to edit anything here to run the bot — all settings are in [`config.py`](../config.py).

<sub>© Trinity Mods · <a href="https://github.com/Trinity-Mods">github.com/Trinity-Mods</a> · support: <a href="https://t.me/the_universal_being">@the_universal_being</a></sub>
