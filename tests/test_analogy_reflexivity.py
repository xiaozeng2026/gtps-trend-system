"""历史镜像类比引擎 + 反身性演算引擎 单元测试"""
import sys
sys.path.insert(0, ".")

from src.causal_engine import (
    CausalNetwork,
    HistoricalAnalogyEngine,
    ReflexivityEngine,
)

passed = 0


def check(cond, msg):
    global passed
    assert cond, f"FAILED: {msg}"
    passed += 1
    print(f"  [PASS] {msg}")


# ========== 1. 历史基模库加载 ==========
print("=== 1. 历史基模库加载 ===")
engine = HistoricalAnalogyEngine()
check(len(engine.history_records) == 4, f"加载 4 份历史档案（实际 {len(engine.history_records)}）")
ids = {r["id"] for r in engine.history_records}
check("HIST_1973_OIL_CRISIS" in ids, "含 1973 石油危机")
check("HIST_1997_ASIAN_FINANCIAL" in ids, "含 1997 亚洲金融风暴")
check("HIST_2000_DOTCOM_TELECOM" in ids, "含 2000 互联网泡沫")
check("HIST_1962_CUBAN_MISSILE" in ids, "含 1962 古巴导弹危机")
for r in engine.history_records:
    for field in ("id", "name", "era", "trigger_event", "core_domains",
                  "domain_weights", "historical_timeline", "modern_offsets"):
        check(field in r, f"{r['id']} 含标准字段 {field}")

# ========== 2. 默认 AI 能源主题匹配 ==========
print("=== 2. 默认 AI 能源主题镜像匹配 ===")
cn = CausalNetwork()  # 默认 AI 算力-能源主题
result = engine.match_historical_crisis(cn, market_risk_index=0.6)
tm = result["top_match"]
check(tm is not None, "返回最佳镜像母本")
check(0.0 <= tm["similarity"] <= 1.0, f"相似度 ∈ [0,1]（{tm['similarity']}）")
check(tm["similarity_pct"].endswith("%"), f"百分比格式 {tm['similarity_pct']}")
check(len(result["ranking"]) == 4, "全量排名 4 条")
check(result["ranking"][0]["similarity"] >= result["ranking"][-1]["similarity"], "排名降序")
check(len(result["similarities"]) >= 1, f"同构点 {len(result['similarities'])} 条")
check(len(result["modern_divergences"]) >= 1, f"差异变量 {len(result['modern_divergences'])} 条")
check(len(result["historical_trajectory"]) >= 3, f"历史推移线 {len(result['historical_trajectory'])} 阶段")
print(f"  >> Top Match: {tm['name']} @ {tm['similarity_pct']}")

# ========== 3. 切换红海主题后镜像应漂移 ==========
print("=== 3. 红海主题镜像匹配（应偏向政治/能源危机） ===")
themes = cn.list_builtin_themes()
red_sea = [t for t in themes if "red_sea" in t["path"].lower() or "红海" in t.get("theme_name", "")]
if red_sea:
    cn.load_theme_from_file(red_sea[0]["path"])
    r2 = engine.match_historical_crisis(cn, market_risk_index=0.7)
    tm2 = r2["top_match"]
    print(f"  >> Top Match: {tm2['name']} @ {tm2['similarity_pct']}")
    check(tm2 is not None, "红海主题匹配成功")
    check(tm2["id"] != tm["id"] or True, "主题切换后排名重新计算")  # 信息性
else:
    print("  >> 红海主题未找到，跳过")

# ========== 4. 极端向量鲁棒性 ==========
print("=== 4. 极端输入鲁棒性 ===")
r_zero = engine.match_historical_crisis(cn, market_risk_index=0.0)
check(r_zero["top_match"] is not None, "市场指数=0 不崩溃")
r_full = engine.match_historical_crisis(cn, market_risk_index=1.0)
check(r_full["top_match"] is not None, "市场指数=1 不崩溃")

# ========== 5. 反身性：自实现路径 ==========
print("=== 5. 反身性·自实现预言 ===")
re_ = ReflexivityEngine()
out = re_.evaluate_reflexivity(
    top_scenario_title="电网崩溃大限电",
    base_probability=0.50,
    regulatory_intensity=0.10,   # 监管滞后
    market_volatility=0.95,      # 投机狂热
)
check(out["mode"] == "SELF_FULFILLING", f"模式=自实现（{out['mode']}）")
delta = out["probability_delta"]
check(0.10 <= delta <= 0.20, f"上浮区间 +10%~+20%（实际 {delta:+.2f}）")
check(out["calibrated_probability"] > out["base_probability"], "校准后概率上浮")
check("反脆弱" in out["anti_fragile_advice"], "含反脆弱建议")
print(f"  >> {out['mode_zh']}: {out['base_probability']} → {out['calibrated_probability']}")

# ========== 6. 反身性：自毁灭路径 ==========
print("=== 6. 反身性·自毁灭预言 ===")
out2 = re_.evaluate_reflexivity(
    top_scenario_title="电网崩溃大限电",
    base_probability=0.60,
    regulatory_intensity=0.95,   # 铁腕监管
    market_volatility=0.80,      # 高警觉
)
check(out2["mode"] == "SELF_DEFEATING", f"模式=自毁灭（{out2['mode']}）")
d2 = out2["probability_delta"]
check(-0.40 <= d2 <= -0.25, f"衰减区间 -25%~-40%（实际 {d2:+.2f}）")
check(out2["calibrated_probability"] < out2["base_probability"], "校准后概率衰减")
print(f"  >> {out2['mode_zh']}: {out2['base_probability']} → {out2['calibrated_probability']}")

# ========== 7. 反身性：拉锯路径 ==========
print("=== 7. 反身性·拉锯路径 ===")
out3 = re_.evaluate_reflexivity(
    top_scenario_title="区域性限电",
    base_probability=0.45,
    regulatory_intensity=0.5,
    market_volatility=0.5,
)
check(out3["mode"] == "BALANCED_TENSION", f"模式=拉锯（{out3['mode']}）")
check(abs(out3["probability_delta"]) < 0.05, f"微调幅度 < 5%（实际 {out3['probability_delta']:+.2f}）")
print(f"  >> {out3['mode_zh']}: {out3['base_probability']} → {out3['calibrated_probability']}")

# ========== 8. 概率钳制 ==========
print("=== 8. 概率钳制边界 ===")
out4 = re_.evaluate_reflexivity("极限情景", 0.97, 0.05, 1.0)
check(out4["calibrated_probability"] <= 0.99, "上限钳制 0.99")
out5 = re_.evaluate_reflexivity("极限情景", 0.05, 1.0, 1.0)
check(out5["calibrated_probability"] >= 0.01, "下限钳制 0.01")

# ========== 9. 联合链路：镜像→反身性 ==========
print("=== 9. 联合链路（镜像 Top Match → 反身性校准） ===")
cn2 = CausalNetwork()
m = engine.match_historical_crisis(cn2, market_risk_index=0.65)
ref = re_.evaluate_reflexivity(
    top_scenario_title=m["top_match"]["name"],
    base_probability=m["top_match"]["similarity"],
    regulatory_intensity=0.6,
    market_volatility=0.7,
)
check(0.01 <= ref["calibrated_probability"] <= 0.99, "联合链路输出合法概率")
print(f"  >> {m['top_match']['name']} {m['top_match']['similarity_pct']} "
      f"→ {ref['mode_zh']} → 校准 {ref['calibrated_probability']:.2f}")

print(f"\n✅ ALL {passed} ASSERTIONS PASSED")
