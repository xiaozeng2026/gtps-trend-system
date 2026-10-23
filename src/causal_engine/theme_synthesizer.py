"""
任意命题自生因果图谱合成器（ThemeSynthesizer）。

给定一句命题（例："全球 AI 芯片贸易制裁与台湾地缘冲突的连锁传导"），
利用 LLM 生成完整的 6–8 节点、8–12 边的标准主题 JSON，
必须包含至少一组反馈回路与 4 个对立阵营参谋部设定。

智能降级：未配置 API Key 或调用失败 → 高拟真度通用突发危机模板兜底，
确保永远成功返回可直接热插拔进 CausalNetwork 的主题包。
"""
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..simulation.llm_wargame import LLMClient

# 主题 JSON 必须满足的硬约束（用于 LLM 侧提示与本地兜底模板）
_THEME_SCHEMA_HINT = """
输出必须是严格合法的 JSON，顶层包含以下字段：
{
  "theme_id":   "THEME_XXX_UPPERCASE",
  "theme_name": "中文主题名（含中文标点）",
  "description": "一段中文描述该主题的核心矛盾",
  "nodes": [ {"node_id":"ABC_DEF","name":"中文名","domain":"TECHNOLOGY|ENERGY|POLITICS|ECONOMY|SOCIETY|ECOLOGY","intensity":0.5,"description":"中文描述"} ],
  "links": [ {"source_id":"ABC_DEF","target_id":"XYZ_UWU","weight":+0.85 或 -0.45,"delay_months":3,"mechanism":"中文传导机制说明"} ],
  "personas": [ {"persona_id":"BLOC_NAME","name":"中文名","strategy":"中文战略姿态"} ],
  "scenarios": [ {"scenario_id":"SC_NAME","probability":0.45,"time_horizon":"2026-2028","narrative":"中文叙事"} ]
}
约束：
1. nodes 数量 6–8；links 数量 8–12；
2. 至少一条正权重边 + 一条负权重边（分别用于强化/调节回路）；
3. 必须包含至少一组有向闭环（可以通过手动确保 weight 乘积 ≠ 0 的环）；
4. personas 必须 4 个，分别代表相互对立的利益集团；
5. scenarios 必须 3 个，probability 总和约等于 1；
6. weight 范围 [-1.0, +1.0]，probability 范围 [0.0, 1.0]。
最后一行独占：只输出合法 JSON，禁止任何 Markdown、注释或额外文本。
"""

