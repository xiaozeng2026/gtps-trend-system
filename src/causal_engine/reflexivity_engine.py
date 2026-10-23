"""
索罗斯反身性（Reflexivity）二级演算引擎。

核心思想：当某个危机情景被社会普遍预期后，"预期本身"会反过来改变现实——
  · 自实现预言（Self-Fulfilling）：资本抢跑囤积避险 → 挤兑加速 → 危机时间线提前、概率上浮；
  · 自毁灭预言（Self-Defeating）：监管与民意警觉 → 提前拆弹对冲 → 危机被反向化解、概率衰减。

本引擎对市场一致性预期形成后的"二级人类行为反弹"做量化修正，
输出反身性演化模式、校准后真实概率与一条反脆弱决策建议。
"""
from typing import Any, Dict


class ReflexivityEngine:
    """索罗斯反身性演算器：一级概率 → 预期反馈 → 二级真实概率。"""

    # 模式判定裕度：两股反身性驱动力之差超过该值才定性，否则视为拉锯
    MODE_MARGIN = 0.10

    # 自实现概率上浮区间：+10% ~ +20%
    SELF_FULFILL_SHIFT_MIN = 0.10
    SELF_FULFILL_SHIFT_MAX = 0.20

    # 自毁灭概率衰减区间：-25% ~ -40%
    SELF_DEFEAT_SHIFT_MIN = 0.25
    SELF_DEFEAT_SHIFT_MAX = 0.40

    # 输出概率钳制边界
    PROB_FLOOR = 0.01
    PROB_CEIL = 0.99

    @staticmethod
    def _clamp01(x: float) -> float:
        return max(0.0, min(1.0, float(x)))

    def evaluate_reflexivity(self,
                             top_scenario_title: str,
                             base_probability: float,
                             regulatory_intensity: float,
                             market_volatility: float) -> Dict[str, Any]:
        """
        反身性二级演算。

        参数：
          top_scenario_title: 当前最高概率情景标题（用于报告语境）
          base_probability:   一级（静态推演）概率 ∈ [0,1]
          regulatory_intensity: 监管干预强度 ∈ [0,1]（越高越可能政策拆弹）
          market_volatility:  市场波动/投机热度 ∈ [0,1]（越高越可能资本抢跑）

        返回：
          {
            "mode": "SELF_FULFILLING" | "SELF_DEFEATING" | "BALANCED_TENSION",
            "mode_zh": "自实现预言·挤兑加速" | "自毁灭预言·政策拆弹" | "反身性拉锯·弱反馈",
            "scenario": 情景标题,
            "base_probability": 原始概率,
            "calibrated_probability": 反身性校准后概率,
            "probability_delta": 校准位移（带符号）,
            "drives": {"self_fulfilling": x, "self_defeating": y},
            "reasoning": 演算逻辑说明,
            "anti_fragile_advice": 反脆弱决策建议,
          }
        """
        base = self._clamp01(base_probability)
        reg = self._clamp01(regulatory_intensity)
        vol = self._clamp01(market_volatility)

        # ---- 两股反身性驱动力建模 ----
        # 自实现驱动力：投机热度高 × 监管滞后（1-reg）→ 资本抢先囤积避险，危机自我加速
        self_fulfilling_drive = vol * (1.0 - reg)
        # 自毁灭驱动力：监管强度 × 民意警觉度（波动本身即警报）——两者相乘，
        # 必须"监管有能力"且"民意有警觉"同时成立，拆弹合力才真正形成
        self_defeating_drive = reg * vol

        margin = self_fulfilling_drive - self_defeating_drive

        if margin > self.MODE_MARGIN:
            # ===== 自实现预言：挤兑加速 =====
            mode, mode_zh = "SELF_FULFILLING", "自实现预言·挤兑加速"
            shift = self.SELF_FULFILL_SHIFT_MIN + (
                self.SELF_FULFILL_SHIFT_MAX - self.SELF_FULFILL_SHIFT_MIN
            ) * self_fulfilling_drive
            calibrated = min(self.PROB_CEIL, base + shift)
            reasoning = (
                f"市场投机热度 {vol:.2f} 高企而监管响应 {reg:.2f} 滞后，"
                f"一致性预期触发资本抢跑：避险囤积与空头挤压使『{top_scenario_title}』"
                f"的传导时间线提前，概率上浮 {shift * 100:+.1f}%。"
            )
            advice = (
                "【反脆弱·抢先锁定】恐慌定价尚未完全形成，立即对关键资源/供应链签订长约锁价，"
                "配置深度虚值看跌等尾部对冲；切忌在挤兑中段追高避险资产——"
                "抢跑者赚的是后知后觉者的恐慌溢价。"
            )
        elif margin < -self.MODE_MARGIN:
            # ===== 自毁灭预言：政策拆弹 =====
            mode, mode_zh = "SELF_DEFEATING", "自毁灭预言·政策拆弹"
            shift = self.SELF_DEFEAT_SHIFT_MIN + (
                self.SELF_DEFEAT_SHIFT_MAX - self.SELF_DEFEAT_SHIFT_MIN
            ) * self_defeating_drive
            calibrated = max(self.PROB_FLOOR, base - shift)
            reasoning = (
                f"监管强度 {reg:.2f} 与社会警觉度同步拉满，预期本身倒逼政策前置："
                f"对冲法案与防范准备在危机落地前先行拆弹，『{top_scenario_title}』"
                f"被反向化解，概率衰减 {-shift * 100:.1f}%。"
            )
            advice = (
                "【反脆弱·逆向布局】政策拆弹将造成避险资产超涨与风险资产错杀，"
                "分批建仓被错杀的优质风险资产；但保留 15% 弹药防范『政策失效尾部』——"
                "拆弹失败时危机将以杠杆化形式回归。"
            )
        else:
            # ===== 反身性拉锯：两股力量对冲 =====
            mode, mode_zh = "BALANCED_TENSION", "反身性拉锯·弱反馈"
            # 残余净位移（方向不定，量级减半）
            shift = margin * 0.15
            calibrated = min(self.PROB_CEIL, max(self.PROB_FLOOR, base + shift))
            reasoning = (
                f"资本抢跑驱动（{self_fulfilling_drive:.2f}）与政策拆弹驱动（{self_defeating_drive:.2f}）"
                f"势均力敌，预期反馈陷入拉锯，『{top_scenario_title}』概率仅微调 {shift * 100:+.1f}%，"
                f"维持一级推演基准判断。"
            )
            advice = (
                "【反脆弱·杠铃策略】85% 仓位配置抗波动的确定性资产（短债、现金流资产），"
                "15% 仓位同时押注两端尾部（危机加速 + 政策超预期），"
                "回避一切『中等风险中等收益』的模糊暴露。"
            )

        return {
            "mode": mode,
            "mode_zh": mode_zh,
            "scenario": top_scenario_title,
            "base_probability": round(base, 4),
            "calibrated_probability": round(calibrated, 4),
            "probability_delta": round(calibrated - base, 4),
            "drives": {
                "self_fulfilling": round(self_fulfilling_drive, 4),
                "self_defeating": round(self_defeating_drive, 4),
            },
            "reasoning": reasoning,
            "anti_fragile_advice": advice,
        }
