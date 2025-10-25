# qp/data/types/derivative.py
"""
衍生数据类型定义

包含公告、新闻情绪、研报、资金流、板块/主题、龙虎榜等衍生数据类型
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import pandas as pd


# ========== 枚举定义 ==========

class AnnouncementType(Enum):
    """公告类型"""
    FINANCIAL = "financial"  # 财务公告
    BUSINESS = "business"    # 业务公告
    GOVERNANCE = "governance"  # 治理公告
    RISK = "risk"           # 风险提示
    OTHER = "other"         # 其他


class NewsSentiment(Enum):
    """新闻情绪"""
    POSITIVE = "positive"   # 正面
    NEUTRAL = "neutral"     # 中性
    NEGATIVE = "negative"   # 负面


class ReportType(Enum):
    """研报类型"""
    INITIATE = "initiate"   # 首次覆盖
    MAINTAIN = "maintain"   # 维持评级
    UPGRADE = "upgrade"     # 上调评级
    DOWNGRADE = "downgrade"  # 下调评级
    TARGET = "target"       # 目标价调整


class ReportRating(Enum):
    """研报评级"""
    BUY = "buy"             # 买入
    STRONG_BUY = "strong_buy"  # 强烈买入
    HOLD = "hold"           # 持有
    SELL = "sell"           # 卖出
    STRONG_SELL = "strong_sell"  # 强烈卖出


class FlowDirection(Enum):
    """资金流向"""
    INFLOW = "inflow"       # 流入
    OUTFLOW = "outflow"     # 流出
    NEUTRAL = "neutral"     # 中性


class FlowType(Enum):
    """资金流类型"""
    MAIN = "main"           # 主力资金
    RETAIL = "retail"       # 散户资金
    INSTITUTION = "institution"  # 机构资金
    FOREIGN = "foreign"     # 外资


class ThemeType(Enum):
    """主题类型"""
    CONCEPT = "concept"     # 概念
    SECTOR = "sector"       # 板块
    INDUSTRY = "industry"   # 行业
    REGION = "region"       # 地区


class DragonTigerType(Enum):
    """龙虎榜类型"""
    DAILY = "daily"         # 日榜
    WEEKLY = "weekly"       # 周榜
    MONTHLY = "monthly"     # 月榜


class DragonTigerReason(Enum):
    """龙虎榜上榜原因"""
    PRICE_LIMIT = "price_limit"      # 涨跌幅偏离值
    VOLUME = "volume"                # 成交量异常
    TURNOVER = "turnover"            # 换手率异常
    CONTINUOUS = "continuous"        # 连续异常
    OTHER = "other"                  # 其他


# ========== 数据类定义 ==========

@dataclass
class AnnouncementData:
    """公告数据"""
    symbol: str
    title: str
    content: str
    announcement_date: datetime
    announcement_type: AnnouncementType
    source: str
    url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    importance: int = 1  # 重要性等级 1-5
    is_important: bool = False  # 是否重要公告
    
    def __post_init__(self):
        if isinstance(self.announcement_date, str):
            self.announcement_date = pd.to_datetime(self.announcement_date)
        if isinstance(self.announcement_type, str):
            self.announcement_type = AnnouncementType(self.announcement_type)


@dataclass
class NewsSentimentData:
    """新闻情绪数据"""
    symbol: str
    title: str
    content: str
    publish_date: datetime
    sentiment: NewsSentiment
    sentiment_score: float  # 情绪得分 -1.0 到 1.0
    source: str
    url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 置信度 0.0 到 1.0
    
    def __post_init__(self):
        if isinstance(self.publish_date, str):
            self.publish_date = pd.to_datetime(self.publish_date)
        if isinstance(self.sentiment, str):
            self.sentiment = NewsSentiment(self.sentiment)


@dataclass
class ResearchReportData:
    """研报数据"""
    symbol: str
    title: str
    content: str
    publish_date: datetime
    report_type: ReportType
    rating: ReportRating
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    analyst: str = ""
    institution: str = ""
    source: str = ""
    url: Optional[str] = None
    summary: str = ""
    
    def __post_init__(self):
        if isinstance(self.publish_date, str):
            self.publish_date = pd.to_datetime(self.publish_date)
        if isinstance(self.report_type, str):
            self.report_type = ReportType(self.report_type)
        if isinstance(self.rating, str):
            self.rating = ReportRating(self.rating)


@dataclass
class CapitalFlowData:
    """资金流数据"""
    symbol: str
    date: datetime
    flow_type: FlowType
    direction: FlowDirection
    net_amount: float  # 净流入金额（万元）
    inflow_amount: float  # 流入金额（万元）
    outflow_amount: float  # 流出金额（万元）
    volume: float = 0.0  # 成交量
    turnover_rate: float = 0.0  # 换手率
    
    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = pd.to_datetime(self.date)
        if isinstance(self.flow_type, str):
            self.flow_type = FlowType(self.flow_type)
        if isinstance(self.direction, str):
            self.direction = FlowDirection(self.direction)


@dataclass
class ThemeData:
    """板块/主题数据"""
    symbol: str
    theme_name: str
    theme_type: ThemeType
    weight: float  # 权重 0.0 到 1.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: str = ""
    
    def __post_init__(self):
        if isinstance(self.theme_type, str):
            self.theme_type = ThemeType(self.theme_type)
        if self.start_date and isinstance(self.start_date, str):
            self.start_date = pd.to_datetime(self.start_date)
        if self.end_date and isinstance(self.end_date, str):
            self.end_date = pd.to_datetime(self.end_date)


@dataclass
class DragonTigerData:
    """龙虎榜数据"""
    symbol: str
    date: datetime
    dragon_tiger_type: DragonTigerType
    reason: DragonTigerReason
    buy_amount: float  # 买入金额（万元）
    sell_amount: float  # 卖出金额（万元）
    net_amount: float  # 净买入金额（万元）
    buy_seats: List[str] = field(default_factory=list)  # 买入席位
    sell_seats: List[str] = field(default_factory=list)  # 卖出席位
    turnover_rate: float = 0.0  # 换手率
    price_change: float = 0.0  # 涨跌幅
    
    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = pd.to_datetime(self.date)
        if isinstance(self.dragon_tiger_type, str):
            self.dragon_tiger_type = DragonTigerType(self.dragon_tiger_type)
        if isinstance(self.reason, str):
            self.reason = DragonTigerReason(self.reason)


# ========== 数据转换函数 ==========

def announcements_to_df(announcements: List[AnnouncementData]) -> pd.DataFrame:
    """将公告数据列表转换为DataFrame"""
    if not announcements:
        return pd.DataFrame(columns=[
            'symbol', 'title', 'content', 'announcement_date', 'announcement_type',
            'source', 'url', 'keywords', 'importance', 'is_important'
        ])
    
    data = []
    for ann in announcements:
        data.append({
            'symbol': ann.symbol,
            'title': ann.title,
            'content': ann.content,
            'announcement_date': ann.announcement_date,
            'announcement_type': ann.announcement_type.value,
            'source': ann.source,
            'url': ann.url,
            'keywords': ','.join(ann.keywords),
            'importance': ann.importance,
            'is_important': ann.is_important
        })
    
    return pd.DataFrame(data)


def df_to_announcements(df: pd.DataFrame) -> List[AnnouncementData]:
    """将DataFrame转换为公告数据列表"""
    announcements = []
    for _, row in df.iterrows():
        keywords = row['keywords'].split(',') if pd.notna(row['keywords']) else []
        ann = AnnouncementData(
            symbol=row['symbol'],
            title=row['title'],
            content=row['content'],
            announcement_date=row['announcement_date'],
            announcement_type=AnnouncementType(row['announcement_type']),
            source=row['source'],
            url=row.get('url'),
            keywords=keywords,
            importance=row.get('importance', 1),
            is_important=row.get('is_important', False)
        )
        announcements.append(ann)
    
    return announcements


def news_sentiments_to_df(sentiments: List[NewsSentimentData]) -> pd.DataFrame:
    """将新闻情绪数据列表转换为DataFrame"""
    if not sentiments:
        return pd.DataFrame(columns=[
            'symbol', 'title', 'content', 'publish_date', 'sentiment',
            'sentiment_score', 'source', 'url', 'keywords', 'confidence'
        ])
    
    data = []
    for sent in sentiments:
        data.append({
            'symbol': sent.symbol,
            'title': sent.title,
            'content': sent.content,
            'publish_date': sent.publish_date,
            'sentiment': sent.sentiment.value,
            'sentiment_score': sent.sentiment_score,
            'source': sent.source,
            'url': sent.url,
            'keywords': ','.join(sent.keywords),
            'confidence': sent.confidence
        })
    
    return pd.DataFrame(data)


def df_to_news_sentiments(df: pd.DataFrame) -> List[NewsSentimentData]:
    """将DataFrame转换为新闻情绪数据列表"""
    sentiments = []
    for _, row in df.iterrows():
        keywords = row['keywords'].split(',') if pd.notna(row['keywords']) else []
        sent = NewsSentimentData(
            symbol=row['symbol'],
            title=row['title'],
            content=row['content'],
            publish_date=row['publish_date'],
            sentiment=NewsSentiment(row['sentiment']),
            sentiment_score=row['sentiment_score'],
            source=row['source'],
            url=row.get('url'),
            keywords=keywords,
            confidence=row.get('confidence', 0.0)
        )
        sentiments.append(sent)
    
    return sentiments


def research_reports_to_df(reports: List[ResearchReportData]) -> pd.DataFrame:
    """将研报数据列表转换为DataFrame"""
    if not reports:
        return pd.DataFrame(columns=[
            'symbol', 'title', 'content', 'publish_date', 'report_type',
            'rating', 'target_price', 'current_price', 'analyst', 'institution',
            'source', 'url', 'summary'
        ])
    
    data = []
    for report in reports:
        data.append({
            'symbol': report.symbol,
            'title': report.title,
            'content': report.content,
            'publish_date': report.publish_date,
            'report_type': report.report_type.value,
            'rating': report.rating.value,
            'target_price': report.target_price,
            'current_price': report.current_price,
            'analyst': report.analyst,
            'institution': report.institution,
            'source': report.source,
            'url': report.url,
            'summary': report.summary
        })
    
    return pd.DataFrame(data)


def df_to_research_reports(df: pd.DataFrame) -> List[ResearchReportData]:
    """将DataFrame转换为研报数据列表"""
    reports = []
    for _, row in df.iterrows():
        report = ResearchReportData(
            symbol=row['symbol'],
            title=row['title'],
            content=row['content'],
            publish_date=row['publish_date'],
            report_type=ReportType(row['report_type']),
            rating=ReportRating(row['rating']),
            target_price=row.get('target_price'),
            current_price=row.get('current_price'),
            analyst=row.get('analyst', ''),
            institution=row.get('institution', ''),
            source=row.get('source', ''),
            url=row.get('url'),
            summary=row.get('summary', '')
        )
        reports.append(report)
    
    return reports


def capital_flows_to_df(flows: List[CapitalFlowData]) -> pd.DataFrame:
    """将资金流数据列表转换为DataFrame"""
    if not flows:
        return pd.DataFrame(columns=[
            'symbol', 'date', 'flow_type', 'direction', 'net_amount',
            'inflow_amount', 'outflow_amount', 'volume', 'turnover_rate'
        ])
    
    data = []
    for flow in flows:
        data.append({
            'symbol': flow.symbol,
            'date': flow.date,
            'flow_type': flow.flow_type.value,
            'direction': flow.direction.value,
            'net_amount': flow.net_amount,
            'inflow_amount': flow.inflow_amount,
            'outflow_amount': flow.outflow_amount,
            'volume': flow.volume,
            'turnover_rate': flow.turnover_rate
        })
    
    return pd.DataFrame(data)


def df_to_capital_flows(df: pd.DataFrame) -> List[CapitalFlowData]:
    """将DataFrame转换为资金流数据列表"""
    flows = []
    for _, row in df.iterrows():
        flow = CapitalFlowData(
            symbol=row['symbol'],
            date=row['date'],
            flow_type=FlowType(row['flow_type']),
            direction=FlowDirection(row['direction']),
            net_amount=row['net_amount'],
            inflow_amount=row['inflow_amount'],
            outflow_amount=row['outflow_amount'],
            volume=row.get('volume', 0.0),
            turnover_rate=row.get('turnover_rate', 0.0)
        )
        flows.append(flow)
    
    return flows


def themes_to_df(themes: List[ThemeData]) -> pd.DataFrame:
    """将主题数据列表转换为DataFrame"""
    if not themes:
        return pd.DataFrame(columns=[
            'symbol', 'theme_name', 'theme_type', 'weight',
            'start_date', 'end_date', 'description'
        ])
    
    data = []
    for theme in themes:
        data.append({
            'symbol': theme.symbol,
            'theme_name': theme.theme_name,
            'theme_type': theme.theme_type.value,
            'weight': theme.weight,
            'start_date': theme.start_date,
            'end_date': theme.end_date,
            'description': theme.description
        })
    
    return pd.DataFrame(data)


def df_to_themes(df: pd.DataFrame) -> List[ThemeData]:
    """将DataFrame转换为主题数据列表"""
    themes = []
    for _, row in df.iterrows():
        theme = ThemeData(
            symbol=row['symbol'],
            theme_name=row['theme_name'],
            theme_type=ThemeType(row['theme_type']),
            weight=row['weight'],
            start_date=row.get('start_date'),
            end_date=row.get('end_date'),
            description=row.get('description', '')
        )
        themes.append(theme)
    
    return themes


def dragon_tigers_to_df(dragon_tigers: List[DragonTigerData]) -> pd.DataFrame:
    """将龙虎榜数据列表转换为DataFrame"""
    if not dragon_tigers:
        return pd.DataFrame(columns=[
            'symbol', 'date', 'dragon_tiger_type', 'reason', 'buy_amount',
            'sell_amount', 'net_amount', 'buy_seats', 'sell_seats',
            'turnover_rate', 'price_change'
        ])
    
    data = []
    for dt in dragon_tigers:
        data.append({
            'symbol': dt.symbol,
            'date': dt.date,
            'dragon_tiger_type': dt.dragon_tiger_type.value,
            'reason': dt.reason.value,
            'buy_amount': dt.buy_amount,
            'sell_amount': dt.sell_amount,
            'net_amount': dt.net_amount,
            'buy_seats': ','.join(dt.buy_seats),
            'sell_seats': ','.join(dt.sell_seats),
            'turnover_rate': dt.turnover_rate,
            'price_change': dt.price_change
        })
    
    return pd.DataFrame(data)


def df_to_dragon_tigers(df: pd.DataFrame) -> List[DragonTigerData]:
    """将DataFrame转换为龙虎榜数据列表"""
    dragon_tigers = []
    for _, row in df.iterrows():
        buy_seats = row['buy_seats'].split(',') if pd.notna(row['buy_seats']) else []
        sell_seats = row['sell_seats'].split(',') if pd.notna(row['sell_seats']) else []
        dt = DragonTigerData(
            symbol=row['symbol'],
            date=row['date'],
            dragon_tiger_type=DragonTigerType(row['dragon_tiger_type']),
            reason=DragonTigerReason(row['reason']),
            buy_amount=row['buy_amount'],
            sell_amount=row['sell_amount'],
            net_amount=row['net_amount'],
            buy_seats=buy_seats,
            sell_seats=sell_seats,
            turnover_rate=row.get('turnover_rate', 0.0),
            price_change=row.get('price_change', 0.0)
        )
        dragon_tigers.append(dt)
    
    return dragon_tigers


# ========== 常量定义 ==========

# 公告数据列名
ANNOUNCEMENT_COLUMNS = [
    'symbol', 'title', 'content', 'announcement_date', 'announcement_type',
    'source', 'url', 'keywords', 'importance', 'is_important'
]

# 新闻情绪数据列名
NEWS_SENTIMENT_COLUMNS = [
    'symbol', 'title', 'content', 'publish_date', 'sentiment',
    'sentiment_score', 'source', 'url', 'keywords', 'confidence'
]

# 研报数据列名
RESEARCH_REPORT_COLUMNS = [
    'symbol', 'title', 'content', 'publish_date', 'report_type',
    'rating', 'target_price', 'current_price', 'analyst', 'institution',
    'source', 'url', 'summary'
]

# 资金流数据列名
CAPITAL_FLOW_COLUMNS = [
    'symbol', 'date', 'flow_type', 'direction', 'net_amount',
    'inflow_amount', 'outflow_amount', 'volume', 'turnover_rate'
]

# 主题数据列名
THEME_COLUMNS = [
    'symbol', 'theme_name', 'theme_type', 'weight',
    'start_date', 'end_date', 'description'
]

# 龙虎榜数据列名
DRAGON_TIGER_COLUMNS = [
    'symbol', 'date', 'dragon_tiger_type', 'reason', 'buy_amount',
    'sell_amount', 'net_amount', 'buy_seats', 'sell_seats',
    'turnover_rate', 'price_change'
]

# 数据类型映射
DERIVATIVE_DTYPES = {
    'symbol': 'string',
    'title': 'string',
    'content': 'string',
    'source': 'string',
    'url': 'string',
    'keywords': 'string',
    'analyst': 'string',
    'institution': 'string',
    'summary': 'string',
    'description': 'string',
    'theme_name': 'string',
    'buy_seats': 'string',
    'sell_seats': 'string',
    'announcement_date': 'datetime64[ns]',
    'publish_date': 'datetime64[ns]',
    'date': 'datetime64[ns]',
    'start_date': 'datetime64[ns]',
    'end_date': 'datetime64[ns]',
    'announcement_type': 'category',
    'sentiment': 'category',
    'report_type': 'category',
    'rating': 'category',
    'flow_type': 'category',
    'direction': 'category',
    'theme_type': 'category',
    'dragon_tiger_type': 'category',
    'reason': 'category',
    'importance': 'int8',
    'is_important': 'boolean',
    'sentiment_score': 'float32',
    'confidence': 'float32',
    'target_price': 'float32',
    'current_price': 'float32',
    'net_amount': 'float32',
    'inflow_amount': 'float32',
    'outflow_amount': 'float32',
    'volume': 'float32',
    'turnover_rate': 'float32',
    'weight': 'float32',
    'buy_amount': 'float32',
    'sell_amount': 'float32',
    'price_change': 'float32'
}