# 兜底模板：通用突发危机推演骨架（LLM 不可用时的高拟真 fallback）
_GENERIC_CRISIS_TEMPLATE: Dict[str, Any] = {
    "theme_id": "THEME_GENERIC_CRISIS",
    "theme_name": "通用突发危机与全球供应链重定价",
    "description": "重大地缘事件触发的需求-供给-资本-监管四轮冲击与闭环反馈。",
    "nodes": [
        {"node_id": "CRISIS_TRIGGER",       "name": "突发事件冲击强度",     "domain": "POLITICS",  "intensity": 0.75, "description": "突发地缘/能源/科技事件的初始烈度"},
        {"node_id": "SUPPLY_CHOKE",         "name": "关键供应链瓶颈",       "domain": "ECONOMY",   "intensity": 0.60, "description": "上游原材料或关键零部件交付受阻"},
        {"node_id": "PRICE_SPIRAL",         "name": "核心大宗商品价格螺旋", "domain": "ECONOMY",   "intensity": 0.55, "description": "短缺与炒作叠加推高现货价格"},
        {"node_id": "MANUFACTURING_MARGIN", "name": "制造业利润率承压",     "domain": "ECONOMY",   "intensity": 0.48, "description": "成本传导导致中下游利润压缩"},
        {"node_id": "CONSUMER_SQUEEZE",     "name": "居民消费与社会挤压",   "domain": "SOCIETY",   "intensity": 0.42, "description": "终端通胀与收入侵蚀引发居民不满"},
        {"node_id": "POLICY_INTERVENTION",  "name": "紧急政策干预力度",     "domain": "POLITICS",  "intensity": 0.35, "description": "补贴/价格上限/出口管制等行政手段"},
        {"node_id": "SUBSTITUTION_ACCEL",   "name": "替代方案研发加速",     "domain": "TECHNOLOGY","intensity": 0.30, "description": "被卡脖子环节的研发与替代进程加速"},
        {"node_id": "GLOBAL_CAPITAL_FLOW",  "name": "全球避险资本流动方向", "domain": "ECONOMY",   "intensity": 0.50, "description": "避险资产与低风险区域吸引资本流入"}
    ],
    "links": [
        {"source_id": "CRISIS_TRIGGER",       "target_id": "SUPPLY_CHOKE",         "weight":  0.85, "delay_months":  1, "mechanism": "突发事件直接切断关键供给通道"},
        {"source_id": "SUPPLY_CHOKE",         "target_id": "PRICE_SPIRAL",         "weight":  0.80, "delay_months":  1, "mechanism": "供给短缺迅速传导至现货与期货价格"},
        {"source_id": "PRICE_SPIRAL",         "target_id": "MANUFACTURING_MARGIN", "weight":  0.65, "delay_months":  2, "mechanism": "原材料涨价直接压缩下游制造业毛利"},
        {"source_id": "MANUFACTURING_MARGIN", "target_id": "CONSUMER_SQUEEZE",     "weight":  0.55, "delay_months":  3, "mechanism": "利润压力传导至终端售价引发居民不满"},
        {"source_id": "CONSUMER_SQUEEZE",     "target_id": "POLICY_INTERVENTION",  "weight":  0.70, "delay_months":  2, "mechanism": "民意与选票压力促使政府出手干预"},
        {"source_id": "POLICY_INTERVENTION",  "target_id": "PRICE_SPIRAL",         "weight": -0.35, "delay_months":  3, "mechanism": "价格上限与补贴压制通胀螺旋（调节回路）"},
        {"source_id": "SUPPLY_CHOKE",         "target_id": "SUBSTITUTION_ACCEL",   "weight":  0.72, "delay_months":  6, "mechanism": "被卡脖子环节倒逼替代方案研发加速"},
        {"source_id": "SUBSTITUTION_ACCEL",   "target_id": "MANUFACTURING_MARGIN", "weight":  0.50, "delay_months": 18, "mechanism": "替代技术成熟后重新拉中下游利润率（强化回路）"},
        {"source_id": "CRISIS_TRIGGER",       "target_id": "GLOBAL_CAPITAL_FLOW",  "weight":  0.60, "delay_months":  1, "mechanism": "突发事件推动全球资本向避险资产与低风险区域聚集"}
    ],
    "personas": [
        {"persona_id": "SUPPLIER_BLOC",   "name": "上游供给方利益集团",  "strategy": "借机提价、延长账期、推动长协重签"},
        {"persona_id": "DOWNSTREAM_BLOC", "name": "中下游制造寡头",      "strategy": "向政府施压价格管控、加速替代方案、转移产能"},
        {"persona_id": "REGULATOR_BLOC",  "name": "各国监管与宏观当局",  "strategy": "价格上限、补贴、出口管制、战略储备释放"},
        {"persona_id": "FINANCIAL_BLOC",  "name": "全球资本与避险同盟",  "strategy": "加仓黄金美债、抄底被错杀标的、推动供应链重构基金"}
    ],
    "scenarios": [
        {"scenario_id": "SC_CRISIS_MANAGED",    "probability": 0.45, "time_horizon": "2026-2028", "narrative": "政策干预 + 替代技术双管齐下，危机被逐步吸收"},
        {"scenario_id": "SC_CRISIS_RELOCATES",  "probability": 0.35, "time_horizon": "2026-2029", "narrative": "供应链永久性重构，产能与资本外流成为新常态"},
        {"scenario_id": "SC_CRISIS_ESCALATES",  "probability": 0.20, "time_horizon": "2027",      "narrative": "次生危机引爆全球滞胀，央行陷入两难"}
    ]
}


