"""
Probabilistic Scenario Generation and Leading Indicator Engine.
Synthesizes network state and agent actions into calibrated future trajectory branches.

自适应设计：优先从 CausalNetwork.current_theme 读取主题自带的 scenarios 与 personas
（热插拔主题切换后自动同步），同时保留原 AI 能源主题的硬编码情景作为兜底回退。
"""
from typing import List, Dict, Any

from ..core.models import ScenarioOutcome, DomainCategory
from ..causal_engine.causal_network import CausalNetwork
from ..simulation.agent_sandbox import MultiAgentSandbox


def _bayes_calibrate(raw_scores: List[float]) -> List[float]:
    """贝叶斯启发式概率校准：分数归一化后总和 1。"""
    total = sum(raw_scores) or 1.0
    return [round(s / total, 2) for s in raw_scores]


class ScenarioForecastEngine:
    """Translates network state into probabilistic scenario branches."""

    def __init__(self, causal_net: CausalNetwork, sandbox: MultiAgentSandbox):
        self.causal_net = causal_net
        self.sandbox = sandbox

    # ------------------------------------------------------------------ #
    def generate_scenarios(self) -> List[ScenarioOutcome]:
        theme = self.causal_net.current_theme or {}
        nodes = self.causal_net.nodes_data
        theme_scenarios = theme.get("scenarios")

        if theme_scenarios:
            # ---- 路径 A：从主题配置直接取情景，概率用当前节点强度重算 ----
            return self._scenarios_from_theme(theme_scenarios, nodes)

        # ---- 路径 B：向后兼容原 AI 能源主题硬编码情景 ----
        return self._fallback_ai_energy_scenarios(nodes)

    # ------------------------------------------------------------------ #
    def _scenarios_from_theme(self,
                              theme_scenarios: List[Dict[str, Any]],
                              nodes: Dict[str, Any]) -> List[ScenarioOutcome]:
        """从主题配置构造 ScenarioOutcome 列表，概率基于节点强度重算。"""
        # 动态计算三个情景的概率：用各情景涉及的关键节点强度做启发式打分
        node_ids = set(nodes.keys())
        avg_intensity = sum(n.intensity for n in nodes.values()) / max(1, len(nodes))
        # 三个简单权重：情景 0（基准）= 平均强度，情景 1（过渡）= 最大强度×0.7，情景 2（尾部）= 1 - 平均强度
        scores = [avg_intensity, 0.7 * max(n.intensity for n in nodes.values()), 1.0 - avg_intensity]
        probs = _bayes_calibrate(scores)

        out: List[ScenarioOutcome] = []
        for i, sc in enumerate(theme_scenarios):
            title = sc.get("title") or sc.get("narrative", "")[:30]
            # 确保 title 保留情景类别前缀（若用户没写）
            if not any(tag in title for tag in ["基准", "主导", "尾部", "风险", "分流", "博弈"]):
                prefixes = ["【基准主导情景】", "【分流博弈情景】", "【尾部风险情景】"]
                title = f"{prefixes[i % 3]}「{title}」"
            # 构造 domain_impacts（从 personas/scenarios 隐含信息）
            domain_impacts: Dict[DomainCategory, str] = {
                DomainCategory.ECONOMY: sc.get("narrative", "")[:120],
            }
            # 用主题 nodes 自动生成 leading_indicators
            leading = self._build_leading_indicators(nodes)
            # 概率来自重算，但尊重用户原始 probability（若在 0.05~0.95 之间则做加权平均）
            raw_prob = float(sc.get("probability", 0))
            final_prob = raw_prob if 0.05 <= raw_prob <= 0.95 else probs[i]

            out.append(ScenarioOutcome(
                scenario_id=sc.get("scenario_id", f"SC_THEME_{i}"),
                title=title,
                probability=final_prob,
                time_horizon=sc.get("time_horizon", "2026-2028"),
                narrative=sc.get("narrative", title),
                leading_indicators=leading,
                domain_impacts=domain_impacts,
                key_bottlenecks=[],
            ))
        # 重新归一化保证总和 ≈ 1
        return self._renormalize(out)

    def _fallback_ai_energy_scenarios(self, nodes) -> List[ScenarioOutcome]:
        """原 AI 能源主题硬编码情景（向后兼容）。"""
        stress = nodes["GRID_TRANSMISSION_STRESS"].intensity
        nuclear_capex = nodes["CLEAN_NUCLEAR_PPA_CAPEX"].intensity
        migration = nodes["GLOBAL_COMPUTE_MIGRATION"].intensity
        regulation = nodes["REGULATORY_RESTRICTIONS"].intensity

        score_a = nuclear_capex * 0.6 + (1.0 - regulation) * 0.4
        score_b = migration * 0.5 + regulation * 0.5
        score_c = stress * 0.7 + (1.0 - nuclear_capex) * 0.3
        probs = _bayes_calibrate([score_a, score_b, score_c])

        return [
            ScenarioOutcome(
                scenario_id="SCENARIO_ALPHA_PRIVATE_MICROGRID",
                title="【基准主导情景】「离网核能与私有能源堡垒」闭环成型",
                probability=probs[0],
                time_horizon="2026 - 2029 年",
                narrative="科技巨头全面转向「自备能源」战略，算力基础设施演变为兼具发电与计算属性的现代重工业综合体。",
                leading_indicators=[
                    "大型科技企业直接控股 500MW+ 核电站超过 3 例",
                    "变电站重型变压器交付周期持续超过 36 个月",
                    "超算中心自发自用率（Off-Grid Ratio）首次突破 40%",
                ],
                domain_impacts={
                    DomainCategory.TECHNOLOGY: "万卡/十万卡集群顺利扩张，资本开支暴涨 50%。",
                    DomainCategory.ENERGY: "重构全球核能与清洁基荷资产估值，SMR 商业化提速 5 年。",
                    DomainCategory.POLITICS: "政府对科技巨头私有化公用事业产生反垄断担忧。",
                    DomainCategory.SOCIETY: "有效切断工业算力对民用电价的直接推升。",
                },
                key_bottlenecks=["SMR 监管审批与核燃料 HALEU 供应链"],
            ),
            ScenarioOutcome(
                scenario_id="SCENARIO_BETA_GLOBAL_MIGRATION",
                title="【分流博弈情景】「地方保护监管锁死与全球算力大迁徙」",
                probability=probs[1],
                time_horizon="2027 - 2030 年",
                narrative="地方选举与社区环保法律阻击取得上风，高昂合规成本倒逼算力架构向异步分布式演进。",
                leading_indicators=[
                    "至少 2 个算力核心州通过 30%+ 惩罚性附加税法案",
                    "跨境算力互联专线带宽容量同比增速突破 120%",
                    "阿联酋/挪威大型算力园区签约年增超 3GW",
                ],
                domain_impacts={
                    DomainCategory.TECHNOLOGY: "算力架构向异步分布式演进，CPO 产业迎来超预期增长。",
                    DomainCategory.POLITICS: "多国出台「算力主权法案」限制跨境数据训练。",
                    DomainCategory.ECONOMY: "资源型能源国向「算力代工经济体」转型。",
                },
                key_bottlenecks=["跨洲高速骨干光缆时延与数据安全审查摩擦"],
            ),
            ScenarioOutcome(
                scenario_id="SCENARIO_GAMMA_CASCADE_BLACKOUT",
                title="【尾部风险情景】「极端气候撞车算力峰值：区域性级联跳闸」",
                probability=probs[2],
                time_horizon="2026 - 2028 年极寒/酷夏窗口期",
                narrative="极端热浪/寒潮袭击电网腹地，居民负荷与 24 小时满载超算产生同频共振抢电。",
                leading_indicators=[
                    "区域电网运营准备金余量连续 3 天跌破 3%",
                    "超算集群主所在州夏季尖峰现货电价突破 $2,500/MWh",
                    "公用事业发布一级应急负荷强制削减警报",
                ],
                domain_impacts={
                    DomainCategory.TECHNOLOGY: "主流云厂商突发 48 小时全球性 API 中断。",
                    DomainCategory.SOCIETY: "激起强烈反 AI 公众舆论。",
                    DomainCategory.POLITICS: "联邦通过《核心公用基础设施电力配额法案》。",
                },
                key_bottlenecks=["老旧电网物理设备耐受极限与极端气候的非线性耦合"],
            ),
        ]

    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_leading_indicators(nodes: Dict[str, Any]) -> List[str]:
        """从当前主题节点动态生成先导指标，覆盖全部领域节点。"""
        sorted_nodes = sorted(nodes.values(), key=lambda n: n.intensity, reverse=True)
        hints = []
        for n in sorted_nodes[:3]:
            hints.append(f"「{n.name}」强度突破 {int(n.intensity * 100)}%，触发阈值预警")
        while len(hints) < 3:
            hints.append("待观察的系统关键指标（可在主题 JSON 中补充）")
        return hints

    @staticmethod
    def _renormalize(scenarios: List[ScenarioOutcome]) -> List[ScenarioOutcome]:
        total = sum(s.probability for s in scenarios) or 1.0
        renormed = []
        for s in scenarios:
            renormed.append(ScenarioOutcome(
                scenario_id=s.scenario_id,
                title=s.title,
                probability=round(s.probability / total, 2),
                time_horizon=s.time_horizon,
                narrative=s.narrative,
                leading_indicators=s.leading_indicators,
                domain_impacts=s.domain_impacts,
                key_bottlenecks=s.key_bottlenecks,
            ))
        return renormed
