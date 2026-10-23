"""
LLM 驱动的多主体红蓝对抗战略推演引擎（LLM War-Gaming Engine）。

当捕获重大国际事件或突发冲击时，4 个代表不同利益集团的「专属参谋部」
以三轮辩论（立场宣告 → 交叉施压 → 闭门决议）展开博弈，
最终输出量化因果冲击向量（AgentDecision 列表）与《战略闭门圆桌博弈纪要》。

智能降级保护：未配置 API Key 或网络不可用时，自动切换至内置高拟真参谋部
辩论模板，系统永不崩溃、无 Key 也能完整体验全部三轮流程。
"""
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import requests

from ..core.models import AgentDecision

# 因果网络中的 8 个核心节点 ID（与 causal_engine 预设拓扑严格对齐，勿改）
# 注意：主题切换后实际可用节点会不同，由 run_wargame_session 传入 available_nodes 动态覆盖
DEFAULT_NODES = (
    "AI_COMPUTE_DEMAND", "DATACENTER_POWER_LOAD", "GRID_TRANSMISSION_STRESS",
    "POWER_WHOLESALE_PRICE", "LOCAL_COMMUNITY_RESISTANCE",
    "REGULATORY_RESTRICTIONS", "CLEAN_NUCLEAR_PPA_CAPEX", "GLOBAL_COMPUTE_MIGRATION",
)

# 单项战术动作对单个节点冲击幅度的安全钳制区间
DELTA_CLAMP = 0.50


