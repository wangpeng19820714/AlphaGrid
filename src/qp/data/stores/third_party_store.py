# qp/data/stores/third_party_store.py
"""
第三方数据存储

提供指数成分、行业分类、宏观数据的存储和查询功能
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
from ..types.third_party import (
    IndexComponentData, IndustryClassificationData, MacroData,
    index_components_to_df, df_to_index_components,
    industry_classifications_to_df, df_to_industry_classifications,
    macro_data_to_df, df_to_macro_data
)


class ThirdPartyStore(BaseStore):
    """第三方数据存储基类"""
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
        self.index_component_dir = self.root / "index_components"
        self.industry_classification_dir = self.root / "industry_classifications"
        self.macro_data_dir = self.root / "macro_data"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        for directory in [
            self.index_component_dir,
            self.industry_classification_dir,
            self.macro_data_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)


class IndexComponentStore(ThirdPartyStore):
    """指数成分数据存储"""
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
        self.data_dir = self.index_component_dir
    
    def save_index_components(self, components: List[IndexComponentData]) -> int:
        """保存指数成分数据"""
        if not components:
            return 0
        
        # 转换为DataFrame
        df = index_components_to_df(components)
        
        # 按指数代码分组保存
        saved_count = 0
        for index_code, group_df in df.groupby('index_code'):
            # 创建索引代码目录
            index_dir = self.data_dir / index_code
            index_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名（按日期）
            date_str = pd.Timestamp.now().strftime('%Y%m%d')
            file_path = index_dir / f"{index_code}_{date_str}.parquet"
            
            # 保存为Parquet文件
            table = pa.Table.from_pandas(group_df)
            pq.write_table(table, file_path)
            
            # 更新清单索引
            manifest_index = ManifestIndex(index_dir)
            manifest = manifest_index.build_from_files()
            manifest_index.save_atomically(manifest)
            
            saved_count += len(group_df)
        
        return saved_count
    
    def load_index_components(self, index_code: str, 
                            effective_date: Optional[str] = None) -> List[IndexComponentData]:
        """加载指数成分数据"""
        index_dir = self.data_dir / index_code
        
        if not index_dir.exists():
            return []
        
        # 读取所有Parquet文件
        files = list(index_dir.glob("*.parquet"))
        if not files:
            return []
        
        # 使用DuckDB查询
        conn = duckdb.connect()
        
        # 将Path对象转换为字符串列表
        file_paths = [str(f) for f in files]
        
        query = f"""
        SELECT * FROM read_parquet({file_paths})
        WHERE index_code = '{index_code}'
        """
        
        if effective_date:
            query += f" AND effective_date >= '{effective_date}'"
        
        query += " ORDER BY weight DESC"
        
        df = conn.execute(query).df()
        conn.close()
        
        return df_to_index_components(df)
    
    def get_index_components_by_weight(self, index_code: str, min_weight: float = 0.01) -> List[IndexComponentData]:
        """获取权重大于指定值的成分股"""
        components = self.load_index_components(index_code)
        return [comp for comp in components if comp.weight >= min_weight]
    
    def get_top_components(self, index_code: str, top_n: int = 10) -> List[IndexComponentData]:
        """获取权重排名前N的成分股"""
        components = self.load_index_components(index_code)
        return sorted(components, key=lambda x: x.weight, reverse=True)[:top_n]


class IndustryClassificationStore(ThirdPartyStore):
    """行业分类数据存储"""
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
        self.data_dir = self.industry_classification_dir
    
    def save_industry_classifications(self, classifications: List[IndustryClassificationData]) -> int:
        """保存行业分类数据"""
        if not classifications:
            return 0
        
        # 转换为DataFrame
        df = industry_classifications_to_df(classifications)
        
        # 按行业标准分组保存
        saved_count = 0
        for (industry_standard, industry_level), group_df in df.groupby(['industry_standard', 'industry_level']):
            # 创建目录结构
            standard_dir = self.data_dir / industry_standard
            level_dir = standard_dir / industry_level
            level_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            date_str = pd.Timestamp.now().strftime('%Y%m%d')
            file_path = level_dir / f"{industry_standard}_{industry_level}_{date_str}.parquet"
            
            # 保存为Parquet文件
            table = pa.Table.from_pandas(group_df)
            pq.write_table(table, file_path)
            
            # 更新清单索引
            manifest_index = ManifestIndex(level_dir)
            manifest = manifest_index.build_from_files()
            manifest_index.save_atomically(manifest)
            
            saved_count += len(group_df)
        
        return saved_count
    
    def load_industry_classifications(self, symbol: str,
                                    industry_standard: Optional[str] = None,
                                    industry_level: Optional[str] = None) -> List[IndustryClassificationData]:
        """加载行业分类数据"""
        classifications = []
        
        # 确定搜索范围
        if industry_standard and industry_level:
            search_dirs = [self.data_dir / industry_standard / industry_level]
        elif industry_standard:
            search_dirs = [self.data_dir / industry_standard / level for level in ['level1', 'level2', 'level3', 'level4']]
        else:
            search_dirs = []
            for std_dir in self.data_dir.iterdir():
                if std_dir.is_dir():
                    for level_dir in std_dir.iterdir():
                        if level_dir.is_dir():
                            search_dirs.append(level_dir)
        
        # 搜索所有相关目录
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            files = list(search_dir.glob("*.parquet"))
            if not files:
                continue
            
            # 使用DuckDB查询
            conn = duckdb.connect()
            
            # 将Path对象转换为字符串列表
            file_paths = [str(f) for f in files]
            
            query = f"""
            SELECT * FROM read_parquet({file_paths})
            WHERE symbol = '{symbol}'
            """
            
            if industry_standard:
                query += f" AND industry_standard = '{industry_standard}'"
            if industry_level:
                query += f" AND industry_level = '{industry_level}'"
            
            query += " ORDER BY industry_level"
            
            df = conn.execute(query).df()
            conn.close()
            
            if not df.empty:
                classifications.extend(df_to_industry_classifications(df))
        
        return classifications
    
    def get_industry_by_level(self, symbol: str, level: str,
                            industry_standard: Optional[str] = None) -> Optional[IndustryClassificationData]:
        """获取指定级别的行业分类"""
        classifications = self.load_industry_classifications(symbol, industry_standard, level)
        return classifications[0] if classifications else None


class MacroDataStore(ThirdPartyStore):
    """宏观数据存储"""
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
        self.data_dir = self.macro_data_dir
    
    def save_macro_data(self, macro_data: List[MacroData]) -> int:
        """保存宏观数据"""
        if not macro_data:
            return 0
        
        # 转换为DataFrame
        df = macro_data_to_df(macro_data)
        
        # 按数据类型和频率分组保存
        saved_count = 0
        for (data_type, frequency), group_df in df.groupby(['data_type', 'frequency']):
            # 创建目录结构
            type_dir = self.data_dir / data_type
            freq_dir = type_dir / frequency
            freq_dir.mkdir(parents=True, exist_ok=True)
            
            # 按年份分组保存
            for year, year_df in group_df.groupby(group_df['date'].dt.year):
                file_path = freq_dir / f"{data_type}_{frequency}_{year}.parquet"
                
                # 保存为Parquet文件
                table = pa.Table.from_pandas(year_df)
                pq.write_table(table, file_path)
                
                # 更新清单索引
                manifest_index = ManifestIndex(freq_dir)
                manifest = manifest_index.build_from_files()
                manifest_index.save_atomically(manifest)
                
                saved_count += len(year_df)
        
        return saved_count
    
    def load_macro_data(self, data_code: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None, data_type: Optional[str] = None) -> List[MacroData]:
        """加载宏观数据"""
        macro_data = []
        
        # 确定搜索范围
        if data_type:
            search_dirs = [self.data_dir / data_type]
        else:
            search_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        
        # 搜索所有相关目录
        for type_dir in search_dirs:
            if not type_dir.exists():
                continue
            
            for freq_dir in type_dir.iterdir():
                if not freq_dir.is_dir():
                    continue
                
                files = list(freq_dir.glob("*.parquet"))
                if not files:
                    continue
                
                # 使用DuckDB查询
                conn = duckdb.connect()
                
                # 将Path对象转换为字符串列表
                file_paths = [str(f) for f in files]
                
                query = f"""
                SELECT * FROM read_parquet({file_paths})
                WHERE data_code = '{data_code}'
                """
                
                if start_date:
                    query += f" AND date >= '{start_date}'"
                if end_date:
                    query += f" AND date <= '{end_date}'"
                
                query += " ORDER BY date"
                
                df = conn.execute(query).df()
                conn.close()
                
                if not df.empty:
                    macro_data.extend(df_to_macro_data(df))
        
        return macro_data
    
    def get_latest_macro_data(self, data_code: str) -> Optional[MacroData]:
        """获取最新的宏观数据"""
        macro_data = self.load_macro_data(data_code)
        if macro_data:
            return max(macro_data, key=lambda x: x.date)
        return None
    
    def get_macro_data_by_type(self, data_type: str, start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[MacroData]:
        """按数据类型获取宏观数据"""
        type_dir = self.data_dir / data_type
        if not type_dir.exists():
            return []
        
        macro_data = []
        for freq_dir in type_dir.iterdir():
            if not freq_dir.is_dir():
                continue
            
            files = list(freq_dir.glob("*.parquet"))
            if not files:
                continue
            
            # 使用DuckDB查询
            conn = duckdb.connect()
            
            # 将Path对象转换为字符串列表
            file_paths = [str(f) for f in files]
            
            query = f"""
            SELECT * FROM read_parquet({file_paths})
            WHERE data_type = '{data_type}'
            """
            
            if start_date:
                query += f" AND date >= '{start_date}'"
            if end_date:
                query += f" AND date <= '{end_date}'"
            
            query += " ORDER BY date"
            
            df = conn.execute(query).df()
            conn.close()
            
            if not df.empty:
                macro_data.extend(df_to_macro_data(df))
        
        return macro_data


def get_third_party_store(config: Optional[StoreConfig] = None) -> ThirdPartyStore:
    """
    获取第三方数据存储实例
    
    Args:
        config: 存储配置，如果为None则使用默认配置
        
    Returns:
        第三方数据存储实例
    """
    if config is None:
        config = StoreConfig(root="data/third_party")
    
    return ThirdPartyStore(config)
