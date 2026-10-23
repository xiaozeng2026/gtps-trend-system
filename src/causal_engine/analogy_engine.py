"""
历史因果波形镜像类比引擎（Historical Analogy Engine）。

将当前因果网络的领域强度分布与实时市场异动合成为特征向量，
与人类近百年重大战略危机基模库做加权余弦相似度匹配，
输出：最佳历史镜像母本、历史同构点、时代差异变量、历史演变推移线。
"""
import json
import math
import os
from typing import Any, Dict, List, Optional

from .causal_network import CausalNetwork


class HistoricalAnalogyEngine:
    """
    历史危机镜像匹配器。

    特征向量维度：6 个领域（technology/energy/politics/economy/society/ecology）
    的平均节点强度 + 1 维实时宏观市场风险指数（权重更高）。
    """

    # 向量维度顺序（与历史 JSON 的 domain_weights 键严格一致）
    DOMAIN_ORDER = ["technology", "energy", "politics", "economy", "society", "ecology"]

    # 各领域中文名（用于报告输出）
    DOMAIN_ZH = {
        "technology": "科技",
        "energy": "能源",
        "politics": "政治",
        "economy": "经济",
        "society": "社会",
        "ecology": "生态",
    }

    # 加权余弦的维度权重：市场异动维度权重更高（危机中金融市场是先行放大器）
    DIMENSION_WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5]

    # 同构/差异判定的强度阈值
    HIGH_THRESHOLD = 0.55
    LOW_THRESHOLD = 0.40

    def __init__(self, history_db_dir: Optional[str] = None):
        """扫描并加载历史危机基模库目录下的全部 JSON 档案。"""
        if history_db_dir is None:
            # 默认目录：项目根/data/history_db/
            history_db_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data", "history_db",
            )
        self.history_db_dir = history_db_dir
        self.history_records: List[Dict[str, Any]] = self._load_history_db(history_db_dir)

    @staticmethod
    def _load_history_db(db_dir: str) -> List[Dict[str, Any]]:
        records = []
        if not os.path.isdir(db_dir):
            return records
        for fname in sorted(os.listdir(db_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(db_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                # 基础校验：必须含 id/name/domain_weights
                if rec.get("id") and rec.get("domain_weights"):
                    rec["_source_file"] = fname
                    records.append(rec)
            except (json.JSONDecodeError, OSError):
                continue
        return records

    # ------------------------------------------------------------------
    # 特征向量合成
    # ------------------------------------------------------------------
    def _current_feature_vector(self, current_net: CausalNetwork,
                                market_risk_index: float) -> Dict[str, float]:
        """当前网络：各领域节点强度均值 + 市场风险指数，合成 7 维特征。"""
        domain_sum: Dict[str, float] = {d: 0.0 for d in self.DOMAIN_ORDER}
        domain_cnt: Dict[str, int] = {d: 0 for d in self.DOMAIN_ORDER}
        for node in current_net.nodes_data.values():
            d = node.domain.value.lower()
            if d in domain_sum:
                domain_sum[d] += node.intensity
                domain_cnt[d] += 1
        vec = {
            d: (domain_sum[d] / domain_cnt[d] if domain_cnt[d] > 0 else 0.0)
            for d in self.DOMAIN_ORDER
        }
        vec["market"] = max(0.0, min(1.0, market_risk_index))
        return vec

    def _history_feature_vector(self, record: Dict[str, Any]) -> Dict[str, float]:
        """历史危机：domain_weights + market_shock_intensity，合成 7 维特征。"""
        weights = record.get("domain_weights", {})
        vec = {
            d: max(0.0, min(1.0, float(weights.get(d, 0.0))))
            for d in self.DOMAIN_ORDER
        }
        vec["market"] = max(0.0, min(1.0, float(record.get("market_shock_intensity", 0.5))))
        return vec

    # ------------------------------------------------------------------
    # 加权余弦相似度
    # ------------------------------------------------------------------
    @classmethod
    def _weighted_cosine(cls, a: List[float], b: List[float]) -> float:
        """加权余弦相似度 ∈ [0, 1]（输入向量各维均非负）。"""
        w = cls.DIMENSION_WEIGHTS
        dot = sum(wi * ai * bi for wi, ai, bi in zip(w, a, b))
        na = math.sqrt(sum(wi * ai * ai for wi, ai in zip(w, a)))
        nb = math.sqrt(sum(wi * bi * bi for wi, bi in zip(w, b)))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    # ------------------------------------------------------------------
    # 同构点 / 差异变量提炼
    # ------------------------------------------------------------------
    def _extract_similarities(self, cur: Dict[str, float], hist: Dict[str, float],
                              record: Dict[str, Any]) -> List[str]:
        """历史同构点：当前与历史同时高压的领域 = 结构相同的传导主链。"""
        sims: List[str] = []
        for d in self.DOMAIN_ORDER:
            if cur[d] >= self.HIGH_THRESHOLD and hist[d] >= self.HIGH_THRESHOLD:
                sims.append(
                    f"【{self.DOMAIN_ZH[d]}】同构承压：当前强度 {cur[d]:.2f} ≈ 当年 {hist[d]:.2f}，"
                    f"均为危机传导主引擎"
                )
        if cur["market"] >= 0.5 and hist["market"] >= 0.5:
            sims.append(
                f"【金融市场】同步异动：当前风险指数 {cur['market']:.2f} ≈ 当年冲击 {hist['market']:.2f}，"
                f"资本定价已开始抢跑"
            )
        if not sims:
            # 退化情形：取双方最接近的两个领域作为弱同构
            diffs = sorted(self.DOMAIN_ORDER, key=lambda d: abs(cur[d] - hist[d]))
            for d in diffs[:2]:
                sims.append(
                    f"【{self.DOMAIN_ZH[d]}】弱同构：当前 {cur[d]:.2f} 与当年 {hist[d]:.2f} 量级接近"
                )
        return sims

    def _extract_divergences(self, cur: Dict[str, float], hist: Dict[str, float],
                             record: Dict[str, Any]) -> List[str]:
        """时代差异变量：现代阻尼（当年高危、当前已降温）+ 新增风险维度 + 基模内置抵消项。"""
        divs: List[str] = []
        # 1. 现代吸收阻尼：历史高压但当前低压的领域
        for d in self.DOMAIN_ORDER:
            if hist[d] >= self.HIGH_THRESHOLD and cur[d] < self.LOW_THRESHOLD:
                divs.append(
                    f"【{self.DOMAIN_ZH[d]}】当年为高危传导区（{hist[d]:.2f}），"
                    f"当前显著降温（{cur[d]:.2f}）——现代体系对该链路具备吸收阻尼"
                )
        # 2. 新增风险维度：当前高压但历史低压（当年不存在的新变量）
        for d in self.DOMAIN_ORDER:
            if cur[d] >= self.HIGH_THRESHOLD and hist[d] < self.LOW_THRESHOLD:
                divs.append(
                    f"【{self.DOMAIN_ZH[d]}】当年并非主战场（{hist[d]:.2f}），"
                    f"当前却高度承压（{cur[d]:.2f}）——警惕历史剧本未覆盖的新传导路径"
                )
        # 3. 基模内置的现代抵消异变量（取前 3 条）
        for offset in record.get("modern_offsets", [])[:3]:
            divs.append(f"【现代对冲】{offset}")
        return divs

    # ------------------------------------------------------------------
    # 核心匹配入口
    # ------------------------------------------------------------------
    def match_historical_crisis(self, current_net: CausalNetwork,
                                market_risk_index: float = 0.0) -> Dict[str, Any]:
        """
        将当前网络拓扑与全部历史危机逐一比对，输出最佳镜像母本及三项关键解读。

        返回结构：
        {
          "top_match": {id, name, era, trigger_event, similarity, similarity_pct},
          "ranking": [{id, name, similarity, similarity_pct}, ...],   # 全部按相似度降序
          "similarities": [...],          # 历史同构点
          "modern_divergences": [...],    # 时代差异变量
          "historical_trajectory": [...], # 历史演变推移线（阶段参照）
          "current_vector": {...}, "history_vector": {...},
        }
        """
        cur = self._current_feature_vector(current_net, market_risk_index)
        cur_list = [cur[d] for d in self.DOMAIN_ORDER] + [cur["market"]]

        scored: List[Dict[str, Any]] = []
        for rec in self.history_records:
            hv = self._history_feature_vector(rec)
            hist_list = [hv[d] for d in self.DOMAIN_ORDER] + [hv["market"]]
            sim = self._weighted_cosine(cur_list, hist_list)
            scored.append({"record": rec, "history_vector": hv, "similarity": sim})

        scored.sort(key=lambda x: x["similarity"], reverse=True)

        ranking = [
            {
                "id": s["record"]["id"],
                "name": s["record"]["name"],
                "similarity": round(s["similarity"], 4),
                "similarity_pct": f"{s['similarity'] * 100:.1f}%",
            }
            for s in scored
        ]

        if not scored:
            return {
                "top_match": None,
                "ranking": [],
                "similarities": [],
                "modern_divergences": ["历史基模库为空，无法执行镜像类比"],
                "historical_trajectory": [],
                "current_vector": cur,
                "history_vector": {},
            }

        best = scored[0]
        rec, hv = best["record"], best["history_vector"]

        return {
            "top_match": {
                "id": rec["id"],
                "name": rec["name"],
                "era": rec.get("era", ""),
                "trigger_event": rec.get("trigger_event", ""),
                "similarity": round(best["similarity"], 4),
                "similarity_pct": f"{best['similarity'] * 100:.1f}%",
            },
            "ranking": ranking,
            "similarities": self._extract_similarities(cur, hv, rec),
            "modern_divergences": self._extract_divergences(cur, hv, rec),
            "historical_trajectory": rec.get("historical_timeline", []),
            "current_vector": cur,
            "history_vector": hv,
        }