class LLMClient:
    """OpenAI 兼容接口的通用调用客户端（DeepSeek / Qwen / Kimi / OpenAI 等）。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        model_name: str = "deepseek-chat",
        timeout: int = 30,
    ):
        # 显式传参优先，其次按常见环境变量顺序探测
        self.api_key = api_key or (
            os.environ.get("LLM_API_KEY")
            or os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("DASHSCOPE_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout

    @property
    def available(self) -> bool:
        """是否具备发起真实调用的最小条件（已配置 Key）。"""
        return bool(self.api_key)

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.8, max_tokens: int = 800) -> str:
        """发起一次对话补全调用；任何失败均抛出 RuntimeError，由上层降级接管。"""
        if not self.available:
            raise RuntimeError("未配置 API Key")
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # 网络超时 / 鉴权失败 / 响应结构异常统一上抛
            raise RuntimeError(f"LLM 调用失败: {exc}") from exc


# ---------------------------------------------------------------------------
# 4 大利益集团参谋部设定（System Prompt + 内置降级模板）
# ---------------------------------------------------------------------------
PERSONAS: Dict[str, Dict] = {
    "TECH_HYPERSCALER": {
        "name": "全球算力与科技资本寡头·参谋部",
        "system_prompt": (
            "你是全球算力与科技资本寡头的首席战略参谋。性格激进、技术至上，对算力交付延误零容忍。"
            "你手握千亿资本，核心手腕：威胁若本地电网设卡，立即将核心算力迁往政策更友好的海外节点，"
            "并大力推进离网核电与私有微网建设。所有发言须强硬、数据化、带有最后期限色彩。"
            "使用中文，发言控制在 150 字以内。"
        ),
        # 内置降级模板：默认因果冲击向量（该主体的战术抓手）
        "vector": {"CLEAN_NUCLEAR_PPA_CAPEX": +0.25, "GLOBAL_COMPUTE_MIGRATION": +0.15, "DATACENTER_POWER_LOAD": +0.05},
        "opening_tpl": "【立场宣告】「{title}」已直接威胁我方季度算力交付红线。我方 72 小时内可启动备用资本池：要么本地电网 30 天内给出并网扩容承诺，要么核心训练集群即刻启动海外迁移评估，离网核电 PPA 谈判同步加速。",
        "debate_tpl": "【交叉施压】敬告电网守护者：N-1 红线不是无限期拖延的挡箭牌，我方每户数据中心愿付容量保证金，但拒绝为电网历史欠账买单。同时提醒监督委员会：算力外迁一旦启动，本地税基与高薪岗位将不可逆流失。",
        "action_name": "千亿资本双线反制（离网核电PPA + 海外迁移评估）",
    },
    "GRID_GUARDIAN": {
        "name": "区域电网与公用事业守护者·参谋部",
        "system_prompt": (
            "你是区域电网与公用事业公司的首席战略参谋。性格极端风险厌恶，坚持物理电网 N-1 安全红线高于一切商业利益。"
            "反制手腕：提高容量拍卖出清保证金、加征高耗能峰值附加费、以优先保障民用供电为由对算力负荷实施分级管控。"
            "所有发言须以电网物理约束与民生优先为核心论据。使用中文，发言控制在 150 字以内。"
        ),
        "vector": {"POWER_WHOLESALE_PRICE": +0.15, "REGULATORY_RESTRICTIONS": +0.10, "DATACENTER_POWER_LOAD": -0.10},
        "opening_tpl": "【立场宣告】「{title}」令我网峰谷差逼近 N-1 安全红线。我方即日起上调容量拍卖出清保证金，并对单点 100MW 以上负荷开征尖峰附加费——民用供电优先级永远高于任何商业算力合同。",
        "debate_tpl": "【交叉施压】回应科技寡头：迁移威胁对我方无效——电网是物理资产不是谈判筹码。若贵方坚持无序扩张，我方将启动负荷分级管控预案。同时建议监督委员会：并网审批必须与储能配套强制挂钩。",
        "action_name": "容量保证金上调 + 高耗能尖峰附加费开征",
    },
    "STATE_REGULATOR": {
        "name": "地方主权政府与公用事业监督委员会·参谋部",
        "system_prompt": (
            "你是地方政府与公用事业监督委员会的首席政策参谋。对选民政治压力高度敏感，背负环保考核硬约束。"
            "反制手腕：以反垄断、水资源与噪音环评为由发起立法调查，暂缓新建算力中心供地审批，出台能耗配额封顶。"
            "所有发言须体现选民利益、环保合规与程序正义。使用中文，发言控制在 150 字以内。"
        ),
        "vector": {"REGULATORY_RESTRICTIONS": +0.20, "LOCAL_COMMUNITY_RESISTANCE": +0.10, "AI_COMPUTE_DEMAND": -0.05},
        "opening_tpl": "【立场宣告】针对「{title}」，本委员会收到大量选民关于电费与水耗的投诉。即日起对辖区算力项目启动反垄断与环评双重审查，新建供地审批一律暂缓，能耗配额封顶方案进入立法快车道。",
        "debate_tpl": "【交叉施压】警告科技寡头：资本体量不构成豁免环评的理由，外迁威胁不会改变选票算术。同时要求电网守护者提交民生电价冲击评估——任何附加费最终不得转嫁给居民用户，否则委员会将行使否决权。",
        "action_name": "反垄断+环评双审查与能耗配额封顶立法",
    },
    "GLOBAL_ARBITRAGEUR": {
        "name": "中东与北欧地缘主权算力游说团·参谋部",
        "system_prompt": (
            "你是中东与北欧主权基金支持的算力招商游说团首席代表。性格精明，是纯粹的地缘套利者与国家资本利益代言人。"
            "核心手腕：以 2 美分/度的极低光伏/水电价格、十年免税与主权担保土地，游说算力巨头实施跨国大迁徙。"
            "所有发言须突出成本碾压优势与政策确定性。使用中文，发言控制在 150 字以内。"
        ),
        "vector": {"GLOBAL_COMPUTE_MIGRATION": +0.25, "DATACENTER_POWER_LOAD": -0.15, "GRID_TRANSMISSION_STRESS": -0.08},
        "opening_tpl": "【立场宣告】「{title}」正是全球算力版图重构的窗口期。我方正式报价：2 美分/度绿电、十年免税、主权基金担保的 GW 级园区，90 天即可完成首期交付——欢迎各家带着负荷来谈。",
        "debate_tpl": "【交叉施压】对科技寡头：您在本土每多耗一个季度，训练成本就多拉开一代差距，我们的园区即插即用。对监督委员会与电网：各位的博弈越激烈，我们的招商管道越拥挤——本周已有三家 hyperscaler 索取意向书。",
        "action_name": "2美分绿电+免税一揽子招商报价攻势",
    },
}

# 第三轮要求 LLM 输出因果向量的格式指令（追加在用户提示末尾）
def _vector_format_hint(available_nodes: tuple = DEFAULT_NODES) -> str:
    return (
        "\n\n最后必须独占一行输出因果冲击向量，格式严格为："
        '因果向量: {"节点ID": +/-0.xx}，节点 ID 只能从以下选取：' + ", ".join(available_nodes)
    )


@dataclass
class WarGameResult:
    """一场红蓝对抗推演的完整产出。"""
    event_title: str
    event_summary: str
    mode: str                       # "LIVE_LLM" 或 "BUILTIN_TEMPLATE"（降级）
    opening_statements: Dict[str, str] = field(default_factory=dict)
    cross_debate: Dict[str, str] = field(default_factory=dict)
    resolutions: Dict[str, str] = field(default_factory=dict)
    decisions: List[AgentDecision] = field(default_factory=list)
    briefing: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class LLMWarGameEngine:
    """多主体红蓝对抗战略推演引擎（真实 LLM 驱动 + 内置模板智能降级）。"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.client = llm_client or LLMClient()
        self.session_history: List[WarGameResult] = []

    # ------------------------------------------------------------------ #
    # 主流程：三轮辩论 + 决策提取 + 纪要生成
    # ------------------------------------------------------------------ #
    def run_wargame_session(self, event_title: str, event_summary: str,
                            progress_cb=None,
                            available_nodes: Optional[List[str]] = None) -> WarGameResult:
        """
        三轮红蓝对抗推演主流程。
        available_nodes: 当前主题可用的节点 ID 列表（动态覆盖硬编码 DEFAULT_NODES）；
        传入后 LLM 生成的因果向量和模板 vector 会按此过滤，避免主题切换后 KeyError。
        """
        _valid_nodes = tuple(available_nodes) if available_nodes else DEFAULT_NODES
        mode = "LIVE_LLM" if self.client.available else "BUILTIN_TEMPLATE"
        result = WarGameResult(event_title=event_title, event_summary=event_summary, mode=mode)

        # ---- 第一轮：危机态势研判与立场宣告 ----
        for pid, persona in PERSONAS.items():
            fallback = persona["opening_tpl"].format(title=event_title)
            result.opening_statements[pid] = self._speak(
                pid,
                f"今日突发国际事件：{event_title}\n事件详情：{event_summary}\n"
                f"请以你的参谋部身份发表本轮立场宣告（受影响研判 + 初步诉求）。",
                fallback,
                valid_nodes=_valid_nodes,
            )
            if mode == "LIVE_LLM" and result.opening_statements[pid] == fallback:
                # 首个真实调用即失败：整场降级为模板模式，保证风格一致
                mode = "BUILTIN_TEMPLATE"
                result.mode = mode
        if progress_cb:
            progress_cb("第一轮 · 危机态势研判与立场宣告完成（4 方参谋部已就位）")

        # ---- 第二轮：交叉辩论与反制施压（可见他方首轮立场） ----
        others_view = "\n".join(
            f"【{PERSONAS[pid]['name']}】{stmt}" for pid, stmt in result.opening_statements.items()
        )
        for pid, persona in PERSONAS.items():
            result.cross_debate[pid] = self._speak(
                pid,
                f"事件：{event_title}\n\n各方首轮立场如下：\n{others_view}\n\n"
                f"请针对与你利益冲突的其他主体进行点名施压、利益置换或发出最后通牒。",
                persona["debate_tpl"],
                valid_nodes=_valid_nodes,
            )
        if progress_cb:
            progress_cb("第二轮 · 交叉辩论与反制施压完成（点名交锋结束）")

        # ---- 第三轮：闭门决议，产出战术动作 + 量化因果向量 ----
        debate_view = "\n".join(
            f"【{PERSONAS[pid]['name']}】{stmt}" for pid, stmt in result.cross_debate.items()
        )
        for pid, persona in PERSONAS.items():
            text = self._speak(
                pid,
                f"事件：{event_title}\n\n交叉辩论实录：\n{debate_view}\n\n"
                f"请给出你方闭门博弈决议：一项具体战术行动（名称 + 100 字内执行要点）。",
                f"【闭门决议】执行「{persona['action_name']}」，即刻生效。",
                json_mode=True,
                valid_nodes=_valid_nodes,
            )
            result.resolutions[pid] = text
            result.decisions.extend(self._to_decisions(pid, text, valid_nodes=_valid_nodes))
        if progress_cb:
            progress_cb("第三轮 · 闭门博弈决议与因果冲击向量提取完成")

        result.briefing = self._compose_briefing(result)
        self.session_history.append(result)
        return result

    # ------------------------------------------------------------------ #
    # 将决议文本落地为对因果网络的干预（供外部编排层调用）
    # ------------------------------------------------------------------ #
    @staticmethod
    def apply_to_network(causal_net, decisions: List[AgentDecision]) -> None:
        """把博弈决议的因果冲击向量注入既有 CausalNetwork 并完成再平衡传导。"""
        for d in decisions:
            causal_net.apply_node_impulse(
                d.target_node_id, d.intervention_strength,
                reason=f"[红蓝对抗] {d.agent_id}: {d.action_name}",
            )
        causal_net.propagate_dynamics(steps=2)

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    def _speak(self, persona_id: str, user_prompt: str, fallback: str,
               json_mode: bool = False, valid_nodes: tuple = DEFAULT_NODES) -> str:
        """单主体发言：优先真实 LLM，任何失败无缝回退内置高拟真模板。"""
        if not self.client.available:
            return fallback
        prompt = user_prompt + (_vector_format_hint(valid_nodes) if json_mode else "")
        try:
            return self.client.chat(PERSONAS[persona_id]["system_prompt"], prompt)
        except RuntimeError:
            return fallback + (_vector_format_hint(valid_nodes) if json_mode else "")

    def _to_decisions(self, persona_id: str, resolution_text: str,
                      valid_nodes: tuple = DEFAULT_NODES) -> List[AgentDecision]:
        """从第三轮决议文本提取因果冲击向量，映射为 AgentDecision 列表。"""
        vector = self._extract_vector(resolution_text, persona_id, valid_nodes=valid_nodes)
        persona = PERSONAS[persona_id]
        return [
            AgentDecision(
                agent_id=persona_id,
                action_name=persona["action_name"],
                target_node_id=node_id,
                intervention_strength=delta,
                cost=round(abs(delta) * 10, 2),
                explanation=f"{persona['name']}闭门决议：{persona['action_name']}",
            )
            for node_id, delta in vector.items()
        ]

    @staticmethod
    def _extract_vector(text: str, persona_id: str,
                        valid_nodes: tuple = DEFAULT_NODES) -> Dict[str, float]:
        """从文本中解析「因果向量」JSON 块；解析失败回退该主体模板向量（过滤到 valid_nodes）。"""
        match = re.search(r"\{[^{}]*\}", text)
        if match:
            try:
                raw = json.loads(match.group(0))
                vector = {
                    k: max(-DELTA_CLAMP, min(DELTA_CLAMP, float(v)))
                    for k, v in raw.items() if k in valid_nodes
                }
                if vector:
                    return vector
            except (ValueError, TypeError):
                pass
        # 回退：过滤 PERSONAS 模板向量到当前 valid_nodes
        fallback = {k: v for k, v in PERSONAS[persona_id]["vector"].items() if k in valid_nodes}
        return fallback if fallback else dict(PERSONAS[persona_id]["vector"])

    @staticmethod
    def _compose_briefing(result: WarGameResult) -> str:
        """自动撰写高管级《战略闭门圆桌博弈纪要与内参决议》（Markdown）。"""
        mode_label = "真实 LLM 在线推演" if result.mode == "LIVE_LLM" else "内置参谋部模板（离线降级）"
        lines = [
            "# 战略闭门圆桌博弈纪要与内参决议",
            "",
            f"- **触发事件**：{result.event_title}",
            f"- **事件摘要**：{result.event_summary}",
            f"- **推演引擎模式**：{mode_label}",
            f"- **纪要生成时间**：{result.timestamp}",
            "",
            "## 一、首轮立场宣告（Opening Statements）",
        ]
        for pid, stmt in result.opening_statements.items():
            lines += ["", f"### {PERSONAS[pid]['name']}", stmt]
        lines += ["", "## 二、交叉辩论与反制施压（Cross-Debate）"]
        for pid, stmt in result.cross_debate.items():
            lines += ["", f"### {PERSONAS[pid]['name']}", stmt]
        lines += ["", "## 三、闭门博弈决议与量化因果冲击", "",
                  "| 博弈主体 | 战术行动 | 目标因果变量 | 冲击强度 |", "|---|---|---|---|"]
        for d in result.decisions:
            lines.append(
                f"| {PERSONAS[d.agent_id]['name']} | {d.action_name} | "
                f"`{d.target_node_id}` | {d.intervention_strength:+.2f} |"
            )
        lines += ["", "> 内参提示：上述冲击向量已可经 `apply_to_network` 注入因果网络，",
                  "> 建议结合情景树引擎复算三套未来情景的概率漂移。", ""]
        return "\n".join(lines)
