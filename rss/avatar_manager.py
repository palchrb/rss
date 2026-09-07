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
import asyncio

from mautrix.types import ContentURI

from .db import DBManager

if TYPE_CHECKING:
    from .bot import RSSBot


class AvatarManager:
    bot: RSSBot
    _avatars: dict[str, ContentURI]
    _db: DBManager
    _lock: asyncio.Lock

    def __init__(self, bot: RSSBot) -> None:
        self.bot = bot
        self._db = bot.dbm
        self._lock = asyncio.Lock()
        self._avatars = {}

    async def load_db(self) -> None:
        self._avatars = {
            avatar.url: ContentURI(avatar.mxc) for avatar in await self._db.get_avatars()
        }

    async def get_mxc(self, url: str) -> ContentURI:
        try:
            return self._avatars[url]
        except KeyError:
            pass
        async with self.bot.http.get(url) as resp:
            resp.raise_for_status()
            data = await resp.read()
            mime_type = resp.content_type
        async with self._lock:
            try:
                return self._avatars[url]
            except KeyError:
                pass
            mxc = await self.bot.client.upload_media(data, mime_type=mime_type)
            self._avatars[url] = mxc
            await self._db.put_avatar(url, mxc)
        return mxc
