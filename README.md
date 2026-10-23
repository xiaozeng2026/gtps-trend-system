# GTPS — 全球人类社会趋势预判系统
**Global Trend Prediction System**

> 人类社会是一个高阶非线性自适应系统。GTPS 摆脱传统线性预测范式，
> 通过「全源感知 → 因果建模 → 博弈仿真 → 概率预警」的闭环管线，
> 对跨领域宏观趋势进行结构化推演与前瞻性预警。

---

## 一、核心设计理念

| 支柱 | 说明 |
| --- | --- |
| 1. 多模态全源情报感知 | 覆盖科技、能源、政治、经济、社会五大维度的每日国际大事采集 |
| 2. 跨域因果网络图谱 | 以 Causal Graph 刻画跨领域传导路径，显式建模系统内生闭环反馈（Feedback Loops） |
| 3. 多主体博弈仿真沙盒 | 将国家/企业/监管/市场抽象为自适应 Agent，推演资源博弈与政策响应的涌现均衡 |
| 4. 概率情景树与先导预警 | 输出带概率权的情景分支，维护 Leading Indicators 体系实现分级预警 |

**首期 MVP 验证命题：**

```
前沿 AI 算力激增
    ➔ 区域电网与清洁能源承载极限
        ➔ 关键资源博弈与政策限制
            ➔ 社会经济外溢
```

## 二、工程拓扑

```
人类社会趋势预判系统/
├── requirements.txt          # 核心依赖清单
├── README.md
├── src/
│   ├── core/                 # 数据模型与枚举定义（Pydantic 契约，全系统共享）
│   ├── collector/            # 每日国际大事情报采集（RSS/API 多源拉取）
│   ├── ingestion/            # 多模态特征提取管线（清洗/实体/量化/时序对齐）
│   ├── causal_engine/        # 跨域因果拓扑与动力学引擎（networkx 图谱 + 反馈环）
│   ├── simulation/           # 多主体博弈仿真沙盒（Agent 策略推演）
│   └── forecasting/          # 概率情景树与预警引擎（Leading Indicators）
└── data/                     # 持久化推演结果（事件库/图谱快照/情景树/预警记录）
```

## 三、数据流与运行逻辑

```
[全球情报源]
     │  RSS / API / 公开数据
     ▼
collector ──原始事件流──▶ ingestion ──标准化信号(Signal)──▶ causal_engine
                                                              │ 因果传播 + 反馈环
                                                              ▼
                                    forecasting ◀──仿真轨迹── simulation
                                         │
                                         ▼
                              概率情景树 + 分级预警 ──▶ data/ 持久化
                                         │
                                         ▼
                              Streamlit 可视化大屏
```

分层职责约束：

- **core** 不依赖任何上层模块，只定义契约；其余各层仅通过 core 的类型通信。
- **collector / ingestion** 无状态，可独立调度（每日批处理）。
- **causal_engine** 是唯一允许修改图谱拓扑的层；simulation 只读图谱。
- **forecasting** 聚合因果传播结果与仿真轨迹，产出最终可解释的概率情景。

## 四、快速开始

### 1. 环境要求
- Python ≥ 3.10

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 模块依赖关系

| 模块 | 关键依赖 | 职责关键词 |
| --- | --- | --- |
| core | pydantic | Event / Signal / CausalEdge / Scenario 契约 |
| collector | feedparser, requests | 多源情报拉取 |
| ingestion | pandas, pydantic | 特征提取与信号标准化 |
| causal_engine | networkx | 图谱拓扑、反馈环识别、动力学传播 |
| simulation | networkx, pandas | Agent 博弈推演 |
| forecasting | pandas, networkx | 情景树生成、先导指标预警 |

### 4. 可视化大屏与演示

```bash
streamlit run app.py        # Streamlit 可视化大屏
python run_demo.py          # 端到端推演演示（采集→因果→仿真→预警）
```

## 五、路线图

- [x] 阶段一：项目骨架与核心依赖
- [ ] 阶段二：core 数据契约与 collector 情报采集 MVP
- [ ] 阶段三：ingestion 特征管线 + causal_engine 因果图谱 MVP
- [ ] 阶段四：simulation 算力-电力-政策三方博弈沙盒
- [ ] 阶段五：forecasting 情景树 + Streamlit 预警大屏
