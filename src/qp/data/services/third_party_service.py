# qp/data/services/third_party_service.py
"""
第三方数据服务

提供指数成分、行业分类、宏观数据的业务逻辑和分析功能
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from .base import BaseDataService
from ..providers.third_party_provider import ThirdPartyProvider, MockThirdPartyProvider
from ..types.third_party import (
    IndexComponentData, IndustryClassificationData, MacroData,
    IndexType, IndustryLevel, IndustryStandard, MacroDataType, DataFrequency
)


class ThirdPartyDataService(BaseDataService):
    """第三方数据服务"""
    
    def __init__(self, provider: Optional[ThirdPartyProvider] = None):
        super().__init__()
        self.provider = provider or MockThirdPartyProvider()
    
    # ========== 指数成分数据服务 ==========
    
    def get_index_components(self, index_code: str, date: Optional[str] = None) -> List[IndexComponentData]:
        """
        获取指数成分数据
        
        Args:
            index_code: 指数代码
            date: 查询日期，如果为None则获取最新数据
            
        Returns:
            指数成分数据列表
        """
        return self.provider.get_index_components(index_code, date)
    
    def get_index_components_by_weight(self, index_code: str, min_weight: float = 0.01,
                                     date: Optional[str] = None) -> List[IndexComponentData]:
        """
        获取权重大于指定值的指数成分
        
        Args:
            index_code: 指数代码
            min_weight: 最小权重阈值
            date: 查询日期
            
        Returns:
            符合条件的指数成分数据列表
        """
        components = self.get_index_components(index_code, date)
        return [comp for comp in components if comp.weight >= min_weight]
    
    def get_top_components(self, index_code: str, top_n: int = 10,
                          date: Optional[str] = None) -> List[IndexComponentData]:
        """
        获取权重排名前N的成分股
        
        Args:
            index_code: 指数代码
            top_n: 前N名
            date: 查询日期
            
        Returns:
            权重排名前N的成分股列表
        """
        components = self.get_index_components(index_code, date)
        return sorted(components, key=lambda x: x.weight, reverse=True)[:top_n]
    
    def analyze_index_concentration(self, index_code: str, 
                                  date: Optional[str] = None) -> Dict[str, Any]:
        """
        分析指数集中度
        
        Args:
            index_code: 指数代码
            date: 查询日期
            
        Returns:
            集中度分析结果
        """
        components = self.get_index_components(index_code, date)
        if not components:
            return {}
        
        weights = [comp.weight for comp in components]
        total_weight = sum(weights)
        
        # 计算前10大权重
        top10_weight = sum(sorted(weights, reverse=True)[:10])
        
        # 计算赫芬达尔指数（HHI）
        hhi = sum(w * w for w in weights)
        
        return {
            "total_components": len(components),
            "total_weight": total_weight,
            "top10_weight": top10_weight,
            "top10_concentration": top10_weight / total_weight if total_weight > 0 else 0,
            "hhi": hhi,
            "max_weight": max(weights),
            "min_weight": min(weights),
            "avg_weight": total_weight / len(components)
        }
    
    # ========== 行业分类数据服务 ==========
    
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
        return self.provider.get_industry_classifications(symbol, industry_standard, industry_level)
    
    def get_industry_by_level(self, symbol: str, level: IndustryLevel,
                            industry_standard: Optional[str] = None) -> Optional[IndustryClassificationData]:
        """
        获取指定级别的行业分类
        
        Args:
            symbol: 股票代码
            level: 行业分类级别
            industry_standard: 行业分类标准
            
        Returns:
            指定级别的行业分类数据
        """
        classifications = self.get_industry_classifications(symbol, industry_standard)
        for cls in classifications:
            if cls.industry_level == level:
                return cls
        return None
    
    def get_industry_hierarchy(self, symbol: str, 
                             industry_standard: Optional[str] = None) -> Dict[str, IndustryClassificationData]:
        """
        获取完整的行业分类层级
        
        Args:
            symbol: 股票代码
            industry_standard: 行业分类标准
            
        Returns:
            按级别分组的行业分类数据
        """
        classifications = self.get_industry_classifications(symbol, industry_standard)
        hierarchy = {}
        
        for cls in classifications:
            level_key = f"level{cls.industry_level.value.split('level')[1]}"
            hierarchy[level_key] = cls
        
        return hierarchy
    
    def get_industry_statistics(self, symbols: List[str],
                              industry_standard: Optional[str] = None) -> Dict[str, Any]:
        """
        获取行业统计信息
        
        Args:
            symbols: 股票代码列表
            industry_standard: 行业分类标准
            
        Returns:
            行业统计信息
        """
        industry_counts = {}
        level_counts = {}
        
        for symbol in symbols:
            classifications = self.get_industry_classifications(symbol, industry_standard)
            for cls in classifications:
                # 统计行业分布
                industry_key = f"{cls.industry_code}_{cls.industry_name}"
                industry_counts[industry_key] = industry_counts.get(industry_key, 0) + 1
                
                # 统计级别分布
                level_key = cls.industry_level.value
                level_counts[level_key] = level_counts.get(level_key, 0) + 1
        
        return {
            "total_symbols": len(symbols),
            "industry_distribution": industry_counts,
            "level_distribution": level_counts,
            "most_common_industry": max(industry_counts.items(), key=lambda x: x[1]) if industry_counts else None
        }
    
    # ========== 宏观数据服务 ==========
    
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
        return self.provider.get_macro_data(data_code, start_date, end_date, data_type)
    
    def get_macro_data_by_type(self, data_type: MacroDataType, start_date: str, end_date: str) -> List[MacroData]:
        """
        按数据类型获取宏观数据
        
        Args:
            data_type: 宏观数据类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指定类型的宏观数据列表
        """
        # 根据数据类型映射数据代码
        data_code_mapping = {
            MacroDataType.GDP: "GDP",
            MacroDataType.CPI: "CPI",
            MacroDataType.PPI: "PPI",
            MacroDataType.MONEY_SUPPLY: "M2",
            MacroDataType.INTEREST_RATE: "RATE",
        }
        
        data_code = data_code_mapping.get(data_type, data_type.value.upper())
        return self.get_macro_data(data_code, start_date, end_date, data_type.value)
    
    def get_latest_macro_data(self, data_code: str) -> Optional[MacroData]:
        """
        获取最新的宏观数据
        
        Args:
            data_code: 数据代码
            
        Returns:
            最新的宏观数据
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        macro_data = self.get_macro_data(data_code, start_date, end_date)
        if macro_data:
            return max(macro_data, key=lambda x: x.date)
        return None
    
    def analyze_macro_trend(self, data_code: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        分析宏观数据趋势
        
        Args:
            data_code: 数据代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            趋势分析结果
        """
        macro_data = self.get_macro_data(data_code, start_date, end_date)
        if not macro_data:
            return {}
        
        # 转换为DataFrame进行分析
        df = pd.DataFrame([{
            'date': macro.date,
            'value': macro.value,
            'change_rate': macro.change_rate
        } for macro in macro_data])
        
        df = df.sort_values('date')
        
        # 计算趋势指标
        values = df['value'].values
        first_value = values[0]
        last_value = values[-1]
        total_change = last_value - first_value
        total_change_rate = (total_change / first_value * 100) if first_value != 0 else 0
        
        # 计算移动平均
        if len(values) >= 12:
            ma12 = values[-12:].mean()
            ma6 = values[-6:].mean() if len(values) >= 6 else values.mean()
        else:
            ma12 = values.mean()
            ma6 = values.mean()
        
        # 计算波动率
        volatility = df['value'].std() if len(df) > 1 else 0
        
        return {
            "data_code": data_code,
            "period": f"{start_date} to {end_date}",
            "data_points": len(macro_data),
            "first_value": first_value,
            "last_value": last_value,
            "total_change": total_change,
            "total_change_rate": round(total_change_rate, 2),
            "average_value": values.mean(),
            "ma12": round(ma12, 2),
            "ma6": round(ma6, 2),
            "volatility": round(volatility, 2),
            "max_value": values.max(),
            "min_value": values.min(),
            "trend": "上升" if total_change > 0 else "下降" if total_change < 0 else "平稳"
        }
    
    def get_macro_correlation(self, data_codes: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
        """
        分析多个宏观数据之间的相关性
        
        Args:
            data_codes: 数据代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            相关性分析结果
        """
        all_data = {}
        
        # 获取所有数据
        for data_code in data_codes:
            macro_data = self.get_macro_data(data_code, start_date, end_date)
            if macro_data:
                df = pd.DataFrame([{
                    'date': macro.date,
                    'value': macro.value
                } for macro in macro_data])
                df = df.set_index('date')
                all_data[data_code] = df['value']
        
        if len(all_data) < 2:
            return {"error": "需要至少2个数据系列进行相关性分析"}
        
        # 合并数据
        combined_df = pd.DataFrame(all_data)
        combined_df = combined_df.dropna()  # 删除缺失值
        
        if len(combined_df) < 2:
            return {"error": "有效数据点不足进行相关性分析"}
        
        # 计算相关性矩阵
        correlation_matrix = combined_df.corr()
        
        return {
            "data_codes": data_codes,
            "period": f"{start_date} to {end_date}",
            "data_points": len(combined_df),
            "correlation_matrix": correlation_matrix.to_dict(),
            "strong_correlations": self._find_strong_correlations(correlation_matrix)
        }
    
    def _find_strong_correlations(self, correlation_matrix: pd.DataFrame, 
                                threshold: float = 0.7) -> List[Dict[str, Any]]:
        """查找强相关性"""
        strong_correlations = []
        
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    strong_correlations.append({
                        "series1": correlation_matrix.columns[i],
                        "series2": correlation_matrix.columns[j],
                        "correlation": round(corr_value, 3),
                        "strength": "强正相关" if corr_value > 0 else "强负相关"
                    })
        
        return strong_correlations
