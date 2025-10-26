# qp/data/stores/data_layers_models.py
"""数据分层模型定义 - ODS/DWD/DWS层的数据类型"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

from ..types.common import Exchange, Interval

# 导入DWD层数据模型
from .dwd_store import DWDFinancialData, DWDFundamentalData


# ========== ODS层数据模型 ==========

@dataclass
class ODSBarData:
    """ODS层原始K线数据"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    
    # 原始价格数据
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    
    # 原始成交量数据
    volume: float
    turnover: float
    
    # 原始数据元信息
    source: str                    # 数据源
    raw_data: Dict[str, Any]      # 原始数据字段
    quality_score: float          # 数据质量分数
    created_at: datetime          # 创建时间
    updated_at: datetime          # 更新时间


@dataclass
class ODSFinancialData:
    """ODS层原始财务数据"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp
    report_type: str              # 年报、中报、季报
    
    # 原始财务数据
    raw_income: Dict[str, float]     # 利润表原始数据
    raw_balance: Dict[str, float]    # 资产负债表原始数据
    raw_cashflow: Dict[str, float]   # 现金流量表原始数据
    
    # 元信息
    source: str
    quality_score: float
    created_at: datetime
    updated_at: datetime


@dataclass
class ODSFundamentalData:
    """ODS层原始基本面数据"""
    symbol: str
    exchange: Exchange
    date: pd.Timestamp
    
    # 原始基本面数据
    raw_data: Dict[str, Any]      # 原始基本面数据字段
    
    # 元信息
    source: str
    quality_score: float
    created_at: datetime
    updated_at: datetime


# ========== DWD层数据模型 ==========

@dataclass
class DWDBarData:
    """DWD层规整K线数据"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    
    # 规整价格数据
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    
    # 规整成交量数据
    volume: float
    turnover: float
    amount: float          # 成交额
    vwap: float           # 成交量加权平均价
    
    # 数据质量信息
    is_valid: bool           # 数据是否有效
    quality_issues: List[str]  # 质量问题列表
    processed_at: datetime   # 处理时间


@dataclass
class DWDFinancialData:
    """DWD层规整财务数据"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp
    report_type: str
    
    # 规整财务指标
    total_revenue: float
    net_profit: float
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    
    # 计算字段
    revenue_growth: float     # 营收增长率
    profit_growth: float      # 利润增长率
    roe: float               # 净资产收益率
    roa: float               # 总资产收益率
    
    # 数据质量
    is_valid: bool
    quality_issues: List[str]
    processed_at: datetime


# ========== DWS层数据模型 ==========

@dataclass
class DWSAdjustedData:
    """DWS层复权价格数据"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    
    # 复权价格
    open_qfq: float          # 前复权开盘价
    high_qfq: float          # 前复权最高价
    low_qfq: float           # 前复权最低价
    close_qfq: float         # 前复权收盘价
    
    open_hfq: float          # 后复权开盘价
    high_hfq: float          # 后复权最高价
    low_hfq: float           # 后复权最低价
    close_hfq: float         # 后复权收盘价
    
    # 复权因子
    qfq_factor: float        # 前复权因子
    hfq_factor: float        # 后复权因子
    
    # 元信息
    adjusted_at: datetime
    source_dwd: str


@dataclass
class DWSFactorData:
    """DWS层资金因子数据"""
    symbol: str
    exchange: Exchange
    datetime: pd.Timestamp
    
    # 资金流向因子
    net_inflow: float         # 净流入
    main_inflow: float        # 主力流入
    retail_inflow: float      # 散户流入
    
    # 成交量因子
    volume_ratio: float       # 成交量比
    price_volume_ratio: float # 价量比
    
    # 价格动量因子
    price_momentum_5d: float  # 5日价格动量
    price_momentum_20d: float # 20日价格动量
    
    # 元信息
    calculated_at: datetime
    source_dwd: str


