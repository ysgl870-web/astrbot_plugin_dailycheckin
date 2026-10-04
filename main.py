# astrbot_plugin_dailycheckin
# 群内每日签到打卡积分插件（纯标准库，零额外依赖）

from __future__ import annotations

import json
import os
import random
import datetime
from typing import Dict, Any, Optional

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register

try:
    from astrbot.core.config.astrbot_config import AstrBotConfig
except Exception:  # pragma: no cover
    from astrbot.core import AstrBotConfig  # type: ignore

# 数据目录：优先使用 AstrBot 提供的 StarTools，失败则回退到容器内固定路径
def _resolve_data_dir() -> str:
    try:
        from astrbot.api.star import StarTools
        d = str(StarTools.get_data_dir("astrbot_plugin_dailycheckin"))
        if d:
            os.makedirs(d, exist_ok=True)
            return d
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dailycheckin] StarTools 不可用，回退默认数据目录: {e}")
    d = "/AstrBot/data/plugin_data/astrbot_plugin_dailycheckin"
    os.makedirs(d, exist_ok=True)
    return d


@register(
    "astrbot_plugin_dailycheckin",
    "ysgl",
    "群内每日签到打卡赚积分，支持连续签到加成与积分榜排行",
    "1.0.0",
    "https://ysgl.bot.cd",
)
class DailyCheckin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.data_dir = _resolve_data_dir()
        self.data_file = os.path.join(self.data_dir, "checkin_data.json")
        self.data: Dict[str, Any] = self._load()

        # 可配置项（带默认值）
        self.base_min: int = int(self.config.get("base_min", 5))
        self.base_max: int = int(self.config.get("base_max", 15))
        self.max_streak_bonus: int = int(self.config.get("max_streak_bonus", 7))

    # ---------------- 数据持久化 ----------------
    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:  # noqa: BLE001
                logger.error(f"[dailycheckin] 读取数据失败，将重置: {e}")
        return {"groups": {}}

    def _save(self) -> None:
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            logger.error(f"[dailycheckin] 写入数据失败: {e}")

    # ---------------- 工具方法 ----------------
    def _group_key(self, event) -> str:
        try:
            return str(event.get_group_id())
        except Exception:
            return "private"

    def _user_key(self, event) -> str:
        try:
            return str(event.get_sender_id())
        except Exception:
            return "unknown"

    def _user_name(self, event) -> str:
        try:
            return event.get_sender_name() or "无名氏"
        except Exception:
            return "无名氏"

    def _gu(self, group: str) -> Dict[str, Any]:
        return self.data.setdefault("groups", {}).setdefault(group, {"users": {}})["users"]

    @staticmethod
    def _today() -> str:
        return datetime.date.today().isoformat()

    @staticmethod
    def _yesterday() -> str:
        return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    # ---------------- 指令 ----------------
    @filter.command("签到", alias={"checkin", "打卡", "每日签到"})
    async def checkin(self, event):
        group = self._group_key(event)
        uid = self._user_key(event)
        name = self._user_name(event)
        users = self._gu(group)
        today = self._today()

        u = users.get(uid)
        if u and u.get("last") == today:
            yield event.plain_result("今天已经签到过啦，明天再来吧～ 💤")
            return

        if u and u.get("last") == self._yesterday():
            streak = int(u.get("streak", 0)) + 1
        else:
            streak = 1

        base = random.randint(self.base_min, self.base_max)
        bonus = min(streak, self.max_streak_bonus) * 2
        gained = base + bonus

        users[uid] = {
            "name": name,
            "points": int(u.get("points", 0)) + gained if u else gained,
            "streak": streak,
            "last": today,
            "total": int(u.get("total", 0)) + 1 if u else 1,
        }
        self._save()

        msg = (
            f"✅ 签到成功！\n"
            f"获得积分：+{gained}"
            f"（基础 {base}" + (f" + 连签加成 {bonus}" if bonus else "") + "）\n"
            f"连续签到：{streak} 天\n"
            f"当前总积分：{users[uid]['points']}"
        )
        yield event.plain_result(msg)

    @filter.command("我的积分", alias={"my", "积分", "我的信息"})
    async def my_info(self, event):
        group = self._group_key(event)
        uid = self._user_key(event)
        users = self._gu(group)
        u = users.get(uid)
        if not u:
            yield event.plain_result("你还没有签过到哦，发送「签到」开始打卡吧～")
            return
        yield event.plain_result(
            f"👤 {u.get('name', '无名氏')} 的签到档案\n"
            f"总积分：{u.get('points', 0)}\n"
            f"连续签到：{u.get('streak', 0)} 天\n"
            f"累计签到：{u.get('total', 0)} 次\n"
            f"最近签到：{u.get('last', '无')}"
        )

    @filter.command("积分榜", alias={"rank", "排行", "排行榜"})
    async def rank(self, event):
        group = self._group_key(event)
        users = self._gu(group)
        if not users:
            yield event.plain_result("本群还没有人签到过哦～")
            return
        top = sorted(users.items(), key=lambda kv: kv[1].get("points", 0), reverse=True)[:10]
        lines = ["🏆 本群积分榜 Top10"]
        medals = ["🥇", "🥈", "🥉"]
        for i, (_, u) in enumerate(top):
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(
                f"{prefix} {u.get('name', '无名氏')}  "
                f"{u.get('points', 0)} 分"
                f"（连签 {u.get('streak', 0)} 天）"
            )
        yield event.plain_result("\n".join(lines))
