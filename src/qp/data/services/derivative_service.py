# qp/data/services/derivative_service.py
"""
衍生数据服务

提供公告、新闻情绪、研报、资金流、板块/主题、龙虎榜等衍生数据的业务逻辑
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from .base import BaseDataService
from ..providers.derivative_provider import DerivativeProvider, MockDerivativeProvider
from ..types.derivative import (
    AnnouncementData, NewsSentimentData, ResearchReportData,
    CapitalFlowData, ThemeData, DragonTigerData,
    AnnouncementType, NewsSentiment, ReportType, ReportRating,
    FlowType, FlowDirection, ThemeType, DragonTigerType, DragonTigerReason
)


class DerivativeDataService(BaseDataService):
    """衍生数据服务"""
    
    def __init__(self, provider: Optional[DerivativeProvider] = None):
        """
        初始化衍生数据服务
        
        Args:
            provider: 数据提供者，如果为None则使用默认提供者
        """
        super().__init__()
        self.provider = provider or MockDerivativeProvider()
    
    def get_announcements(self, symbol: str, start_date: str, end_date: str, 
                         announcement_type: Optional[str] = None,
                         importance_min: int = 1) -> List[AnnouncementData]:
        """
        获取公告数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            announcement_type: 公告类型过滤
            importance_min: 最小重要性等级
            
        Returns:
            公告数据列表
        """
        announcements = self.provider.get_announcements(
            symbol, start_date, end_date, announcement_type
        )
        
        # 过滤重要性等级
        if importance_min > 1:
            announcements = [ann for ann in announcements if ann.importance >= importance_min]
        
        return announcements
    
    def get_important_announcements(self, symbol: str, start_date: str, end_date: str) -> List[AnnouncementData]:
        """获取重要公告数据"""
        return self.get_announcements(symbol, start_date, end_date, importance_min=4)
    
    def get_news_sentiments(self, symbol: str, start_date: str, end_date: str,
                           sentiment: Optional[str] = None,
                           confidence_min: float = 0.5) -> List[NewsSentimentData]:
        """
        获取新闻情绪数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            sentiment: 情绪类型过滤
            confidence_min: 最小置信度
            
        Returns:
            新闻情绪数据列表
        """
        sentiments = self.provider.get_news_sentiments(
            symbol, start_date, end_date, sentiment
        )
        
        # 过滤置信度
        if confidence_min > 0:
            sentiments = [sent for sent in sentiments if sent.confidence >= confidence_min]
        
        return sentiments
    
    def get_positive_sentiments(self, symbol: str, start_date: str, end_date: str) -> List[NewsSentimentData]:
        """获取正面情绪新闻"""
        return self.get_news_sentiments(symbol, start_date, end_date, sentiment="positive")
    
    def get_negative_sentiments(self, symbol: str, start_date: str, end_date: str) -> List[NewsSentimentData]:
        """获取负面情绪新闻"""
        return self.get_news_sentiments(symbol, start_date, end_date, sentiment="negative")
    
    def get_research_reports(self, symbol: str, start_date: str, end_date: str,
                            report_type: Optional[str] = None,
                            rating: Optional[str] = None) -> List[ResearchReportData]:
        """
        获取研报数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            report_type: 研报类型过滤
            rating: 评级过滤
            
        Returns:
            研报数据列表
        """
        return self.provider.get_research_reports(
            symbol, start_date, end_date, report_type, rating
        )
    
    def get_buy_reports(self, symbol: str, start_date: str, end_date: str) -> List[ResearchReportData]:
        """获取买入评级研报"""
        return self.get_research_reports(symbol, start_date, end_date, rating="buy")
    
    def get_sell_reports(self, symbol: str, start_date: str, end_date: str) -> List[ResearchReportData]:
        """获取卖出评级研报"""
        return self.get_research_reports(symbol, start_date, end_date, rating="sell")
    
    def get_capital_flows(self, symbol: str, start_date: str, end_date: str,
                         flow_type: Optional[str] = None) -> List[CapitalFlowData]:
        """
        获取资金流数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            flow_type: 资金流类型过滤
            
        Returns:
            资金流数据列表
        """
        return self.provider.get_capital_flows(symbol, start_date, end_date, flow_type)
    
    def get_main_capital_flows(self, symbol: str, start_date: str, end_date: str) -> List[CapitalFlowData]:
        """获取主力资金流数据"""
        return self.get_capital_flows(symbol, start_date, end_date, flow_type="main")
    
    def get_institution_capital_flows(self, symbol: str, start_date: str, end_date: str) -> List[CapitalFlowData]:
        """获取机构资金流数据"""
        return self.get_capital_flows(symbol, start_date, end_date, flow_type="institution")
    
    def get_themes(self, symbol: str, theme_type: Optional[str] = None) -> List[ThemeData]:
        """
        获取板块/主题数据
        
        Args:
            symbol: 股票代码
            theme_type: 主题类型过滤
            
        Returns:
            主题数据列表
        """
        return self.provider.get_themes(symbol, theme_type)
    
    def get_concept_themes(self, symbol: str) -> List[ThemeData]:
        """获取概念主题数据"""
        return self.get_themes(symbol, theme_type="concept")
    
    def get_sector_themes(self, symbol: str) -> List[ThemeData]:
        """获取板块主题数据"""
        return self.get_themes(symbol, theme_type="sector")
    
    def get_dragon_tigers(self, symbol: str, start_date: str, end_date: str,
                         dragon_tiger_type: Optional[str] = None) -> List[DragonTigerData]:
        """
        获取龙虎榜数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            dragon_tiger_type: 龙虎榜类型过滤
            
        Returns:
            龙虎榜数据列表
        """
        return self.provider.get_dragon_tigers(symbol, start_date, end_date, dragon_tiger_type)
    
    def get_daily_dragon_tigers(self, symbol: str, start_date: str, end_date: str) -> List[DragonTigerData]:
        """获取日龙虎榜数据"""
        return self.get_dragon_tigers(symbol, start_date, end_date, dragon_tiger_type="daily")
    
    # ========== 统计分析方法 ==========
    
    def get_sentiment_summary(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取情绪分析摘要"""
        sentiments = self.get_news_sentiments(symbol, start_date, end_date)
        
        if not sentiments:
            return {
                "total_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "avg_sentiment_score": 0.0,
                "avg_confidence": 0.0
            }
        
        positive_count = sum(1 for s in sentiments if s.sentiment == NewsSentiment.POSITIVE)
        negative_count = sum(1 for s in sentiments if s.sentiment == NewsSentiment.NEGATIVE)
        neutral_count = sum(1 for s in sentiments if s.sentiment == NewsSentiment.NEUTRAL)
        
        avg_sentiment_score = sum(s.sentiment_score for s in sentiments) / len(sentiments)
        avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments)
        
        return {
            "total_count": len(sentiments),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "avg_sentiment_score": avg_sentiment_score,
            "avg_confidence": avg_confidence
        }
    
    def get_capital_flow_summary(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取资金流摘要"""
        flows = self.get_capital_flows(symbol, start_date, end_date)
        
        if not flows:
            return {
                "total_net_amount": 0.0,
                "total_inflow": 0.0,
                "total_outflow": 0.0,
                "avg_turnover_rate": 0.0,
                "inflow_days": 0,
                "outflow_days": 0
            }
        
        total_net_amount = sum(f.net_amount for f in flows)
        total_inflow = sum(f.inflow_amount for f in flows)
        total_outflow = sum(f.outflow_amount for f in flows)
        avg_turnover_rate = sum(f.turnover_rate for f in flows) / len(flows)
        
        inflow_days = sum(1 for f in flows if f.direction == FlowDirection.INFLOW)
        outflow_days = sum(1 for f in flows if f.direction == FlowDirection.OUTFLOW)
        
        return {
            "total_net_amount": total_net_amount,
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "avg_turnover_rate": avg_turnover_rate,
            "inflow_days": inflow_days,
            "outflow_days": outflow_days
        }
    
    def get_research_summary(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取研报摘要"""
        reports = self.get_research_reports(symbol, start_date, end_date)
        
        if not reports:
            return {
                "total_count": 0,
                "buy_count": 0,
                "sell_count": 0,
                "hold_count": 0,
                "avg_target_price": 0.0,
                "institutions": []
            }
        
        buy_count = sum(1 for r in reports if r.rating in [ReportRating.BUY, ReportRating.STRONG_BUY])
        sell_count = sum(1 for r in reports if r.rating in [ReportRating.SELL, ReportRating.STRONG_SELL])
        hold_count = sum(1 for r in reports if r.rating == ReportRating.HOLD)
        
        target_prices = [r.target_price for r in reports if r.target_price is not None]
        avg_target_price = sum(target_prices) / len(target_prices) if target_prices else 0.0
        
        institutions = list(set(r.institution for r in reports if r.institution))
        
        return {
            "total_count": len(reports),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "avg_target_price": avg_target_price,
            "institutions": institutions
        }
    
    def get_theme_summary(self, symbol: str) -> Dict[str, Any]:
        """获取主题摘要"""
        themes = self.get_themes(symbol)
        
        if not themes:
            return {
                "total_count": 0,
                "concept_count": 0,
                "sector_count": 0,
                "industry_count": 0,
                "avg_weight": 0.0,
                "top_themes": []
            }
        
        concept_count = sum(1 for t in themes if t.theme_type == ThemeType.CONCEPT)
        sector_count = sum(1 for t in themes if t.theme_type == ThemeType.SECTOR)
        industry_count = sum(1 for t in themes if t.theme_type == ThemeType.INDUSTRY)
        
        avg_weight = sum(t.weight for t in themes) / len(themes)
        
        # 按权重排序获取前5个主题
        sorted_themes = sorted(themes, key=lambda x: x.weight, reverse=True)
        top_themes = [(t.theme_name, t.weight) for t in sorted_themes[:5]]
        
        return {
            "total_count": len(themes),
            "concept_count": concept_count,
            "sector_count": sector_count,
            "industry_count": industry_count,
            "avg_weight": avg_weight,
            "top_themes": top_themes
        }
    
    def get_dragon_tiger_summary(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取龙虎榜摘要"""
        dragon_tigers = self.get_dragon_tigers(symbol, start_date, end_date)
        
        if not dragon_tigers:
            return {
                "total_count": 0,
                "total_buy_amount": 0.0,
                "total_sell_amount": 0.0,
                "total_net_amount": 0.0,
                "avg_turnover_rate": 0.0,
                "avg_price_change": 0.0
            }
        
        total_buy_amount = sum(dt.buy_amount for dt in dragon_tigers)
        total_sell_amount = sum(dt.sell_amount for dt in dragon_tigers)
        total_net_amount = sum(dt.net_amount for dt in dragon_tigers)
        avg_turnover_rate = sum(dt.turnover_rate for dt in dragon_tigers) / len(dragon_tigers)
        avg_price_change = sum(dt.price_change for dt in dragon_tigers) / len(dragon_tigers)
        
        return {
            "total_count": len(dragon_tigers),
            "total_buy_amount": total_buy_amount,
            "total_sell_amount": total_sell_amount,
            "total_net_amount": total_net_amount,
            "avg_turnover_rate": avg_turnover_rate,
            "avg_price_change": avg_price_change
        }
    
    # ========== 数据保存方法 ==========
    
    def save_announcements(self, announcements: List[AnnouncementData]) -> int:
        """保存公告数据"""
        # 这里应该调用存储层的方法
        # 目前返回模拟数据
        return len(announcements)
    
    def save_news_sentiments(self, sentiments: List[NewsSentimentData]) -> int:
        """保存新闻情绪数据"""
        return len(sentiments)
    
    def save_research_reports(self, reports: List[ResearchReportData]) -> int:
        """保存研报数据"""
        return len(reports)
    
    def save_capital_flows(self, flows: List[CapitalFlowData]) -> int:
        """保存资金流数据"""
        return len(flows)
    
    def save_themes(self, themes: List[ThemeData]) -> int:
        """保存主题数据"""
        return len(themes)
    
    def save_dragon_tigers(self, dragon_tigers: List[DragonTigerData]) -> int:
        """保存龙虎榜数据"""
        return len(dragon_tigers)