@dataclass
class DWSMergedFinancialData:
    """DWS层财务合并表"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp
    
    # 财务比率
    pe_ratio: float           # 市盈率
    pb_ratio: float           # 市净率
    ps_ratio: float           # 市销率
    pcf_ratio: float          # 市现率
    
    # 成长指标
    revenue_growth_yoy: float # 营收同比增长
    profit_growth_yoy: float  # 利润同比增长
    
    # 盈利能力
    roe: float               # 净资产收益率
    roa: float               # 总资产收益率
    gross_margin: float       # 毛利率
    net_margin: float         # 净利率
    
    # 元信息
    merged_at: datetime
    source_dwd: str


# ========== 数据转换函数 ==========

def ods_financial_to_dwd_financial(ods_financial: ODSFinancialData) -> DWDFinancialData:
    """ODS财务数据转换为DWD财务数据"""
    # 提取规整财务指标
    total_revenue = ods_financial.raw_income.get('total_revenue', 0.0)
    net_profit = ods_financial.raw_income.get('net_profit', 0.0)
    total_assets = ods_financial.raw_balance.get('total_assets', 0.0)
    total_liabilities = ods_financial.raw_balance.get('total_liabilities', 0.0)
    shareholders_equity = ods_financial.raw_balance.get('shareholders_equity', 0.0)
    
    # 计算增长率（需要历史数据，这里简化处理）
    revenue_growth = 0.0
    profit_growth = 0.0
    
    # 计算财务比率
    roe = (net_profit / shareholders_equity * 100) if shareholders_equity > 0 else 0.0
    roa = (net_profit / total_assets * 100) if total_assets > 0 else 0.0
    
    # 数据质量检查
    quality_issues = []
    if total_revenue < 0:
        quality_issues.append("营收为负数")
    if net_profit == 0 and total_revenue > 0:
        quality_issues.append("营收为正但净利润为0")
    if total_assets <= 0:
        quality_issues.append("总资产无效")
    
    is_valid = len(quality_issues) == 0
    
    return DWDFinancialData(
        symbol=ods_financial.symbol,
        exchange=ods_financial.exchange,
        report_date=ods_financial.report_date,
        report_type=ods_financial.report_type,
        total_revenue=total_revenue,
        net_profit=net_profit,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        shareholders_equity=shareholders_equity,
        revenue_growth=revenue_growth,
        profit_growth=profit_growth,
        roe=roe,
        roa=roa,
        is_valid=is_valid,
        quality_issues=quality_issues,
        processed_at=datetime.now()
    )


def ods_fundamental_to_dwd_fundamental(ods_fundamental: ODSFundamentalData) -> DWDFundamentalData:
    """ODS基本面数据转换为DWD基本面数据"""
    raw_data = ods_fundamental.raw_data
    
    # 提取规整基本面指标
    pe_ratio = raw_data.get('pe_ratio', 0.0)
    pb_ratio = raw_data.get('pb_ratio', 0.0)
    ps_ratio = raw_data.get('ps_ratio', 0.0)
    market_cap = raw_data.get('market_cap', 0.0)
    circulating_cap = raw_data.get('circulating_cap', 0.0)
    
    # 数据质量检查
    quality_issues = []
    if pe_ratio < 0:
        quality_issues.append("市盈率为负数")
    if pb_ratio < 0:
        quality_issues.append("市净率为负数")
    if market_cap <= 0:
        quality_issues.append("市值无效")
    if circulating_cap > market_cap:
        quality_issues.append("流通市值大于总市值")
    
    is_valid = len(quality_issues) == 0
    
    return DWDFundamentalData(
        symbol=ods_fundamental.symbol,
        exchange=ods_fundamental.exchange,
        date=ods_fundamental.date,
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
        ps_ratio=ps_ratio,
        market_cap=market_cap,
        circulating_cap=circulating_cap,
        is_valid=is_valid,
        quality_issues=quality_issues,
        processed_at=datetime.now()
    )


def ods_bar_to_dwd_bar(ods_bar: ODSBarData) -> DWDBarData:
    """将ODS层K线数据转换为DWD层数据"""
    # 计算VWAP
    vwap = (ods_bar.open_price + ods_bar.high_price + ods_bar.low_price + ods_bar.close_price) / 4
    
    # 计算成交额
    amount = ods_bar.volume * ods_bar.close_price
    
    # 数据质量检查
    quality_issues = []
    if not (ods_bar.low_price <= ods_bar.open_price <= ods_bar.high_price):
        quality_issues.append("价格关系异常")
    if not (ods_bar.low_price <= ods_bar.close_price <= ods_bar.high_price):
        quality_issues.append("价格关系异常")
    if ods_bar.volume < 0:
        quality_issues.append("成交量异常")
    
    return DWDBarData(
        symbol=ods_bar.symbol,
        exchange=ods_bar.exchange,
        interval=ods_bar.interval,
        datetime=ods_bar.datetime,
        open_price=ods_bar.open_price,
        high_price=ods_bar.high_price,
        low_price=ods_bar.low_price,
        close_price=ods_bar.close_price,
        volume=ods_bar.volume,
        turnover=ods_bar.turnover,
        amount=amount,
        vwap=vwap,
        is_valid=len(quality_issues) == 0,
        quality_issues=quality_issues,
        processed_at=datetime.now()
    )


def dwd_bar_to_dws_adjusted(dwd_bar: DWDBarData, qfq_factor: float = 1.0, hfq_factor: float = 1.0) -> DWSAdjustedData:
    """将DWD层K线数据转换为DWS层复权数据"""
    return DWSAdjustedData(
        symbol=dwd_bar.symbol,
        exchange=dwd_bar.exchange,
        interval=dwd_bar.interval,
        datetime=dwd_bar.datetime,
        open_qfq=dwd_bar.open_price * qfq_factor,
        high_qfq=dwd_bar.high_price * qfq_factor,
        low_qfq=dwd_bar.low_price * qfq_factor,
        close_qfq=dwd_bar.close_price * qfq_factor,
        open_hfq=dwd_bar.open_price * hfq_factor,
        high_hfq=dwd_bar.high_price * hfq_factor,
        low_hfq=dwd_bar.low_price * hfq_factor,
        close_hfq=dwd_bar.close_price * hfq_factor,
        qfq_factor=qfq_factor,
        hfq_factor=hfq_factor,
        adjusted_at=datetime.now(),
        source_dwd=f"dwd_bars_{dwd_bar.symbol}_{dwd_bar.exchange.value}_{dwd_bar.interval.value}"
    )


def dwd_bar_to_dws_factor(dwd_bar: DWDBarData, net_inflow: float = 0.0, 
                         volume_ratio: float = 1.0, momentum_5d: float = 0.0, 
                         momentum_20d: float = 0.0) -> DWSFactorData:
    """将DWD层K线数据转换为DWS层因子数据"""
    return DWSFactorData(
        symbol=dwd_bar.symbol,
        exchange=dwd_bar.exchange,
        datetime=dwd_bar.datetime,
        net_inflow=net_inflow,
        main_inflow=net_inflow * 0.7,  # 简化：主力占70%
        retail_inflow=net_inflow * 0.3,  # 简化：散户占30%
        volume_ratio=volume_ratio,
        price_volume_ratio=volume_ratio * momentum_5d,
        price_momentum_5d=momentum_5d,
        price_momentum_20d=momentum_20d,
        calculated_at=datetime.now(),
        source_dwd=f"dwd_bars_{dwd_bar.symbol}_{dwd_bar.exchange.value}_{dwd_bar.interval.value}"
    )


def dwd_financial_to_dws_merged(dwd_financial: DWDFinancialData, 
                               pe_ratio: float = 0.0, pb_ratio: float = 0.0) -> DWSMergedFinancialData:
    """将DWD层财务数据转换为DWS层财务合并表"""
    return DWSMergedFinancialData(
        symbol=dwd_financial.symbol,
        exchange=dwd_financial.exchange,
        report_date=dwd_financial.report_date,
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
        ps_ratio=0.0,  # 需要市值数据
        pcf_ratio=0.0,  # 需要市值数据
        revenue_growth_yoy=dwd_financial.revenue_growth,
        profit_growth_yoy=dwd_financial.profit_growth,
        roe=dwd_financial.roe,
        roa=dwd_financial.roa,
        gross_margin=0.0,  # 需要毛利率计算
        net_margin=0.0,    # 需要净利率计算
        merged_at=datetime.now(),
        source_dwd=f"dwd_financial_{dwd_financial.symbol}_{dwd_financial.exchange.value}"
    )


# ========== 数据质量检查 ==========

class DataQualityChecker:
    """数据质量检查器"""
    
    @staticmethod
    def check_ods_bar_quality(ods_bar: ODSBarData) -> Dict[str, Any]:
        """检查ODS层K线数据质量"""
        issues = []
        
        # 价格关系检查
        if not (ods_bar.low_price <= ods_bar.open_price <= ods_bar.high_price):
            issues.append("价格关系异常")
        
        if not (ods_bar.low_price <= ods_bar.close_price <= ods_bar.high_price):
            issues.append("价格关系异常")
        
        # 成交量检查
        if ods_bar.volume < 0:
            issues.append("成交量异常")
        
        # 成交额检查
        if ods_bar.turnover < 0:
            issues.append("成交额异常")
        
        return {
            'quality_score': 1.0 - len(issues) / 10.0,
            'issues': issues,
            'is_valid': len(issues) == 0
        }
    
    @staticmethod
    def check_dwd_bar_quality(dwd_bar: DWDBarData) -> Dict[str, Any]:
        """检查DWD层K线数据质量"""
        issues = []
        
        # VWAP检查
        if dwd_bar.vwap <= 0:
            issues.append("VWAP异常")
        
        # 成交额检查
        if dwd_bar.amount <= 0:
            issues.append("成交额异常")
        
        return {
            'quality_score': 1.0 - len(issues) / 10.0,
            'issues': issues,
            'is_valid': len(issues) == 0
        }
    
    @staticmethod
    def check_dws_adjusted_quality(dws_adjusted: DWSAdjustedData) -> Dict[str, Any]:
        """检查DWS层复权数据质量"""
        issues = []
        
        # 复权因子检查
        if dws_adjusted.qfq_factor <= 0:
            issues.append("前复权因子异常")
        
        if dws_adjusted.hfq_factor <= 0:
            issues.append("后复权因子异常")
        
        return {
            'quality_score': 1.0 - len(issues) / 10.0,
            'issues': issues,
            'is_valid': len(issues) == 0
        }


# ========== 数据分层配置 ==========

@dataclass
class DataLayerConfig:
    """数据分层配置"""
    # ODS层配置
    ods_root: str = "data/ods"
    ods_retention_days: int = 3650  # 10年
    ods_compression: str = "snappy"  # 压缩格式
    ods_partition_by: List[str] = None  # 分区策略
    
    # DWD层配置
    dwd_root: str = "data/dwd"
    dwd_retention_days: int = 1825  # 5年
    dwd_compression: str = "snappy"  # 压缩格式
    dwd_partition_by: List[str] = None  # 分区策略
    
    # DWS层配置
    dws_root: str = "data/dws"
    dws_retention_days: int = 1095  # 3年
    dws_compression: str = "snappy"  # 压缩格式
    dws_partition_by: List[str] = None  # 分区策略
    
    # 处理配置
    batch_size: int = 1000
    parallel_workers: int = 4
    quality_threshold: float = 0.8
    
    def __post_init__(self):
        """初始化后处理"""
        # 设置默认分区策略
        if self.ods_partition_by is None:
            self.ods_partition_by = ['market', 'date', 'symbol']
        if self.dwd_partition_by is None:
            self.dwd_partition_by = ['market', 'symbol']
        if self.dws_partition_by is None:
            self.dws_partition_by = ['market', 'symbol']
