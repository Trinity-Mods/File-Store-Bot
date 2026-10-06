# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🔐 Access settings — the mode comes from ACCESS_MODE in config.py and can be changed live with /settings.
# Only the values changed in /settings are saved to the database; everything else keeps following config.py.

from dataclasses import dataclass, replace

from config import ACCESS_MODE, REFERRAL_COUNT, REFERRAL_EXPIRE
from database.database import clear_settings, get_settings, save_settings

MODES = ("off", "fsub", "referral", "dual")
MODE_LABELS = {
    "off": "🔓 ᴏᴘᴇɴ — ɴᴏ ʀᴇꜱᴛʀɪᴄᴛɪᴏɴꜱ",
    "fsub": "📢 ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴏɴʟʏ",
    "referral": "👥 ʀᴇꜰᴇʀʀᴀʟ ᴏɴʟʏ",
    "dual": "🔁 ᴅᴜᴀʟ — ꜰᴏʀᴄᴇ-ꜱᴜʙ ➜ ʀᴇꜰᴇʀʀᴀʟ",
}
_KEY = "access"
_FIELDS = ("mode", "referral_count", "referral_expire")


@dataclass(frozen=True)
class AccessSettings:
    mode: str = ACCESS_MODE
    referral_count: int = REFERRAL_COUNT
    referral_expire: int = REFERRAL_EXPIRE
    overrides: tuple = ()  # names of the values changed with /settings

    @property
    def fsub_on(self) -> bool:
        return self.mode in ("fsub", "dual")

    @property
    def referral_on(self) -> bool:
        return self.mode in ("referral", "dual")


def mode_for(fsub: bool, referral: bool) -> str:
    if fsub and referral:
        return "dual"
    if fsub:
        return "fsub"
    if referral:
        return "referral"
    return "off"


def _valid(field: str, value) -> bool:
    if field == "mode":
        return value in MODES
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    if field == "referral_count":
        return 1 <= value <= 1000
    if field == "referral_expire":
        return value >= 0
    return False


_current = AccessSettings()


def current() -> AccessSettings:
    return _current


async def load() -> AccessSettings:
    """Apply the values saved with /settings on top of config.py (called once at startup)."""
    global _current
    saved = await get_settings(_KEY)
    values = {field: saved[field] for field in _FIELDS if field in saved and _valid(field, saved[field])}
    _current = replace(AccessSettings(), **values, overrides=tuple(sorted(values)))
    return _current


async def update(**changes) -> AccessSettings:
    global _current
    values = {field: value for field, value in changes.items() if field in _FIELDS and _valid(field, value)}
    if not values:
        return _current
    await save_settings(_KEY, values)
    overrides = tuple(sorted(set(_current.overrides) | set(values)))
    _current = replace(_current, **values, overrides=overrides)
    return _current


async def reset() -> AccessSettings:
    """Forget every /settings change and go back to config.py."""
    global _current
    await clear_settings(_KEY)
    _current = AccessSettings()
    return _current

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
