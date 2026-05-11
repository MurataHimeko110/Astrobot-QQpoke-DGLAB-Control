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
# Original inspiration from:
#   - astrbot_dg_lab_plugin (https://github.com/RC-CHN/astrbot_dg_lab_plugin)
#   - astrbot_plugin_pokepro (https://github.com/Zhalslar/astrbot_plugin_pokepro)
#   - DG-LAB OPENSOURCE (https://github.com/DG-LAB-OPENSOURCE/DG-LAB-OPENSOURCE)

import asyncio
import time
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from .ws_server import CoyoteWSServer
from .coyote_control import CoyoteController

PLUGIN_NAME = "astrbot_plugin_DGLab_poke"

@register(PLUGIN_NAME, "YourName", "戳一戳触发郊狼电击", "1.0.0")
class DGLabPokePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 提取配置
        self.coyote_cfg = {
            'enabled':         config.get('coyote_enabled', False),
            'connection_mode': config.get('connection_mode', 'lan'),
            'public_ws_url':   config.get('public_ws_url', ''),
            'ws_port':         config.get('ws_port', 9999),
            'ws_host':         config.get('ws_host', '0.0.0.0'),
            'channel':         config.get('channel', 'A'),
            'strength_min':    config.get('strength_min', 20),
            'strength_max':    config.get('strength_max', 80),
            'shock_duration':  config.get('shock_duration', 2.0),
            'cooldown':        config.get('cooldown', 10),
            'whitelist_mode':  config.get('whitelist_mode', False),
            'whitelist_groups': config.get('whitelist_groups', []),
            'whitelist_users':  config.get('whitelist_users', []),
            'qr_save_path':    config.get('qr_save_path', ''),
        }

        self.ws_server = CoyoteWSServer(self.coyote_cfg)
        self.controller = CoyoteController(self.ws_server, self.coyote_cfg)

        # 注册 Dashboard API
        self._register_web_api()

    def _register_web_api(self):
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/status",
            self._page_status,
            ["GET"],
            "获取郊狼连接状态"
        )
        self.context.register_web_api(
            f"/{PLUGIN_NAME}/shock",
            self._page_shock,
            ["POST"],
            "手动触发电击"
        )

    async def initialize(self):
        if self.coyote_cfg['enabled']:
            await self.ws_server.start()

    async def terminate(self):
        if self.ws_server:
            await self.ws_server.stop()

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_poke(self, event: AstrMessageEvent):
        if not self.coyote_cfg['enabled']:
            return

        raw = getattr(event.message_obj, 'raw_message', None)
        if not isinstance(raw, dict):
            return
        if raw.get('post_type') != 'notice' or raw.get('notice_type') != 'notify' or raw.get('sub_type') != 'poke':
            return

        target_id = str(raw.get('target_id', ''))
        self_id   = str(raw.get('self_id', ''))
        user_id   = str(raw.get('user_id', ''))
        group_id  = str(raw.get('group_id') or '')

        if target_id != self_id:
            return

        cooldown_key = f"cooldown:{group_id}:{user_id}"
        last_trigger = await self.get_kv_data(cooldown_key, 0.0)
        now = time.time()
        if now - last_trigger < self.coyote_cfg['cooldown']:
            return
        await self.put_kv_data(cooldown_key, now)

        if self.coyote_cfg['whitelist_mode']:
            allowed = False
            if group_id and group_id in self.coyote_cfg['whitelist_groups']:
                allowed = True
            if user_id in self.coyote_cfg['whitelist_users']:
                allowed = True
            if not allowed:
                logger.info(f"[DGLab] 白名单拒绝: group={group_id}, user={user_id}")
                return

        asyncio.create_task(self.controller.random_shock())

    async def _page_status(self):
        from quart import jsonify
        connected = self.ws_server.is_connected
        qr_url = self.ws_server.get_qr_url() if not connected else ""
        return jsonify({
            "connected": connected,
            "qr_url": qr_url,
            "channel": self.coyote_cfg['channel'],
            "strength_min": self.coyote_cfg['strength_min'],
            "strength_max": self.coyote_cfg['strength_max'],
        })

    async def _page_shock(self):
        asyncio.create_task(self.controller.random_shock())
        from quart import jsonify
        return jsonify({"message": "电击指令已发送"})