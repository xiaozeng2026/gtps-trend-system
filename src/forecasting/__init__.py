"""forecasting: 概率情景树与预警引擎。

融合因果动力学传播结果与多主体仿真轨迹，生成带概率权的
情景树（Scenario Tree），维护前瞻先导预警指标
（Leading Indicators）体系，输出分级预警信号与可视化数据。
"""
from .scenario_engine import ScenarioForecastEngine

__all__ = ["ScenarioForecastEngine"]
