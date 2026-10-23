"""collector: 每日国际大事情报采集层。

基于 feedparser / requests 从全球 RSS、API 与公开数据源拉取
科技、能源、政治、经济、社会五大维度的多模态原始情报，
输出符合 core 契约的原始事件流，供 ingestion 层消费。
"""
from .news_collector import DailyNewsCollector, GlobalEvent
from .market_data import MarketDataCollector, MarketQuote, CrossCheckFilter

__all__ = ["DailyNewsCollector", "GlobalEvent",
           "MarketDataCollector", "MarketQuote", "CrossCheckFilter"]
