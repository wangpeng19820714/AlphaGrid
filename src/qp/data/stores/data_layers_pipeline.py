# qp/data/stores/data_layers_pipeline.py
"""数据分层管道 - 统一的数据流转处理"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import logging

from .ods_store import ODSStore, ODSBarData, ODSFinancialData, create_ods_bar_from_bar_data
from .dwd_store import DWDStore, DWDBarData, DWDFinancialData, DWDProcessor, create_dwd_bar_from_ods_bar
from .dws_store import DWSStore, DWSAdjustedData, DWSFactorData, DWSMergedFinancialData, DWSProcessor
from .data_layers_models import DataLayerConfig, DataQualityChecker
from ..types.bar import BarData
from ..types.common import Exchange, Interval


class DataLayersPipeline:
    """数据分层管道 - 统一的数据流转处理"""
    
    def __init__(self, config: DataLayerConfig = None):
        """
        初始化数据分层管道
        
        Args:
            config: 数据分层配置
        """
        if config is None:
            config = DataLayerConfig()
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化各层存储
        from .base import StoreConfig
        
        self.ods_store = ODSStore(StoreConfig(root=config.ods_root))
        self.dwd_store = DWDStore(StoreConfig(root=config.dwd_root))
        self.dws_store = DWSStore(StoreConfig(root=config.dws_root))
        
        # 初始化处理器
        self.dwd_processor = DWDProcessor(self.dwd_store)
        self.dws_processor = DWSProcessor(self.dws_store)
        
        # 初始化质量检查器
        self.quality_checker = DataQualityChecker()
    
    def process_bar_data(self, bar_data: List[BarData], source: str = "unknown") -> Dict[str, Any]:
        """
        处理K线数据 - 从原始数据到汇总数据的完整流程
        
        Args:
            bar_data: 原始K线数据列表
            source: 数据源标识
            
        Returns:
            处理结果统计
        """
        if not bar_data:
            return {"status": "empty", "count": 0}
        
        self.logger.info(f"开始处理K线数据: {len(bar_data)} 条记录")
        
        # 1. ODS层：保存原始数据
        ods_bars = []
        for bar in bar_data:
            ods_bar = create_ods_bar_from_bar_data(bar, source)
            ods_bars.append(ods_bar)
        
        ods_count = self.ods_store.save_bars(ods_bars)
        self.logger.info(f"ODS层保存完成: {ods_count} 条记录")
        
        # 2. DWD层：规整数据
        dwd_bars = []
        for ods_bar in ods_bars:
            dwd_bar = create_dwd_bar_from_ods_bar(ods_bar)
            if dwd_bar:
                dwd_bars.append(dwd_bar)
        
        dwd_count = self.dwd_store.save_bars(dwd_bars)
        self.logger.info(f"DWD层保存完成: {dwd_count} 条记录")
        
        # 3. DWS层：汇总数据
        # 计算复权价格
        dwd_df = pd.DataFrame([{
            'symbol': bar.symbol,
            'exchange': bar.exchange.value if hasattr(bar.exchange, 'value') else str(bar.exchange),
            'interval': bar.interval.value if hasattr(bar.interval, 'value') else str(bar.interval),
            'datetime': bar.datetime,
            'open': bar.open_price,
            'high': bar.high_price,
            'low': bar.low_price,
            'close': bar.close_price,
            'volume': bar.volume,
            'turnover': bar.turnover,
            'amount': bar.amount,
            'vwap': bar.vwap
        } for bar in dwd_bars])
        
        adjusted_data = self.dws_processor.calculate_adjusted_prices(dwd_df)
        adjusted_count = self.dws_store.save_adjusted_data(adjusted_data)
        self.logger.info(f"DWS层复权价格保存完成: {adjusted_count} 条记录")
        
        # 计算资金因子
        factor_data = self.dws_processor.calculate_money_flow_factors(dwd_df)
        factor_count = self.dws_store.save_factor_data(factor_data)
        self.logger.info(f"DWS层资金因子保存完成: {factor_count} 条记录")
        
        return {
            "status": "success",
            "ods_count": ods_count,
            "dwd_count": dwd_count,
            "adjusted_count": adjusted_count,
            "factor_count": factor_count,
            "total_count": len(bar_data)
        }
    
    def process_financial_data(self, financial_data: List[Dict[str, Any]], 
                             source: str = "unknown") -> Dict[str, Any]:
        """
        处理财务数据 - 从原始数据到汇总数据的完整流程
        
        Args:
            financial_data: 原始财务数据列表
            source: 数据源标识
            
        Returns:
            处理结果统计
        """
        if not financial_data:
            return {"status": "empty", "count": 0}
        
        self.logger.info(f"开始处理财务数据: {len(financial_data)} 条记录")
        
        # 1. ODS层：保存原始财务数据
        ods_financial = []
        for data in financial_data:
            ods_financial.append(ODSFinancialData(
                symbol=data['symbol'],
                exchange=Exchange(data['exchange']),
                report_date=pd.Timestamp(data['report_date']),
                report_type=data.get('report_type', '年报'),
                raw_income=data.get('income', {}),
                raw_balance=data.get('balance', {}),
                raw_cashflow=data.get('cashflow', {}),
                source=source,
                quality_score=1.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ))
        
        ods_count = self.ods_store.save_financial(ods_financial)
        self.logger.info(f"ODS层财务数据保存完成: {ods_count} 条记录")
        
        # 2. DWD层：规整财务数据
        dwd_financial = []
        for ods_fin in ods_financial:
            dwd_fin = DWDFinancialData(
                symbol=ods_fin.symbol,
                exchange=ods_fin.exchange,
                report_date=ods_fin.report_date,
                report_type=ods_fin.report_type,
                total_revenue=ods_fin.raw_income.get('total_revenue', 0.0),
                net_profit=ods_fin.raw_income.get('net_profit', 0.0),
                total_assets=ods_fin.raw_balance.get('total_assets', 0.0),
                total_liabilities=ods_fin.raw_balance.get('total_liabilities', 0.0),
                shareholders_equity=ods_fin.raw_balance.get('shareholders_equity', 0.0),
                revenue_growth=0.0,  # 需要计算
                profit_growth=0.0,   # 需要计算
                roe=0.0,            # 需要计算
                roa=0.0,            # 需要计算
                is_valid=True,
                quality_issues=[],
                processed_at=datetime.now()
            )
            dwd_financial.append(dwd_fin)
        
        dwd_count = self.dwd_store.save_financial(dwd_financial)
        self.logger.info(f"DWD层财务数据保存完成: {dwd_count} 条记录")
        
        # 3. DWS层：财务合并表
        dwd_financial_df = pd.DataFrame([{
            'symbol': fin.symbol,
            'exchange': fin.exchange.value if hasattr(fin.exchange, 'value') else str(fin.exchange),
            'report_date': fin.report_date,
            'revenue_growth': fin.revenue_growth,
            'profit_growth': fin.profit_growth,
            'roe': fin.roe,
            'roa': fin.roa
        } for fin in dwd_financial])
        
        merged_data = self.dws_processor.merge_financial_data(dwd_financial_df)
        merged_count = self.dws_store.save_merged_financial_data(merged_data)
        self.logger.info(f"DWS层财务合并表保存完成: {merged_count} 条记录")
        
        return {
            "status": "success",
            "ods_count": ods_count,
            "dwd_count": dwd_count,
            "merged_count": merged_count,
            "total_count": len(financial_data)
        }
    
    def batch_process_symbols(self, symbols: List[str], exchange: str, 
                            start_date: pd.Timestamp, end_date: pd.Timestamp) -> Dict[str, Any]:
        """
        批量处理多个股票的数据
        
        Args:
            symbols: 股票代码列表
            exchange: 交易所代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            批量处理结果统计
        """
        self.logger.info(f"开始批量处理 {len(symbols)} 个股票")
        
        results = {
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "symbol_results": {}
        }
        
        for symbol in symbols:
            try:
                # 这里需要从数据源获取数据，暂时跳过
                self.logger.info(f"处理股票 {symbol} - 跳过（需要数据源）")
                results["symbol_results"][symbol] = {"status": "skipped"}
                results["success_count"] += 1
                
            except Exception as e:
                self.logger.error(f"处理股票 {symbol} 失败: {e}")
                results["error_count"] += 1
                results["errors"].append({"symbol": symbol, "error": str(e)})
        
        return results
    
    def get_data_summary(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """
        获取数据汇总信息
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            
        Returns:
            数据汇总信息
        """
        summary = {
            "symbol": symbol,
            "exchange": exchange,
            "ods": {},
            "dwd": {},
            "dws": {}
        }
        
        try:
            # ODS层数据统计
            ods_bars = self.ods_store.load_bars(exchange, symbol, "1d")
            summary["ods"]["bars_count"] = len(ods_bars)
            summary["ods"]["bars_date_range"] = {
                "start": str(ods_bars['datetime'].min()) if not ods_bars.empty else None,
                "end": str(ods_bars['datetime'].max()) if not ods_bars.empty else None
            }
            
            ods_financial = self.ods_store.load_financial(exchange, symbol)
            summary["ods"]["financial_count"] = len(ods_financial)
            
            # DWD层数据统计
            dwd_bars = self.dwd_store.load_bars(exchange, symbol, "1d")
            summary["dwd"]["bars_count"] = len(dwd_bars)
            summary["dwd"]["bars_date_range"] = {
                "start": str(dwd_bars['datetime'].min()) if not dwd_bars.empty else None,
                "end": str(dwd_bars['datetime'].max()) if not dwd_bars.empty else None
            }
            
            dwd_financial = self.dwd_store.load_financial(exchange, symbol)
            summary["dwd"]["financial_count"] = len(dwd_financial)
            
            # DWS层数据统计
            adjusted_data = self.dws_store.load_adjusted_data(exchange, symbol, "1d")
            summary["dws"]["adjusted_count"] = len(adjusted_data)
            
            factor_data = self.dws_store.load_factor_data(exchange, symbol)
            summary["dws"]["factor_count"] = len(factor_data)
            
            merged_financial = self.dws_store.load_merged_financial_data(exchange, symbol)
            summary["dws"]["merged_financial_count"] = len(merged_financial)
            
        except Exception as e:
            self.logger.error(f"获取数据汇总失败: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def cleanup_old_data(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """
        清理过期数据
        
        Args:
            retention_days: 保留天数，如果为None则使用配置中的值
            
        Returns:
            清理结果统计
        """
        if retention_days is None:
            retention_days = min(
                self.config.ods_retention_days,
                self.config.dwd_retention_days,
                self.config.dws_retention_days
            )
        
        self.logger.info(f"开始清理 {retention_days} 天前的数据")
        
        # 这里需要实现具体的清理逻辑
        # 暂时返回占位结果
        return {
            "status": "not_implemented",
            "retention_days": retention_days,
            "message": "数据清理功能待实现"
        }


# ========== 便捷函数 ==========

def create_data_layers_pipeline(config: DataLayerConfig = None) -> DataLayersPipeline:
    """创建数据分层管道实例"""
    return DataLayersPipeline(config)


def process_bar_data_to_layers(bar_data: List[BarData], source: str = "unknown", 
                              config: DataLayerConfig = None) -> Dict[str, Any]:
    """便捷函数：将K线数据处理到各层"""
    pipeline = create_data_layers_pipeline(config)
    return pipeline.process_bar_data(bar_data, source)


def get_symbol_data_summary(exchange: str, symbol: str, 
                           config: DataLayerConfig = None) -> Dict[str, Any]:
    """便捷函数：获取股票数据汇总"""
    pipeline = create_data_layers_pipeline(config)
    return pipeline.get_data_summary(exchange, symbol)
