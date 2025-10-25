# qp/data/stores/derivative_store.py
"""
衍生数据存储

提供公告、新闻情绪、研报、资金流、板块/主题、龙虎榜等衍生数据的存储功能
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

from .base import StoreConfig, BaseStore, ManifestIndex
from ..types.derivative import (
    AnnouncementData, NewsSentimentData, ResearchReportData,
    CapitalFlowData, ThemeData, DragonTigerData,
    announcements_to_df, df_to_announcements,
    news_sentiments_to_df, df_to_news_sentiments,
    research_reports_to_df, df_to_research_reports,
    capital_flows_to_df, df_to_capital_flows,
    themes_to_df, df_to_themes,
    dragon_tigers_to_df, df_to_dragon_tigers
)


class DerivativeStore(BaseStore):
    """衍生数据存储基类"""
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
        self.announcement_dir = self.root / "announcements"
        self.news_sentiment_dir = self.root / "news_sentiments"
        self.research_report_dir = self.root / "research_reports"
        self.capital_flow_dir = self.root / "capital_flows"
        self.theme_dir = self.root / "themes"
        self.dragon_tiger_dir = self.root / "dragon_tigers"
    
    def _ensure_directories(self):
        """确保所有目录存在"""
        for directory in [
            self.announcement_dir, self.news_sentiment_dir, self.research_report_dir,
            self.capital_flow_dir, self.theme_dir, self.dragon_tiger_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)


class AnnouncementStore(DerivativeStore):
    """公告数据存储"""
    
    def save_announcements(self, announcements: List[AnnouncementData]) -> int:
        """保存公告数据"""
        if not announcements:
            return 0
        
        self._ensure_directories()
        
        # 转换为DataFrame
        df = announcements_to_df(announcements)
        
        # 按股票代码分组保存
        total_saved = 0
        for symbol, group_df in df.groupby('symbol'):
            symbol_dir = self.announcement_dir / symbol
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为Parquet文件
            file_path = symbol_dir / f"announcements_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet"
            table = pa.Table.from_pandas(group_df, preserve_index=False)
            pq.write_table(table, file_path, compression='snappy')
            
            total_saved += len(group_df)
        
        return total_saved
    
    def load_announcements(self, symbol: str, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> List[AnnouncementData]:
        """加载公告数据"""
        symbol_dir = self.announcement_dir / symbol
        
        if not symbol_dir.exists():
            return []
        
        # 读取所有Parquet文件
        files = list(symbol_dir.glob("*.parquet"))
        if not files:
            return []
        
        # 使用DuckDB查询
        conn = duckdb.connect()
        
        # 将Path对象转换为字符串列表
        file_paths = [str(f) for f in files]
        
        # 构建查询
        query = f"""
        SELECT * FROM read_parquet({file_paths})
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND announcement_date >= '{start_date}'"
        if end_date:
            query += f" AND announcement_date <= '{end_date}'"
        
        query += " ORDER BY announcement_date DESC"
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_announcements(df)


