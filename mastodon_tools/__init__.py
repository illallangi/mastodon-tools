from .swimmer import MastodonSwimmer
from .user import MastodonUser

from pathlib import Path

from appdirs import user_config_dir
import requests_cache

requests_cache.install_cache(
    Path(user_config_dir()) / "mastodon-tools.db",
    expire_after=3600,
)

__all__ = [
    "MastodonSwimmer",
    "MastodonUser",
]
