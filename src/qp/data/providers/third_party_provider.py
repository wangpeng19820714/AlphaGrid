# qp/data/providers/third_party_provider.py
"""
第三方数据提供者

提供指数成分、行业分类、宏观数据等第三方数据的获取功能
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from .base import BaseProvider
from ..types.third_party import (
    IndexComponentData, IndustryClassificationData, MacroData,
    IndexType, IndustryLevel, IndustryStandard, MacroDataType, DataFrequency
)


class ThirdPartyProvider(BaseProvider):
    """第三方数据提供者基类"""
    
    def get_index_components(self, index_code: str, date: Optional[str] = None) -> List[IndexComponentData]:
        """
        获取指数成分数据
        
        Args:
            index_code: 指数代码
            date: 查询日期，如果为None则获取最新数据
            
        Returns:
            指数成分数据列表
        """
        raise NotImplementedError("子类必须实现 get_index_components 方法")
    
    def get_industry_classifications(self, symbol: str, 
                                   industry_standard: Optional[str] = None,
                                   industry_level: Optional[str] = None) -> List[IndustryClassificationData]:
        """
        获取行业分类数据
        
        Args:
            symbol: 股票代码
            industry_standard: 行业分类标准
            industry_level: 行业分类级别
            
        Returns:
            行业分类数据列表
        """
        raise NotImplementedError("子类必须实现 get_industry_classifications 方法")
    
    def get_macro_data(self, data_code: str, start_date: str, end_date: str,
                      data_type: Optional[str] = None) -> List[MacroData]:
        """
        获取宏观数据
        
        Args:
            data_code: 数据代码
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型过滤
            
        Returns:
            宏观数据列表
        """
        raise NotImplementedError("子类必须实现 get_macro_data 方法")


class MockThirdPartyProvider(ThirdPartyProvider):
    """模拟第三方数据提供者（用于测试）"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "mock_third_party"
    
    def get_index_components(self, index_code: str, date: Optional[str] = None) -> List[IndexComponentData]:
        """获取模拟指数成分数据"""
        components = []
        
        # 根据指数代码生成不同的成分数据
        if index_code == "000001.SH":  # 上证指数
            symbols = ["600000.SH", "600036.SH", "600519.SH", "000001.SZ", "000002.SZ"]
            names = ["浦发银行", "招商银行", "贵州茅台", "平安银行", "万科A"]
            weights = [0.15, 0.12, 0.20, 0.18, 0.10]
            index_name = "上证指数"
            index_type = IndexType.BROAD_MARKET
        elif index_code == "399001.SZ":  # 深证成指
            symbols = ["000001.SZ", "000002.SZ", "000858.SZ", "002415.SZ", "300750.SZ"]
            names = ["平安银行", "万科A", "五粮液", "海康威视", "宁德时代"]
            weights = [0.18, 0.15, 0.12, 0.10, 0.08]
            index_name = "深证成指"
            index_type = IndexType.BROAD_MARKET
        elif index_code == "000016.SH":  # 上证50
            symbols = ["600519.SH", "600036.SH", "600000.SH", "000001.SZ", "600276.SH"]
            names = ["贵州茅台", "招商银行", "浦发银行", "平安银行", "恒瑞医药"]
            weights = [0.25, 0.15, 0.12, 0.10, 0.08]
            index_name = "上证50"
            index_type = IndexType.BROAD_MARKET
        else:  # 默认
            symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH", "600519.SH"]
            names = ["平安银行", "万科A", "浦发银行", "招商银行", "贵州茅台"]
            weights = [0.20, 0.18, 0.15, 0.12, 0.10]
            index_name = f"指数{index_code}"
            index_type = IndexType.BROAD_MARKET
        
        # 生成成分数据
        for i, (symbol, name, weight) in enumerate(zip(symbols, names, weights)):
            component = IndexComponentData(
                index_code=index_code,
                index_name=index_name,
                index_type=index_type,
                symbol=symbol,
                symbol_name=name,
                weight=weight,
                market_cap=1000000 + i * 100000,  # 模拟市值
                free_float=800000 + i * 80000,    # 模拟自由流通市值
                effective_date=datetime.now() - timedelta(days=30),
                is_active=True,
                source="模拟数据源"
            )
            components.append(component)
        
        return components
    
    def get_industry_classifications(self, symbol: str, 
                                   industry_standard: Optional[str] = None,
                                   industry_level: Optional[str] = None) -> List[IndustryClassificationData]:
        """获取模拟行业分类数据"""
        classifications = []
        
        # 模拟不同股票的行业分类
        industry_mapping = {
            "000001.SZ": ("801010", "银行", IndustryLevel.LEVEL1),
            "000002.SZ": ("801110", "房地产", IndustryLevel.LEVEL1),
            "600000.SH": ("801010", "银行", IndustryLevel.LEVEL1),
            "600036.SH": ("801010", "银行", IndustryLevel.LEVEL1),
            "600519.SH": ("801120", "食品饮料", IndustryLevel.LEVEL1),
            "000858.SZ": ("801120", "食品饮料", IndustryLevel.LEVEL1),
            "002415.SZ": ("801080", "电子", IndustryLevel.LEVEL1),
            "300750.SZ": ("801880", "电力设备", IndustryLevel.LEVEL1),
        }
        
        industry_code, industry_name, level = industry_mapping.get(
            symbol, ("801000", "其他", IndustryLevel.LEVEL1)
        )
        
        # 生成不同级别的行业分类
        levels = [IndustryLevel.LEVEL1, IndustryLevel.LEVEL2, IndustryLevel.LEVEL3]
        if industry_level and IndustryLevel(industry_level) in levels:
            levels = [IndustryLevel(industry_level)]
        
        for i, level_enum in enumerate(levels):
            if level_enum == IndustryLevel.LEVEL1:
                code = industry_code
                name = industry_name
                parent_code = None
                parent_name = None
            elif level_enum == IndustryLevel.LEVEL2:
                code = industry_code + "10"
                name = f"{industry_name}子行业"
                parent_code = industry_code
                parent_name = industry_name
            else:  # LEVEL3
                code = industry_code + "20"
                name = f"{industry_name}细分行业"
                parent_code = industry_code + "10"
                parent_name = f"{industry_name}子行业"
            
            classification = IndustryClassificationData(
                symbol=symbol,
                symbol_name=f"股票{symbol}",
                industry_code=code,
                industry_name=name,
                industry_level=level_enum,
                industry_standard=IndustryStandard.SW,
                parent_industry_code=parent_code,
                parent_industry_name=parent_name,
                effective_date=datetime.now() - timedelta(days=30),
                is_active=True,
                source="模拟数据源"
            )
            classifications.append(classification)
        
        return classifications
    
    def get_macro_data(self, data_code: str, start_date: str, end_date: str,
                      data_type: Optional[str] = None) -> List[MacroData]:
        """获取模拟宏观数据"""
        macro_data = []
        
        # 根据数据代码生成不同的宏观数据
        data_mapping = {
            "GDP": ("GDP", "国内生产总值", MacroDataType.GDP, DataFrequency.QUARTERLY, "亿元"),
            "CPI": ("CPI", "消费者价格指数", MacroDataType.CPI, DataFrequency.MONTHLY, "%"),
            "PPI": ("PPI", "生产者价格指数", MacroDataType.PPI, DataFrequency.MONTHLY, "%"),
            "M2": ("M2", "货币供应量M2", MacroDataType.MONEY_SUPPLY, DataFrequency.MONTHLY, "亿元"),
            "RATE": ("RATE", "基准利率", MacroDataType.INTEREST_RATE, DataFrequency.IRREGULAR, "%"),
        }
        
        data_name, data_desc, data_type_enum, frequency, unit = data_mapping.get(
            data_code, ("CUSTOM", "自定义数据", MacroDataType.CUSTOM, DataFrequency.MONTHLY, "")
        )
        
        if data_type and MacroDataType(data_type) != data_type_enum:
            return macro_data
        
        # 生成时间序列数据
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        if frequency == DataFrequency.QUARTERLY:
            # 季度数据
            dates = pd.date_range(start_dt, end_dt, freq='Q')
        elif frequency == DataFrequency.MONTHLY:
            # 月度数据
            dates = pd.date_range(start_dt, end_dt, freq='M')
        elif frequency == DataFrequency.YEARLY:
            # 年度数据
            dates = pd.date_range(start_dt, end_dt, freq='Y')
        else:
            # 日度数据
            dates = pd.date_range(start_dt, end_dt, freq='D')
        
        # 生成模拟数据
        base_value = 100.0
        for i, date in enumerate(dates):
            # 模拟数据变化
            if data_type_enum == MacroDataType.GDP:
                value = base_value + i * 2.5 + (i % 4) * 0.5  # GDP增长趋势
            elif data_type_enum == MacroDataType.CPI:
                value = 2.0 + (i % 12) * 0.1 + (i % 4) * 0.05  # CPI波动
            elif data_type_enum == MacroDataType.PPI:
                value = 1.5 + (i % 12) * 0.08 + (i % 6) * 0.03  # PPI波动
            elif data_type_enum == MacroDataType.MONEY_SUPPLY:
                value = base_value * (1.1 ** (i / 12))  # 货币供应量增长
            elif data_type_enum == MacroDataType.INTEREST_RATE:
                value = 3.0 + (i % 24) * 0.1  # 利率变化
            else:
                value = base_value + i * 0.5
            
            # 计算变化值
            previous_value = value - 0.5 if i > 0 else None
            change_value = value - previous_value if previous_value else None
            change_rate = (change_value / previous_value * 100) if previous_value else None
            
            macro = MacroData(
                data_code=data_code,
                data_name=data_name,
                data_type=data_type_enum,
                frequency=frequency,
                date=date,
                value=round(value, 2),
                unit=unit,
                previous_value=round(previous_value, 2) if previous_value else None,
                change_value=round(change_value, 2) if change_value else None,
                change_rate=round(change_rate, 2) if change_rate else None,
                seasonally_adjusted=frequency == DataFrequency.QUARTERLY,
                source="模拟数据源",
                description=data_desc
            )
            macro_data.append(macro)
        
        return macro_data


