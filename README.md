# Astrobot-QQpoke-DGLAB-Control
# astrbot_plugin_DGLab_poke

将 **DG-LAB 郊狼脉冲主机 3.0** 的远程电击功能集成到 AstrBot 中。  
当有人（或你自己）在 QQ 中戳机器人时，机器人会通过 WebSocket 向绑定的 DG‑LAB APP 发送随机强度的电击指令，持续数秒后自动归零。

### 特性
- 内置 WebSocket 服务端，无需额外部署 Node.js 后端。
- 支持 **局域网直连** 和 **内网穿透 (SakuraFrp)** 两种连接模式。
- 群聊 / 私聊戳一戳均可触发，冷却时间、强度范围均可配置。
- 白名单机制，可按群或用户精确控制触发权限。
- Dashboard 页面实时显示连接状态、二维码，支持手动电击。
- 所有参数均在 AstrBot WebUI 中可视化调节。

### 连接模式说明
插件提供两种连接方式，可在 WebUI 配置面板中随时切换：

#### 1. 局域网直连（默认）
- **适用场景**：手机和 AstrBot 服务器在同一个 Wi‑Fi 或局域网内。
- 插件会自动检测服务器的局域网 IP 并生成二维码，APP 扫码即可连接。
- 无需任何额外配置。

#### 2. 内网穿透（公网连接）
- **适用场景**：手机使用移动数据，或与服务器不在同一局域网。
- 需要配合内网穿透软件（如 **SakuraFrp**）使用。
- 在穿透软件中创建 TCP 隧道（或 WSS 隧道），将 AstrBot 的 WebSocket 端口暴露到公网。
- 在插件配置中选择“内网穿透模式”，并填入公网地址即可自动生成正确的二维码。
- 推荐使用 SakuraFrp 的 **TCP 隧道** 或 **WSS 隧道**（WSS 更安全）。

### 安装
在 AstrBot 插件市场中搜索 `astrbot_plugin_DGLab_poke` 安装，或手动放入 `AstrBot/data/plugins/` 目录，依赖会在安装时自动处理。

### 快速开始
1. 在 AstrBot WebUI 插件管理页启用 `coyote_enabled`。
2. 根据实际情况选择连接模式并保存。
3. 重载插件，查看日志或 Dashboard 页面获取二维码/地址。
4. 二维码图片会自动保存到配置的路径（默认 `data/plugin_data/astrbot_plugin_DGLab_poke/qr_code/qrcode.png`），可直接打开扫码。
5. 打开 DG‑LAB APP → SOCKET 控制，扫描二维码或手动输入地址完成配对。
6. 在 QQ 中戳机器人，即可触发随机电击。

### 配置项说明
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `coyote_enabled` | 是否启用插件 | false |
| `connection_mode` | 连接模式：`lan`（局域网）或 `frp`（内网穿透） | lan |
| `public_ws_url` | 内网穿透公网地址（仅 frp 模式有效） | （空） |
| `ws_port` | WebSocket 监听端口 | 9999 |
| `ws_host` | 监听地址（通常 0.0.0.0） | 0.0.0.0 |
| `channel` | 控制通道 (A/B) | A |
| `strength_min` | 随机强度下限 (0~200) | 20 |
| `strength_max` | 随机强度上限 (0~200) | 80 |
| `shock_duration` | 电击保持时间（秒） | 2.0 |
| `cooldown` | 触发冷却时间（秒） | 10 |
| `whitelist_mode` | 是否启用白名单 | false |
| `whitelist_groups` | 白名单群号列表 | [] |
| `whitelist_users` | 白名单用户 QQ 号列表 | [] |
| `qr_save_path` | 二维码图片保存文件夹路径 | （空，默认 `qr_code/`） |

### Dashboard 页面
插件详情页内嵌了“郊狼控制”面板，可实时查看连接状态、显示二维码，并提供手动电击按钮，方便测试。

### 参考与致谢
本项目基于以下开源项目的思想与代码构建：
- **[astrbot_dg_lab_plugin](https://github.com/RC-CHN/astrbot_dg_lab_plugin)** — HTTP API 调用郊狼的示例。
- **[astrbot_plugin_pokepro](https://github.com/Zhalslar/astrbot_plugin_pokepro)** — 戳一戳事件监听与处理逻辑。
- **[DG‑LAB SOCKET 控制 v2](https://github.com/dg-lab-opensource/socket)** — WebSocket 控制协议的设计参考。

感谢以上项目的作者们！

### 版本要求
- AstrBot ≥ 4.9.2
- Python ≥ 3.10
- 依赖 aiohttp, qrcode[pil]
