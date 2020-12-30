#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2020 Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.
import asyncio
import logging

from pyrogram import raw
from pyrogram.scaffold import Scaffold

log = logging.getLogger(__name__)


class Start(Scaffold):
    async def start(self):
        """Start the client.

        This method connects the client to Telegram and, in case of new sessions, automatically manages the full
        authorization process using an interactive prompt.

        Returns:
            :obj:`~pyrogram.Client`: The started client itself.

        Raises:
            ConnectionError: In case you try to start an already started client.

        Example:
            .. code-block:: python
                :emphasize-lines: 4

                from pyrogram import Client

                app = Client("my_account")
                app.start()

                ...  # Call API methods

                app.stop()
        """
        is_authorized = await self.connect()

        try:
            if not is_authorized:
                if self.login_by_qr_code:
                    asyncio.create_task(self.wait_qr_code_auth())
                    return self
                else:
                    await self.authorize()

            if not await self.storage.is_bot() and self.takeout:
                self.takeout_id = (await self.send(raw.functions.account.InitTakeoutSession())).id
                log.warning(f"Takeout session {self.takeout_id} initiated")

            await self.send(raw.functions.updates.GetState())
        except (Exception, KeyboardInterrupt):
            await self.disconnect()
            raise
        else:
            await self.initialize()
            return self

    async def wait_qr_code_auth(self, max_wait: int = 30):
        try:
            current_timeout = 0

            while current_timeout < max_wait:
                await asyncio.sleep(1)
                current_timeout += 1

                is_authorized = bool(await self.storage.user_id())

                if is_authorized:
                    break

            is_authorized = bool(await self.storage.user_id())

            if not is_authorized:
                raise TimeoutError

            await self.send(raw.functions.updates.GetState())
        except (Exception, KeyboardInterrupt):
            await self.disconnect()
            raise
        else:
            await self.initialize()
            return self
