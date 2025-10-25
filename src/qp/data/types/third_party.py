# qp/data/types/third_party.py
"""
第三方数据类型定义

包含指数成分、行业分类、宏观数据等第三方数据类型
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import pandas as pd


# ========== 枚举定义 ==========

class IndexType(Enum):
    """指数类型"""
    BROAD_MARKET = "broad_market"  # 宽基指数
    SECTOR = "sector"              # 行业指数
    THEME = "theme"                # 主题指数
    STYLE = "style"                # 风格指数
    BOND = "bond"                  # 债券指数
    COMMODITY = "commodity"        # 商品指数
    CUSTOM = "custom"              # 自定义指数


class IndustryLevel(Enum):
    """行业分类级别"""
    LEVEL1 = "level1"  # 一级行业
    LEVEL2 = "level2"  # 二级行业
    LEVEL3 = "level3"  # 三级行业
    LEVEL4 = "level4"  # 四级行业


class IndustryStandard(Enum):
    """行业分类标准"""
    SW = "sw"          # 申万行业分类
    CITIC = "citic"    # 中信行业分类
    GICS = "gics"      # GICS行业分类
    CSRC = "csrc"      # 证监会行业分类
    CUSTOM = "custom"  # 自定义分类


class MacroDataType(Enum):
    """宏观数据类型"""
    GDP = "gdp"                    # GDP数据
    CPI = "cpi"                    # 消费者价格指数
    PPI = "ppi"                    # 生产者价格指数
    MONEY_SUPPLY = "money_supply"  # 货币供应量
    INTEREST_RATE = "interest_rate" # 利率
    EXCHANGE_RATE = "exchange_rate" # 汇率
    UNEMPLOYMENT = "unemployment"   # 失业率
    TRADE = "trade"                # 贸易数据
    FISCAL = "fiscal"              # 财政数据
    CUSTOM = "custom"              # 自定义数据


class DataFrequency(Enum):
    """数据频率"""
    DAILY = "daily"        # 日频
    WEEKLY = "weekly"      # 周频
    MONTHLY = "monthly"    # 月频
    QUARTERLY = "quarterly" # 季频
    YEARLY = "yearly"      # 年频
    IRREGULAR = "irregular" # 不定期


# ========== 数据类定义 ==========

@dataclass
class IndexComponentData:
    """指数成分数据"""
    index_code: str
    index_name: str
    index_type: IndexType
    symbol: str
    symbol_name: str
    weight: float  # 权重 0.0 到 1.0
    market_cap: Optional[float] = None  # 市值
    free_float: Optional[float] = None  # 自由流通市值
    effective_date: Optional[datetime] = None  # 生效日期
    end_date: Optional[datetime] = None  # 结束日期
    is_active: bool = True  # 是否活跃
    source: str = ""  # 数据源
    
    def __post_init__(self):
        if isinstance(self.index_type, str):
            self.index_type = IndexType(self.index_type)
        if isinstance(self.effective_date, str):
            self.effective_date = pd.to_datetime(self.effective_date)
        if isinstance(self.end_date, str):
            self.end_date = pd.to_datetime(self.end_date)


@dataclass
class IndustryClassificationData:
    """行业分类数据"""
    symbol: str
    symbol_name: str
    industry_code: str
    industry_name: str
    industry_level: IndustryLevel
    industry_standard: IndustryStandard
    parent_industry_code: Optional[str] = None  # 父级行业代码
    parent_industry_name: Optional[str] = None  # 父级行业名称
    effective_date: Optional[datetime] = None  # 生效日期
    end_date: Optional[datetime] = None  # 结束日期
    is_active: bool = True  # 是否活跃
    source: str = ""  # 数据源
    
    def __post_init__(self):
        if isinstance(self.industry_level, str):
            self.industry_level = IndustryLevel(self.industry_level)
        if isinstance(self.industry_standard, str):
            self.industry_standard = IndustryStandard(self.industry_standard)
        if isinstance(self.effective_date, str):
            self.effective_date = pd.to_datetime(self.effective_date)
        if isinstance(self.end_date, str):
            self.end_date = pd.to_datetime(self.end_date)


@dataclass
class MacroData:
    """宏观数据"""
    data_code: str
    data_name: str
    data_type: MacroDataType
    frequency: DataFrequency
    date: datetime
    value: float
    unit: str = ""  # 单位
    previous_value: Optional[float] = None  # 前值
    change_value: Optional[float] = None  # 变化值
    change_rate: Optional[float] = None  # 变化率
    seasonally_adjusted: bool = False  # 是否季调
    source: str = ""  # 数据源
    description: str = ""  # 数据描述
    
    def __post_init__(self):
        if isinstance(self.data_type, str):
            self.data_type = MacroDataType(self.data_type)
        if isinstance(self.frequency, str):
            self.frequency = DataFrequency(self.frequency)
        if isinstance(self.date, str):
            self.date = pd.to_datetime(self.date)


# ========== 数据转换函数 ==========

def index_components_to_df(components: List[IndexComponentData]) -> pd.DataFrame:
    """将指数成分数据列表转换为DataFrame"""
    if not components:
        return pd.DataFrame(columns=[
            'index_code', 'index_name', 'index_type', 'symbol', 'symbol_name',
            'weight', 'market_cap', 'free_float', 'effective_date', 'end_date',
            'is_active', 'source'
        ])
    
    data = []
    for comp in components:
        data.append({
            'index_code': comp.index_code,
            'index_name': comp.index_name,
            'index_type': comp.index_type.value,
            'symbol': comp.symbol,
            'symbol_name': comp.symbol_name,
            'weight': comp.weight,
            'market_cap': comp.market_cap,
            'free_float': comp.free_float,
            'effective_date': comp.effective_date,
            'end_date': comp.end_date,
            'is_active': comp.is_active,
            'source': comp.source
        })
    
    return pd.DataFrame(data)


def df_to_index_components(df: pd.DataFrame) -> List[IndexComponentData]:
    """将DataFrame转换为指数成分数据列表"""
    components = []
    for _, row in df.iterrows():
        comp = IndexComponentData(
            index_code=row['index_code'],
            index_name=row['index_name'],
            index_type=IndexType(row['index_type']),
            symbol=row['symbol'],
            symbol_name=row['symbol_name'],
            weight=row['weight'],
            market_cap=row.get('market_cap'),
            free_float=row.get('free_float'),
            effective_date=row.get('effective_date'),
            end_date=row.get('end_date'),
            is_active=row.get('is_active', True),
            source=row.get('source', '')
        )
        components.append(comp)
    
    return components


def industry_classifications_to_df(classifications: List[IndustryClassificationData]) -> pd.DataFrame:
    """将行业分类数据列表转换为DataFrame"""
    if not classifications:
        return pd.DataFrame(columns=[
            'symbol', 'symbol_name', 'industry_code', 'industry_name',
            'industry_level', 'industry_standard', 'parent_industry_code',
            'parent_industry_name', 'effective_date', 'end_date',
            'is_active', 'source'
        ])
    
    data = []
    for cls in classifications:
        data.append({
            'symbol': cls.symbol,
            'symbol_name': cls.symbol_name,
            'industry_code': cls.industry_code,
            'industry_name': cls.industry_name,
            'industry_level': cls.industry_level.value,
            'industry_standard': cls.industry_standard.value,
            'parent_industry_code': cls.parent_industry_code,
            'parent_industry_name': cls.parent_industry_name,
            'effective_date': cls.effective_date,
            'end_date': cls.end_date,
            'is_active': cls.is_active,
            'source': cls.source
        })
    
    return pd.DataFrame(data)


def df_to_industry_classifications(df: pd.DataFrame) -> List[IndustryClassificationData]:
    """将DataFrame转换为行业分类数据列表"""
    classifications = []
    for _, row in df.iterrows():
        cls = IndustryClassificationData(
            symbol=row['symbol'],
            symbol_name=row['symbol_name'],
            industry_code=row['industry_code'],
            industry_name=row['industry_name'],
            industry_level=IndustryLevel(row['industry_level']),
            industry_standard=IndustryStandard(row['industry_standard']),
            parent_industry_code=row.get('parent_industry_code'),
            parent_industry_name=row.get('parent_industry_name'),
            effective_date=row.get('effective_date'),
            end_date=row.get('end_date'),
            is_active=row.get('is_active', True),
            source=row.get('source', '')
        )
        classifications.append(cls)
    
    return classifications


def macro_data_to_df(macro_data: List[MacroData]) -> pd.DataFrame:
    """将宏观数据列表转换为DataFrame"""
    if not macro_data:
        return pd.DataFrame(columns=[
            'data_code', 'data_name', 'data_type', 'frequency', 'date', 'value',
            'unit', 'previous_value', 'change_value', 'change_rate',
            'seasonally_adjusted', 'source', 'description'
        ])
    
    data = []
    for macro in macro_data:
        data.append({
            'data_code': macro.data_code,
            'data_name': macro.data_name,
            'data_type': macro.data_type.value,
            'frequency': macro.frequency.value,
            'date': macro.date,
            'value': macro.value,
            'unit': macro.unit,
            'previous_value': macro.previous_value,
            'change_value': macro.change_value,
            'change_rate': macro.change_rate,
            'seasonally_adjusted': macro.seasonally_adjusted,
            'source': macro.source,
            'description': macro.description
        })
    
    return pd.DataFrame(data)


def df_to_macro_data(df: pd.DataFrame) -> List[MacroData]:
    """将DataFrame转换为宏观数据列表"""
    macro_data = []
    for _, row in df.iterrows():
        macro = MacroData(
            data_code=row['data_code'],
            data_name=row['data_name'],
            data_type=MacroDataType(row['data_type']),
            frequency=DataFrequency(row['frequency']),
            date=row['date'],
            value=row['value'],
            unit=row.get('unit', ''),
            previous_value=row.get('previous_value'),
            change_value=row.get('change_value'),
            change_rate=row.get('change_rate'),
            seasonally_adjusted=row.get('seasonally_adjusted', False),
            source=row.get('source', ''),
            description=row.get('description', '')
        )
        macro_data.append(macro)
    
    return macro_data


# ========== 常量定义 ==========

# 指数成分数据列名
INDEX_COMPONENT_COLUMNS = [
    'index_code', 'index_name', 'index_type', 'symbol', 'symbol_name',
    'weight', 'market_cap', 'free_float', 'effective_date', 'end_date',
    'is_active', 'source'
]

# 行业分类数据列名
INDUSTRY_CLASSIFICATION_COLUMNS = [
    'symbol', 'symbol_name', 'industry_code', 'industry_name',
    'industry_level', 'industry_standard', 'parent_industry_code',
    'parent_industry_name', 'effective_date', 'end_date',
    'is_active', 'source'
]

# 宏观数据列名
MACRO_DATA_COLUMNS = [
    'data_code', 'data_name', 'data_type', 'frequency', 'date', 'value',
    'unit', 'previous_value', 'change_value', 'change_rate',
    'seasonally_adjusted', 'source', 'description'
]

# 数据类型映射
THIRD_PARTY_DTYPES = {
    'index_code': 'string',
    'index_name': 'string',
    'symbol': 'string',
    'symbol_name': 'string',
    'industry_code': 'string',
    'industry_name': 'string',
    'parent_industry_code': 'string',
    'parent_industry_name': 'string',
    'data_code': 'string',
    'data_name': 'string',
    'unit': 'string',
    'source': 'string',
    'description': 'string',
    'effective_date': 'datetime64[ns]',
    'end_date': 'datetime64[ns]',
    'date': 'datetime64[ns]',
    'index_type': 'category',
    'industry_level': 'category',
    'industry_standard': 'category',
    'data_type': 'category',
    'frequency': 'category',
    'weight': 'float32',
    'market_cap': 'float32',
    'free_float': 'float32',
    'value': 'float32',
    'previous_value': 'float32',
    'change_value': 'float32',
    'change_rate': 'float32',
    'is_active': 'boolean',
    'seasonally_adjusted': 'boolean'
}