class ThemeSynthesizer:
    """输入一句命题 → 自生完整主题 JSON → 可热插拔进 CausalNetwork 的合成器。"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.client = llm_client or LLMClient()

    # ------------------------------------------------------------------ #
    def synthesize_theme_from_prompt(self, prompt_text: str) -> Dict[str, Any]:
        """
        给定命题文本，返回标准主题 JSON。
        成功路径：调用 LLM → 解析 JSON → 过 schema 校验 → 输出。
        降级路径（API Key 未配置 / 网络异常 / JSON 结构异常）：
          返回 _GENERIC_CRISIS_TEMPLATE 深拷贝，并把 theme_name 改写成用户命题，
          确保永远不崩溃。
        """
        system_prompt = (
            "你是跨领域因果图谱设计师。给定一个命题，"
            "你需要产出一套完整的、能跑通复杂系统动力学仿真的因果图主题 JSON。"
            "保持节点领域多样，确保至少一组强化回路 + 一组调节回路。"
            + _THEME_SCHEMA_HINT
        )

        fallback = _inject_fallback_name(_GENERIC_CRISIS_TEMPLATE, prompt_text)

        if not self.client.available:
            return fallback

        try:
            raw = self.client.chat(
                system_prompt,
                f"命题：{prompt_text}\n请输出该命题对应的完整主题 JSON。",
                temperature=0.7,
                max_tokens=2500,
            )
            parsed = self._extract_json(raw)
            if parsed and self._validate_theme(parsed):
                # 用用户命题覆盖主题名，保持语义一致性
                parsed["theme_name"] = f"自生主题: {prompt_text[:24]}"
                return parsed
        except Exception:
            pass  # 网络/鉴权/JSON 解析/校验 任一环节失败 → 降级

        return fallback

    def save_theme(self, theme_data: Dict[str, Any], dir_override: Optional[str] = None) -> str:
        """持久化主题 JSON 到 config/themes/theme_custom_xxx.json，返回绝对路径。"""
        target_dir = dir_override or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "themes"
        )
        target_dir = os.path.abspath(target_dir)
        os.makedirs(target_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tid = (theme_data.get("theme_id", "THEME_CUSTOM")
               .replace(" ", "_")
               .replace("/", "_")
               .replace("\\", "_"))
        fname = f"theme_custom_{tid}_{tid.lower() if tid == 'THEME_CUSTOM' else ts}.json"
        fp = os.path.join(target_dir, fname)

        with open(fp, "w", encoding="utf-8") as f:
            json.dump(theme_data, f, ensure_ascii=False, indent=2)
        return fp

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """从原始输出里尽力抽取第一个完整合法的 JSON 对象。"""
        # 优先匹配 ```json ... ```
        fence = re.search(r"```json?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        # 否则找最外层 { ... }
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if not brace:
            return None
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            # 逐层回退，找到可解析的最大对象
            level = 0
            start = None
            for i, ch in enumerate(brace.group(0)):
                if ch == "{":
                    if level == 0:
                        start = i
                    level += 1
                elif ch == "}":
                    level -= 1
                    if level == 0 and start is not None:
                        try:
                            return json.loads(brace.group(0)[start:i + 1])
                        except json.JSONDecodeError:
                            return None
        return None

    @staticmethod
    def _validate_theme(theme: Dict[str, Any]) -> bool:
        """最低门槛校验：必需字段存在 + 节点数在 4-20 之间 + 边数 ≥ 4 + 至少一正一负权重。"""
        if not isinstance(theme, dict):
            return False
        nodes = theme.get("nodes")
        links = theme.get("links")
        personas = theme.get("personas")
        scenarios = theme.get("scenarios")
        if not isinstance(nodes, list) or not (4 <= len(nodes) <= 20):
            return False
        if not isinstance(links, list) or len(links) < 4:
            return False
        if not isinstance(personas, list) or len(personas) < 3:
            return False
        if not isinstance(scenarios, list) or len(scenarios) < 2:
            return False
        weights = [float(lk.get("weight", 0)) for lk in links]
        has_pos = any(w > 0 for w in weights)
        has_neg = any(w < 0 for w in weights)
        return has_pos and has_neg


def _inject_fallback_name(tpl: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """深拷贝兜底模板并把 theme_name 改为用户命题，保持降级风格语义对齐。"""
    import copy
    clone = copy.deepcopy(tpl)
    clone["theme_id"] = "THEME_GENERIC_FALLBACK"
    clone["theme_name"] = f"通用突发危机（降级模板 · 原命题: {prompt[:24]}）"
    clone["description"] = (
        f"命题「{prompt}」触发主题合成失败或 LLM 不可用，"
        "此处提供高拟真通用突发危机推演骨架作为兜底，可直接热插拔运行。"
    )
    return clone
