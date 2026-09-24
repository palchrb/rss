# rss - A maubot plugin to subscribe to RSS/Atom feeds.
# Copyright (C) 2022 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from typing import TYPE_CHECKING
from time import time
import asyncio
import hashlib

import aiohttp

from mautrix.types import ContentURI

from .db import Avatar, DBManager

if TYPE_CHECKING:
    from .bot import RSSBot


class AvatarManager:
    bot: RSSBot
    _avatars: dict[str, Avatar]
    _db: DBManager
    _lock: asyncio.Lock

    def __init__(self, bot: RSSBot) -> None:
        self.bot = bot
        self._db = bot.dbm
        self._lock = asyncio.Lock()
        self._avatars = {}

    async def load_db(self) -> None:
        self._avatars = {avatar.url: avatar for avatar in await self._db.get_avatars()}

    @property
    def _refresh_after(self) -> int:
        return int(self.bot.config["avatar_refresh_days"]) * 24 * 60 * 60

    def _is_fresh(self, avatar: Avatar) -> bool:
        if self._refresh_after <= 0:
            # Refreshing is disabled: uploaded avatars are kept forever, misses are always retried.
            return bool(avatar.mxc)
        return avatar.fetched_at > int(time()) - self._refresh_after

    async def _store(self, url: str, mxc: ContentURI, content_hash: str) -> None:
        avatar = Avatar(url=url, mxc=mxc, content_hash=content_hash, fetched_at=int(time()))
        self._avatars[url] = avatar
        await self._db.put_avatar(avatar)

    async def get_mxc(self, url: str) -> ContentURI:
        """Get the mxc:// URI for an image URL, downloading and uploading it when needed.
        Returns an empty string if the URL is known to have no image."""
        cached = self._avatars.get(url)
        if cached and self._is_fresh(cached):
            return cached.mxc
        try:
            async with self.bot.http.get(url) as resp:
                resp.raise_for_status()
                data = await resp.read()
                mime_type = resp.content_type
        except Exception as e:
            if cached and cached.mxc:
                # Keep the old avatar and try again after the refresh period
                self.bot.log.debug(f"Failed to refresh avatar {url}, keeping the old one: {e}")
                await self._store(url, cached.mxc, cached.content_hash)
                return cached.mxc
            if (
                isinstance(e, aiohttp.ClientResponseError)
                and e.status < 500
                and self._refresh_after > 0
            ):
                # There's no image at this URL, remember that so it isn't retried on every post
                await self._store(url, ContentURI(""), "")
                return ContentURI("")
            raise
        content_hash = hashlib.sha256(data).hexdigest()
        async with self._lock:
            cached = self._avatars.get(url)
            if cached and cached.mxc and cached.content_hash == content_hash:
                mxc = cached.mxc
            else:
                mxc = await self.bot.client.upload_media(data, mime_type=mime_type)
            await self._store(url, mxc, content_hash)
        return mxc
