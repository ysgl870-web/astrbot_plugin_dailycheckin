# astrbot_plugin_dailycheckin · 每日签到打卡

一个零依赖、开箱即用的 AstrBot 群签到积分插件。

## 功能

- **每日签到**：每天签到一次，获得随机基础积分 + 连续签到加成。
- **我的积分**：查询自己的总积分、连续签到天数、累计签到次数。
- **积分榜**：本群积分排行榜 Top10。

## 指令

| 指令 | 别名 | 说明 |
|---|---|---|
| `签到` | `checkin` / `打卡` / `每日签到` | 每日签到一次 |
| `我的积分` | `my` / `积分` / `我的信息` | 查看个人积分档案 |
| `积分榜` | `rank` / `排行` / `排行榜` | 本群 Top10 排行 |

## 积分规则

- 基础积分：每次随机 `base_min` ~ `base_max`（默认 5~15）。
- 连续签到：每天额外 `+2` 分，连续天数达到 `max_streak_bonus`（默认 7）天后加成封顶。
- 漏签一天后，连续天数重置为 1。
- 每天只能签到一次。

## 安装

将本目录放入 AstrBot 插件目录（`data/plugins/astrbot_plugin_dailycheckin`），
在 WebUI 插件管理处重载即可。数据保存在
`data/plugin_data/astrbot_plugin_dailycheckin/checkin_data.json`。

## 配置

在 WebUI 插件配置中可调整：

- `base_min` / `base_max`：签到基础积分区间。
- `max_streak_bonus`：连续签到加成封顶天数。