class AkshareThirdPartyProvider(ThirdPartyProvider):
    """基于AKShare的第三方数据提供者"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "akshare_third_party"
        try:
            import akshare as ak
            self.ak = ak
        except ImportError:
            raise ImportError("请安装 akshare: pip install akshare")
    
    def get_index_components(self, index_code: str, date: Optional[str] = None) -> List[IndexComponentData]:
        """使用AKShare获取指数成分数据"""
        try:
            # 这里需要根据AKShare的实际API来实现
            # 目前返回空列表，实际使用时需要调用相应的AKShare接口
            return []
        except Exception as e:
            print(f"获取指数成分数据失败: {e}")
            return []
    
    def get_industry_classifications(self, symbol: str, 
                                   industry_standard: Optional[str] = None,
                                   industry_level: Optional[str] = None) -> List[IndustryClassificationData]:
        """使用AKShare获取行业分类数据"""
        try:
            # 这里需要根据AKShare的实际API来实现
            return []
        except Exception as e:
            print(f"获取行业分类数据失败: {e}")
            return []
    
    def get_macro_data(self, data_code: str, start_date: str, end_date: str,
                      data_type: Optional[str] = None) -> List[MacroData]:
        """使用AKShare获取宏观数据"""
        try:
            # 这里需要根据AKShare的实际API来实现
            return []
        except Exception as e:
            print(f"获取宏观数据失败: {e}")
            return []
