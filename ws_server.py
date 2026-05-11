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
# Original protocol design references:
#   - DG-LAB OPENSOURCE (https://github.com/DG-LAB-OPENSOURCE/DG-LAB-OPENSOURCE)

import asyncio
import uuid
import socket
import qrcode
from pathlib import Path
from aiohttp import web
from astrbot.api import logger

class CoyoteWSServer:
    def __init__(self, config: dict):
        self.cfg = config
        self.client_id = str(uuid.uuid4())
        self.target_id: str | None = None
        self.app_ws: web.WebSocketResponse | None = None
        self.runner: web.AppRunner | None = None
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self):
        app = web.Application()
        app.router.add_get("/{client_id}", self._handle_ws)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.cfg['ws_host'], self.cfg['ws_port'])
        await site.start()

        qr_url = self.get_qr_url()
        logger.info(
            f"\n{'='*60}\n"
            f"[DGLab] WebSocket 服务已启动 (模式: {self.cfg['connection_mode']})\n"
            f"连接地址：{qr_url}\n"
            f"{'='*60}"
        )

        # 生成二维码图片
        await self._generate_qr_image(qr_url)

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self.app_ws and not self.app_ws.closed:
            await self.app_ws.close()
        if self.runner:
            await self.runner.cleanup()
        logger.info("[DGLab] WS 服务已停止")

    async def _handle_ws(self, request: web.Request):
        qrcode_client_id = request.match_info.get("client_id", "")
        if qrcode_client_id != self.client_id:
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            await ws.send_json({
                "type": "bind", "clientId": "", "targetId": "",
                "message": "210"
            })
            await ws.close()
            return ws

        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logger.info("[DGLab] APP 已连接")

        async for msg in ws:
            if msg.type != web.WSMsgType.TEXT:
                continue
            try:
                data = msg.json()
            except Exception:
                await ws.send_json({
                    "type": "msg", "clientId": "", "targetId": "",
                    "message": "403"
                })
                continue
            if data.get("type") == "bind":
                await self._handle_bind(ws, data)
        logger.info("[DGLab] APP 连接断开")
        self.target_id = None
        self.app_ws = None
        return ws

    async def _handle_bind(self, ws, data):
        if self.app_ws is not None:
            await self.app_ws.close()
        new_target_id = str(uuid.uuid4())
        self.target_id = new_target_id
        self.app_ws = ws
        await self._safe_send(ws, {
            "type": "bind",
            "clientId": self.client_id,
            "targetId": new_target_id,
            "message": "200"
        })
        logger.info(f"[DGLab] 配对成功: targetId={new_target_id}")

    async def _heartbeat_loop(self):
        while True:
            try:
                await asyncio.sleep(60)
                if self.app_ws and not self.app_ws.closed:
                    await self._safe_send(self.app_ws, {
                        "type": "heartbeat",
                        "clientId": self.client_id,
                        "targetId": self.target_id or "",
                        "message": "200"
                    })
            except asyncio.CancelledError:
                break

    async def send_strength(self, channel: str, mode: str, value: int):
        if not self.app_ws or self.app_ws.closed:
            return
        msg = f"strength-{channel}+{mode}+{value}"
        await self._safe_send(self.app_ws, {
            "type": "msg",
            "clientId": self.client_id,
            "targetId": self.target_id or "",
            "message": msg
        })
        logger.debug(f"[DGLab] 指令: {msg}")

    @staticmethod
    async def _safe_send(ws: web.WebSocketResponse, data: dict):
        if not ws.closed:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.error(f"[DGLab] 发送失败: {e}")

    def get_qr_url(self) -> str:
        # 内网穿透模式：使用公网地址
        if self.cfg['connection_mode'] == 'frp' and self.cfg['public_ws_url']:
            url = self.cfg['public_ws_url'].rstrip('/') + '/' + self.client_id
            return f"https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#{url}"

        # 局域网模式：自动检测 IP
        host = self.cfg['ws_host']
        if host == "0.0.0.0":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                host = s.getsockname()[0]
                s.close()
            except Exception:
                host = "127.0.0.1"
        return f"https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#ws://{host}:{self.cfg['ws_port']}/{self.client_id}"

    async def _generate_qr_image(self, qr_url: str):
        """将二维码 URL 生成 PNG 图片保存到指定目录"""
        save_path = self.cfg.get('qr_save_path', '')
        if save_path:
            save_dir = Path(save_path).expanduser().resolve()
        else:
            # 默认保存到插件数据目录下的 qr_code/
            from astrbot.core.utils.astrbot_path import get_astrbot_data_path
            base_dir = Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_DGLab_poke"
            save_dir = base_dir / "qr_code"

        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            img_path = save_dir / "qrcode.png"
            img = qrcode.make(qr_url)
            img.save(str(img_path))
            logger.info(f"[DGLab] 二维码图片已保存：{img_path}")
        except Exception as e:
            logger.error(f"[DGLab] 生成二维码图片失败：{e}")

    @property
    def is_connected(self) -> bool:
        return self.app_ws is not None and not self.app_ws.closed