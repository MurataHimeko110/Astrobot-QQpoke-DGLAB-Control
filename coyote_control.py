# Copyright (C) 2026 YourName
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Inspired by:
#   - astrbot_dg_lab_plugin (https://github.com/RC-CHN/astrbot_dg_lab_plugin)

import asyncio
import random
from astrbot.api import logger

class CoyoteController:
    def __init__(self, ws_server, config: dict):
        self.ws = ws_server
        self.cfg = config

    async def random_shock(self):
        if not self.ws.is_connected:
            logger.debug("[DGLab] APP 未连接，跳过电击")
            return

        strength = random.randint(self.cfg['strength_min'], self.cfg['strength_max'])
        channel = "1" if self.cfg['channel'] == "A" else "2"

        try:
            await self.ws.send_strength(channel, "2", strength)
            logger.info(f"[DGLab] 触发随机电击：通道{self.cfg['channel']}，强度{strength}")
            await asyncio.sleep(self.cfg['shock_duration'])
            await self.ws.send_strength(channel, "2", 0)
            logger.info("[DGLab] 强度已归零")
        except Exception as e:
            logger.error(f"[DGLab] 电击异常: {e}")