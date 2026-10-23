"""
Probabilistic Scenario Generation and Leading Indicator Engine.
Synthesizes network state and agent actions into calibrated future trajectory branches.
"""
from typing import List, Dict
from ..core.models import ScenarioOutcome, DomainCategory
from ..causal_engine.causal_network import CausalNetwork
from ..simulation.agent_sandbox import MultiAgentSandbox


class ScenarioForecastEngine:
    """
    Translates simulation states into probabilistic scenario branches with leading indicators.
    """

    def __init__(self, causal_net: CausalNetwork, sandbox: MultiAgentSandbox):
        self.causal_net = causal_net
        self.sandbox = sandbox

    def generate_scenarios(self) -> List[ScenarioOutcome]:
        nodes = self.causal_net.nodes_data

        stress = nodes["GRID_TRANSMISSION_STRESS"].intensity
        nuclear_capex = nodes["CLEAN_NUCLEAR_PPA_CAPEX"].intensity
        migration = nodes["GLOBAL_COMPUTE_MIGRATION"].intensity
        regulation = nodes["REGULATORY_RESTRICTIONS"].intensity

        # Dynamic Bayesian-inspired probability calibration based on simulated node intensities
        score_a = nuclear_capex * 0.6 + (1.0 - regulation) * 0.4
        score_b = migration * 0.5 + regulation * 0.5
        score_c = stress * 0.7 + (1.0 - nuclear_capex) * 0.3

        total = score_a + score_b + score_c
        prob_a = round(score_a / total, 2)
        prob_b = round(score_b / total, 2)
        prob_c = round(1.0 - prob_a - prob_b, 2)

        scenarios = [
            ScenarioOutcome(
                scenario_id="SCENARIO_ALPHA_PRIVATE_MICROGRID",
                title="【基准主导情景】「离网核能与私有能源堡垒」闭环成型",
                probability=prob_a,
                time_horizon="2026 - 2029 年",
                narrative=(
                    "面对公共输配电网升级迟滞与变压器供应链短缺，科技巨头全面转向「自备能源（Behind-the-Meter）」战略。"
                    "超算中心不再被动等待公共电网扩容，而是通过深度注资重启封存核电站机组、批量部署新型小型模块化反应堆（SMR）"
                    "与长时地热微电网。算力基础设施演变为兼具发电与计算属性的现代独立重工业综合体。"
                ),
                leading_indicators=[
                    "大型科技企业直接控股或长期锁定 500MW+ 核电站全额发电量超过 3 例",
                    "变电站重型变压器交付等待周期持续超过 36 个月且订单排至 2030 年",
                    "超算中心新建项目「自发自用率（Off-Grid Ratio）」首次突破 40%"
                ],
                domain_impacts={
                    DomainCategory.TECHNOLOGY: "万卡/十万卡集群顺利扩张，模型迭代周期保持在 6-9 个月，但算力机房建设资本开支暴涨 50%。",
                    DomainCategory.ENERGY: "重构全球核能与清洁基荷资产估值，核反应堆延寿与 SMR 商业化提速至少 5 年。",
                    DomainCategory.POLITICS: "政府对大型跨国科技巨头私有化公用事业基础设施产生反垄断与能源安全担忧。",
                    DomainCategory.SOCIETY: "有效切断了工业算力对普通居民民用电价的直接推升，社区抗议声浪阶段性平抑。"
                },
                key_bottlenecks=["SMR 监管审批与核燃料（HALEU）供应链浓缩能力缺口"]
            ),
            ScenarioOutcome(
                scenario_id="SCENARIO_BETA_GLOBAL_MIGRATION",
                title="【分流博弈情景】「地方保护监管锁死与全球算力大迁徙」",
                probability=prob_b,
                time_horizon="2027 - 2030 年",
                narrative=(
                    "地方选举与社区环保法律阻击取得上风，多州颁布对数据中心供水、供电能耗的严格行政冻结令。"
                    "高昂合规成本与限电惩罚倒逼模型巨头拆分算力架构：本地仅保留超低延迟边缘推理集群，"
                    "而对延迟不敏感的海量基础预训练与后训练任务，全线迁往中东（光伏超充集群）、北欧（低成本水电高寒区）及东南亚临海地带。"
                ),
                leading_indicators=[
                    "至少 2 个以上算力核心聚集州通过对数据中心新用电征收 30%+ 惩罚性附加税的法案",
                    "跨境算力互联专线带宽容量同比增速突破 120%",
                    "阿联酋、挪威等非传统科技中心的大型算力园区签约容量年增超 3GW"
                ],
                domain_impacts={
                    DomainCategory.TECHNOLOGY: "算力架构向异步分布式演进，跨洋高速专线与光互连（CPO）产业迎来超预期增长。",
                    DomainCategory.POLITICS: "地缘科技博弈复杂化，多国出台「算力主权法案（Compute Sovereignty Act）」限制跨境数据训练。",
                    DomainCategory.ECONOMY: "资源型能源国向「算力代工经济体」成功转型，传统科技重镇出现产业空心化隐患。"
                },
                key_bottlenecks=["跨洲高速骨干光缆时延损耗与跨境数据安全审查摩擦"]
            ),
            ScenarioOutcome(
                scenario_id="SCENARIO_GAMMA_CASCADE_BLACKOUT",
                title="【尾部风险情景】「极端气候撞车算力峰值：区域性级联跳闸与用电配给」",
                probability=prob_c,
                time_horizon="2026 - 2028 年极寒/酷夏窗口期",
                narrative=(
                    "极端热浪/寒潮袭击北美或欧洲电网腹地，居民降温采暖负荷与 24 小时满载超算中心产生同频共振抢电。"
                    "冗余备用率跌破 2%，多座关键变压器过热烧毁引发大范围级联跳闸停电。"
                    "地方政府紧急援引战时/应急状态法案，强行切断商业超算集群外供电，社会矛盾急剧激化并引发资本市场巨震。"
                ),
                leading_indicators=[
                    "区域电网运营准备金余量（Operating Reserve Margin）连续 3 天跌破 3% 红线",
                    "超算集群主要所在州夏季尖峰现货电价瞬间突破 $2,500/MWh 极值",
                    "公用事业机构正式向大型超算发布一级应急负荷强制削减警报（Level-1 Curtailment Notice）"
                ],
                domain_impacts={
                    DomainCategory.TECHNOLOGY: "主流云厂商突发长达 48 小时的全球性模型 API 中断，高估值 AI 资产剧烈回调。",
                    DomainCategory.SOCIETY: "激起强烈的反 AI 公众舆论，公众指责算法巨头掠夺基础生存公共资源。",
                    DomainCategory.POLITICS: "联邦紧急通过《核心公用基础设施电力配额法案》，对所有商业数据中心实施强制拉闸配给制度。"
                },
                key_bottlenecks=["老旧电网物理设备耐受极限与极端气候天气的非线性耦合"]
            )
        ]

        return scenarios
