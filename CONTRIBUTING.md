# 🤝 Contributing to FILE-STORE-BOT

We love your input — whether you're here to report a bug, suggest a feature, submit code, or simply discuss improvements, you're more than welcome! We aim to make contributing to this project as easy, transparent, and rewarding as possible.

### You can help by:

* 🐞 Reporting bugs
* 💬 Sharing ideas or discussing the current code
* 🛠 Submitting a bug fix
* ✨ Proposing or implementing new features

---

## 🧑‍💻 We Develop with GitHub

GitHub is our hub for code, issue tracking, feature requests, and contributions. Here's how to contribute:

1. **Fork the repository** and create your branch from the `main` branch.
2. If you're adding new features or fixing bugs, **test your changes** thoroughly.
3. Ensure your code follows a clean and consistent style.
4. Submit a **pull request to the `main` branch**.

We’ll review and merge as quickly as possible!

---

## 🛠️ Running the bot locally

```bash
git clone https://github.com/<your-username>/File-Store-Bot.git
cd File-Store-Bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in a test bot token, a test channel and a MongoDB URL
python3 main.py
```

Where things live:

* [`config.py`](config.py) — every setting (new options belong here, with a short comment)
* [`core/`](core) — the engine: access modes, force-sub, referrals, delivery, screens
* [`plugins/`](plugins) — Telegram commands and buttons
* [`database/`](database) — MongoDB storage

Please keep the Trinity Mods credit header at the top and bottom of every file.

---

## 📜 Licensing

All contributions made to this repository are automatically licensed under the terms of the **GNU General Public License v3.0**. By submitting your code, you agree that it will be covered by the same [GPL-3.0 License](https://github.com/Trinity-Mods/File-Store-Bot/blob/main/LICENSE) that governs this project.

If you have any questions or concerns regarding licensing, feel free to reach out to the maintainers.

---

## 🐛 Reporting Bugs

We track bugs using GitHub’s [Issues](https://github.com/Trinity-Mods/File-Store-Bot/issues) system.

To report a bug:

1. Go to the [Issues page](https://github.com/Trinity-Mods/File-Store-Bot/issues).
2. Click on **“New Issue”**.
3. Fill out the bug template with as much detail as possible (what you did, what you expected, the bot's log lines).

This helps us identify and resolve issues faster.

Need help right away? Reach out on Telegram: [@the_universal_being](https://t.me/the_universal_being).

---

## 🙌 Thank You

Your contributions make this project better. Whether it’s a single line of code or a detailed issue report — every bit helps!
