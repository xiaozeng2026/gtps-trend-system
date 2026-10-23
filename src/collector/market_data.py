"""
外部高频金融行情直连采集器 + 地缘新闻硬数据真实性交叉核验引擎。

核心思想：新闻文本存在舆论炒作水分，需要用不掺水分的实物/金融硬资产数据
（布伦特原油、伦敦黄金、WTI、天然气、离岸汇率等）进行交叉比对——
  - 若新闻声称地缘冲突同时原油/黄金波动极小 → 判定为「舆论口水战」→ 降低冲击烈度；
  - 若新闻爆发同时大宗商品暴涨 → 确认「实质性战略冲击」→ 提升烈度并附资金证据链。

行情来源：新浪金融公开行情直通车（免 Key、免代理、国内网络极速）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import requests

from ..core.models import DomainCategory

if TYPE_CHECKING:
    # 延迟导入 GlobalEvent 避免 collector.news_collector 与 collector.market_data 相互循环
    from ..collector.news_collector import GlobalEvent

# ---------------------------------------------------------------------------
# 新浪金融行情：5 个关键资产代码（域名冲突不影响国内网络）
# ---------------------------------------------------------------------------
SINA_QUOTES = [
    ("hf_OIL", "布伦特原油 (Brent)",  "commodity_oil_brent"),
    ("hf_GC",  "纽约黄金 (Comex)",     "commodity_gold"),
    ("hf_CL",  "纽约 WTI 原油",        "commodity_oil_wti"),
    ("hf_NG",  "纽约天然气",           "commodity_natural_gas"),
    ("fx_susdcnh", "离岸人民币 (CNH)", "fx_offshore_cny"),
]

SINA_QUOTE_URL = "https://hq.sinajs.cn/list=" + ",".join(q[0] for q in SINA_QUOTES)
SINA_HEADERS = {
    "Referer": "https://finance.sina.com.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

# 用于解析 hq_str_XXX="a,b,c,..." 的正则
_QUOTE_LINE_RE = re.compile(r"hq_str_(\w+)=\"(.+?)\";")


@dataclass
class MarketQuote:
    """单支行情快照（不依赖 Pydantic 以保持轻量快速）。"""
    symbol: str
    name: str
    price: float
    change_pct: float       # 今日涨跌幅（昨收为基准，带正负号）
    high: float
    low: float
    prev_close: float
    open: float = 0.0
    timestamp: str = ""
    source: str = "Sina Live"


class MarketDataCollector:
    """新浪金融直通行情采集器 + 宏观风险指数计算。"""

    def __init__(self, timeout: int = 6):
        self.timeout = timeout
        self._last_snapshot: Optional[Dict[str, MarketQuote]] = None
        self._last_fetch_ts: Optional[datetime] = None

    # ------------------------------------------------------------------ #
    def get_live_market_snapshot(self, force_refresh: bool = False) -> Dict[str, MarketQuote]:
        """拉取新浪金融直通行情；失败时返回上一次可用快照（若无则空字典）。"""
        if (self._last_snapshot is not None
                and not force_refresh
                and self._last_fetch_ts
                and (datetime.now() - self._last_fetch_ts).total_seconds() < 30):
            return self._last_snapshot

        try:
            resp = requests.get(SINA_QUOTE_URL, headers=SINA_HEADERS, timeout=self.timeout)
            resp.encoding = "gbk"
            resp.raise_for_status()
            parsed = self._parse_sina_text(resp.text)
        except Exception:
            # 任何网络/解析异常 → 保留上一次快照并返回
            return self._last_snapshot or {}

        self._last_snapshot = parsed
        self._last_fetch_ts = datetime.now()
        return parsed

    # ------------------------------------------------------------------ #
    def calculate_macro_risk_index(self,
                                   snapshot: Optional[Dict[str, MarketQuote]] = None) -> float:
        """
        全球宏观金融避险与风险指数（0–100）。
        设计意图：黄金是"恐慌性避险最灵敏指标"，原油是"地缘冲突最直接锚点"。
        风险指数 = |黄金今日涨跌幅| * 1.6 + |布伦特原油今日涨跌幅| * 1.0，然后归一化。
          - 指数 ≥ 60：金融市场集体避险、实质性战略冲击；
          - 指数 < 25：资金未响应，大概率舆论口水战或边际扰动。
        """
        if snapshot is not None:
            snap = snapshot
        else:
            snap = self.get_live_market_snapshot()
        gold = snap.get("hf_GC")
        oil = snap.get("hf_OIL")
        if not gold or not oil:
            return 0.0
        raw = abs(gold.change_pct) * 1.6 + abs(oil.change_pct) * 1.0
        # 归一化：|黄金|>=10% 或 |原油|>=25% 极端情况下封顶 100
        risk_index = min(100.0, raw * 8.0)
        return round(risk_index, 2)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_sina_text(text: str) -> Dict[str, MarketQuote]:
        """新浪 hq_str_XXX="..." 文本 → 报价字典。"""
        result: Dict[str, MarketQuote] = {}
        name_map = {code: name for code, name, _ in SINA_QUOTES}

        for m in _QUOTE_LINE_RE.finditer(text):
            code, body = m.group(1), m.group(2)
            fields = body.split(",")
            # fx_susdcnh 字段布局不同且本次不参与风险计算，跳过避免 IndexError
            if code == "fx_susdcnh":
                continue
            if len(fields) < 14:
                continue
            try:
                price = float(fields[0])
                prev_close = float(fields[2]) if fields[2] else float(fields[3])
                open_px = float(fields[3]) if fields[3] else prev_close
                high = float(fields[4]) if fields[4] else price
                low = float(fields[5]) if fields[5] else price
            except (ValueError, IndexError):
                continue
            if prev_close <= 0 or price <= 0:
                continue
            change_pct = round((price - prev_close) / prev_close * 100, 3)
            result[code] = MarketQuote(
                symbol=code,
                name=name_map.get(code, code),
                price=price,
                change_pct=change_pct,
                high=high,
                low=low,
                prev_close=prev_close,
                open=open_px,
                timestamp=f"{fields[12]} {fields[6]}",  # [12]=日期, [6]=时间
            )
        return result


# ---------------------------------------------------------------------------
# 地缘新闻 × 金融硬数据 交叉核验
# ---------------------------------------------------------------------------
SUBSTANTIAL_OIL_THR = 1.2    # 原油涨跌幅 ≥ 1.2% 视为资金已响应
SUBSTANTIAL_GOLD_THR = 0.8   # 黄金涨跌幅 ≥ 0.8% 视为资金已响应
NOISE_THR = 0.4              # 波动 < 0.4% 视为纯舆论口水战


class CrossCheckFilter:
    """
    地缘冲突/能源危机类新闻的真实性交叉核验过滤器。
    核心逻辑：金融硬资产价格波动是资金投票，不掺文本水分。
    """

    @staticmethod
    def verify_event_against_market(event: GlobalEvent,
                                    market_snapshot: Dict[str, MarketQuote]) -> Dict[str, Any]:
        """
        对单条 GlobalEvent 返回结构化核验报告：
          - verification_tag: "资金已证实·重大实质冲击" / "资金未响应·局限舆论博弈" / "不在核验范围"
          - verified_impact: 经金融证据校准后的冲击烈度
          - confidence: 核验置信度 (0-1)
          - evidence: 证据链数组（资产、涨跌幅、解释）
        """
        result: Dict[str, Any] = {
            "verification_tag": "不在核验范围",
            "verified_impact": event.impact_level,
            "confidence": 0.5,
            "evidence": [],
            "needs_adjustment": False,
        }

        # 只对地缘政治 / 能源危机类事件做硬数据交叉核验
        if event.domain not in (DomainCategory.POLITICS, DomainCategory.ENERGY):
            result["evidence"].append({
                "asset": "—", "change_pct": 0.0,
                "note": f"领域 {event.domain} 不属于地缘冲突/能源危机核验范围",
            })
            return result

        gold = market_snapshot.get("hf_GC")
        oil = market_snapshot.get("hf_OIL")
        if not gold or not oil:
            result["verification_tag"] = "核验失败·行情缺失"
            result["confidence"] = 0.0
            result["evidence"].append({"asset": "—", "note": "新浪行情接口未返回黄金或原油数据"})
            return result

        oil_abs = abs(oil.change_pct)
        gold_abs = abs(gold.change_pct)
        evidence = []
        evidence.append({
            "asset": gold.name, "change_pct": gold.change_pct,
            "note": f"今日涨跌 {gold.change_pct:+.2f}%（昨收 {gold.prev_close}）",
        })
        evidence.append({
            "asset": oil.name, "change_pct": oil.change_pct,
            "note": f"今日涨跌 {oil.change_pct:+.2f}%（昨收 {oil.prev_close}）",
        })

        if oil_abs >= SUBSTANTIAL_OIL_THR or gold_abs >= SUBSTANTIAL_GOLD_THR:
            # ---- 资金已证实：实质性战略冲击 ----
            result["verification_tag"] = "资金已证实·重大实质冲击"
            result["verified_impact"] = round(min(0.98, event.impact_level * 1.25), 3)
            result["confidence"] = round(min(0.95, 0.6 + 0.35 * max(oil_abs / SUBSTANTIAL_OIL_THR,
                                                                    gold_abs / SUBSTANTIAL_GOLD_THR)), 3)
            result["needs_adjustment"] = True
            if gold_abs >= SUBSTANTIAL_GOLD_THR:
                evidence.append({"asset": gold.name, "note": f"黄金波动 {gold_abs:.1f}% ≥ 阈值 {SUBSTANTIAL_GOLD_THR}%，印证市场避险"})
            if oil_abs >= SUBSTANTIAL_OIL_THR:
                evidence.append({"asset": oil.name, "note": f"原油波动 {oil_abs:.1f}% ≥ 阈值 {SUBSTANTIAL_OIL_THR}%，印证供应链/地缘实质冲击"})
        elif oil_abs < NOISE_THR and gold_abs < NOISE_THR:
            # ---- 资金未响应：局限舆论博弈 ----
            result["verification_tag"] = "资金未响应·局限舆论博弈"
            result["verified_impact"] = round(max(0.45, event.impact_level * 0.75), 3)
            result["confidence"] = round(max(0.7, 0.9 - 0.5 * max(oil_abs / NOISE_THR, gold_abs / NOISE_THR)), 3)
            result["needs_adjustment"] = True
            evidence.append({"asset": "—", "note": f"黄金/原油波动均 < {NOISE_THR}%，市场未起实质恐慌，判定为舆论口水战"})
        else:
            # 介于阈值之间 → 中性保留原烈度
            result["verification_tag"] = "资金观望·烈度维持"
            result["verified_impact"] = event.impact_level
            result["confidence"] = 0.65
            evidence.append({"asset": "—", "note": "波动处于阈值区间，市场信号模糊，暂维持原冲击烈度"})

        result["evidence"] = evidence
        return result