class NewsSentimentStore(DerivativeStore):
    """新闻情绪数据存储"""
    
    def save_news_sentiments(self, sentiments: List[NewsSentimentData]) -> int:
        """保存新闻情绪数据"""
        if not sentiments:
            return 0
        
        self._ensure_directories()
        
        df = news_sentiments_to_df(sentiments)
        
        total_saved = 0
        for symbol, group_df in df.groupby('symbol'):
            symbol_dir = self.news_sentiment_dir / symbol
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = symbol_dir / f"sentiments_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet"
            table = pa.Table.from_pandas(group_df, preserve_index=False)
            pq.write_table(table, file_path, compression='snappy')
            
            total_saved += len(group_df)
        
        return total_saved
    
    def load_news_sentiments(self, symbol: str, start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[NewsSentimentData]:
        """加载新闻情绪数据"""
        symbol_dir = self.news_sentiment_dir / symbol
        
        if not symbol_dir.exists():
            return []
        
        files = list(symbol_dir.glob("*.parquet"))
        if not files:
            return []
        
        conn = duckdb.connect()
        
        query = f"""
        SELECT * FROM read_parquet({[str(f) for f in files]})
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND publish_date >= '{start_date}'"
        if end_date:
            query += f" AND publish_date <= '{end_date}'"
        
        query += " ORDER BY publish_date DESC"
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_news_sentiments(df)


class ResearchReportStore(DerivativeStore):
    """研报数据存储"""
    
    def save_research_reports(self, reports: List[ResearchReportData]) -> int:
        """保存研报数据"""
        if not reports:
            return 0
        
        self._ensure_directories()
        
        df = research_reports_to_df(reports)
        
        total_saved = 0
        for symbol, group_df in df.groupby('symbol'):
            symbol_dir = self.research_report_dir / symbol
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = symbol_dir / f"reports_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet"
            table = pa.Table.from_pandas(group_df, preserve_index=False)
            pq.write_table(table, file_path, compression='snappy')
            
            total_saved += len(group_df)
        
        return total_saved
    
    def load_research_reports(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[ResearchReportData]:
        """加载研报数据"""
        symbol_dir = self.research_report_dir / symbol
        
        if not symbol_dir.exists():
            return []
        
        files = list(symbol_dir.glob("*.parquet"))
        if not files:
            return []
        
        conn = duckdb.connect()
        
        query = f"""
        SELECT * FROM read_parquet({[str(f) for f in files]})
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND publish_date >= '{start_date}'"
        if end_date:
            query += f" AND publish_date <= '{end_date}'"
        
        query += " ORDER BY publish_date DESC"
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_research_reports(df)


class CapitalFlowStore(DerivativeStore):
    """资金流数据存储"""
    
    def save_capital_flows(self, flows: List[CapitalFlowData]) -> int:
        """保存资金流数据"""
        if not flows:
            return 0
        
        self._ensure_directories()
        
        df = capital_flows_to_df(flows)
        
        total_saved = 0
        for symbol, group_df in df.groupby('symbol'):
            symbol_dir = self.capital_flow_dir / symbol
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = symbol_dir / f"flows_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet"
            table = pa.Table.from_pandas(group_df, preserve_index=False)
            pq.write_table(table, file_path, compression='snappy')
            
            total_saved += len(group_df)
        
        return total_saved
    
    def load_capital_flows(self, symbol: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[CapitalFlowData]:
        """加载资金流数据"""
        symbol_dir = self.capital_flow_dir / symbol
        
        if not symbol_dir.exists():
            return []
        
        files = list(symbol_dir.glob("*.parquet"))
        if not files:
            return []
        
        conn = duckdb.connect()
        
        query = f"""
        SELECT * FROM read_parquet({[str(f) for f in files]})
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND date >= '{start_date}'"
        if end_date:
            query += f" AND date <= '{end_date}'"
        
        query += " ORDER BY date DESC"
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_capital_flows(df)


class ThemeStore(DerivativeStore):
    """主题数据存储"""
    
    def save_themes(self, themes: List[ThemeData]) -> int:
        """保存主题数据"""
        if not themes:
            return 0
        
        self._ensure_directories()
        
        df = themes_to_df(themes)
        
        total_saved = 0
        for symbol, group_df in df.groupby('symbol'):
            symbol_dir = self.theme_dir / symbol
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = symbol_dir / f"themes_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet"
            table = pa.Table.from_pandas(group_df, preserve_index=False)
            pq.write_table(table, file_path, compression='snappy')
            
            total_saved += len(group_df)
        
        return total_saved
    
    def load_themes(self, symbol: str) -> List[ThemeData]:
        """加载主题数据"""
        symbol_dir = self.theme_dir / symbol
        
        if not symbol_dir.exists():
            return []
        
        files = list(symbol_dir.glob("*.parquet"))
        if not files:
            return []
        
        conn = duckdb.connect()
        
        query = f"""
        SELECT * FROM read_parquet({[str(f) for f in files]})
        WHERE symbol = '{symbol}'
        ORDER BY weight DESC
        """
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_themes(df)


class DragonTigerStore(DerivativeStore):
    """龙虎榜数据存储"""
    
    def save_dragon_tigers(self, dragon_tigers: List[DragonTigerData]) -> int:
        """保存龙虎榜数据"""
        if not dragon_tigers:
            return 0
        
        self._ensure_directories()
        
        df = dragon_tigers_to_df(dragon_tigers)
        
        total_saved = 0
        for symbol, group_df in df.groupby('symbol'):
            symbol_dir = self.dragon_tiger_dir / symbol
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = symbol_dir / f"dragon_tigers_{pd.Timestamp.now().strftime('%Y%m%d')}.parquet"
            table = pa.Table.from_pandas(group_df, preserve_index=False)
            pq.write_table(table, file_path, compression='snappy')
            
            total_saved += len(group_df)
        
        return total_saved
    
    def load_dragon_tigers(self, symbol: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[DragonTigerData]:
        """加载龙虎榜数据"""
        symbol_dir = self.dragon_tiger_dir / symbol
        
        if not symbol_dir.exists():
            return []
        
        files = list(symbol_dir.glob("*.parquet"))
        if not files:
            return []
        
        conn = duckdb.connect()
        
        query = f"""
        SELECT * FROM read_parquet({[str(f) for f in files]})
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND date >= '{start_date}'"
        if end_date:
            query += f" AND date <= '{end_date}'"
        
        query += " ORDER BY date DESC"
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_dragon_tigers(df)


# ========== 统一存储接口 ==========

class DerivativeDataStore:
    """衍生数据统一存储接口"""
    
    def __init__(self, config: StoreConfig):
        self.config = config
        self.announcement_store = AnnouncementStore(config)
        self.news_sentiment_store = NewsSentimentStore(config)
        self.research_report_store = ResearchReportStore(config)
        self.capital_flow_store = CapitalFlowStore(config)
        self.theme_store = ThemeStore(config)
        self.dragon_tiger_store = DragonTigerStore(config)
    
    def save_announcements(self, announcements: List[AnnouncementData]) -> int:
        """保存公告数据"""
        return self.announcement_store.save_announcements(announcements)
    
    def load_announcements(self, symbol: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[AnnouncementData]:
        """加载公告数据"""
        return self.announcement_store.load_announcements(symbol, start_date, end_date)
    
    def save_news_sentiments(self, sentiments: List[NewsSentimentData]) -> int:
        """保存新闻情绪数据"""
        return self.news_sentiment_store.save_news_sentiments(sentiments)
    
    def load_news_sentiments(self, symbol: str, start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[NewsSentimentData]:
        """加载新闻情绪数据"""
        return self.news_sentiment_store.load_news_sentiments(symbol, start_date, end_date)
    
    def save_research_reports(self, reports: List[ResearchReportData]) -> int:
        """保存研报数据"""
        return self.research_report_store.save_research_reports(reports)
    
    def load_research_reports(self, symbol: str, start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[ResearchReportData]:
        """加载研报数据"""
        return self.research_report_store.load_research_reports(symbol, start_date, end_date)
    
    def save_capital_flows(self, flows: List[CapitalFlowData]) -> int:
        """保存资金流数据"""
        return self.capital_flow_store.save_capital_flows(flows)
    
    def load_capital_flows(self, symbol: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[CapitalFlowData]:
        """加载资金流数据"""
        return self.capital_flow_store.load_capital_flows(symbol, start_date, end_date)
    
    def save_themes(self, themes: List[ThemeData]) -> int:
        """保存主题数据"""
        return self.theme_store.save_themes(themes)
    
    def load_themes(self, symbol: str) -> List[ThemeData]:
        """加载主题数据"""
        return self.theme_store.load_themes(symbol)
    
    def save_dragon_tigers(self, dragon_tigers: List[DragonTigerData]) -> int:
        """保存龙虎榜数据"""
        return self.dragon_tiger_store.save_dragon_tigers(dragon_tigers)
    
    def load_dragon_tigers(self, symbol: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[DragonTigerData]:
        """加载龙虎榜数据"""
        return self.dragon_tiger_store.load_dragon_tigers(symbol, start_date, end_date)


# ========== 工厂函数 ==========

def get_derivative_store(config: Optional[StoreConfig] = None) -> DerivativeDataStore:
    """获取衍生数据存储实例"""
    if config is None:
        config = StoreConfig()
    return DerivativeDataStore(config)
