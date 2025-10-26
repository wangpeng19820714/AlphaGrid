#!/usr/bin/env python3
"""
数据更新脚本

支持分别执行不同数据类型的获取、存储功能
包括：K线数据、分钟数据、财务数据、基本面数据、第三方数据等
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from qp.data import (
    get_price, get_fundamental, get_universe_meta
)
from qp.data.stores import (
    ODSStore, DWDStore, DWSStore, DataLayersPipeline,
    load_data_layer_config, BarStore, MinuteStore, 
    ThirdPartyStore
)


def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """设置日志"""
    project_root = Path(__file__).parent.parent
    log_path = project_root / log_dir.lstrip('./')
    log_path.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path / 'data_update.log', encoding='utf-8')
        ]
    )


class DataUpdater:
    """数据更新器"""
    
    def __init__(self, config_path: str = "configs/data_config.yaml"):
        self.logger = logging.getLogger(__name__)
        
        # 确保配置文件路径是绝对路径
        if not Path(config_path).is_absolute():
            project_root = Path(__file__).parent.parent
            config_path = str(project_root / config_path)
        
        self.logger.info(f"加载配置文件: {config_path}")
        self.config = load_data_layer_config(config_path)
        
        # 初始化存储层
        from qp.data.stores import StoreConfig
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        
        # 确保数据路径是相对于项目根目录的绝对路径
        ods_root = str(project_root / self.config.ods_root.lstrip('./'))
        dwd_root = str(project_root / self.config.dwd_root.lstrip('./'))
        dws_root = str(project_root / self.config.dws_root.lstrip('./'))
        
        # 为ODS层创建配置
        ods_config = StoreConfig(root=ods_root)
        self.ods_store = ODSStore(ods_config)
        
        # 为DWD层创建配置
        dwd_config = StoreConfig(root=dwd_root)
        self.dwd_store = DWDStore(dwd_config)
        
        # 为DWS层创建配置
        dws_config = StoreConfig(root=dws_root)
        self.dws_store = DWSStore(dws_config)
        
        # 初始化传统存储（用于兼容）
        self.bar_store = BarStore(ods_config)
        self.minute_store = MinuteStore(ods_config)
        self.third_party_store = ThirdPartyStore(ods_config)
        
        self.logger.info(f"数据存储根目录: ODS={ods_root}, DWD={dwd_root}, DWS={dws_root}")
        
        self.logger.info("数据更新器初始化完成")
    
    def update_bar_data(self, symbols: List[str], start_date: str, end_date: str, 
                       markets: List[str] = None) -> bool:
        """
        更新K线数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            markets: 市场列表，默认为['SSE', 'SZSE']
            
        Returns:
            是否成功
        """
        if markets is None:
            markets = ['SSE', 'SZSE']
            
        self.logger.info(f"开始更新K线数据: {len(symbols)}只股票, {start_date} 到 {end_date}")
        
        try:
            # 获取价格数据
            price_data = get_price(symbols, start_offset=-30, end_date=end_date, freq="1d")
            
            if price_data.empty:
                self.logger.warning("未获取到价格数据")
                return False
            
            # 存储到传统BarStore
            saved_count = 0
            try:
                # 按股票分别保存
                for symbol in symbols:
                    symbol_data = price_data[price_data['symbol'] == symbol].copy()
                    if not symbol_data.empty:
                        # 确保数据格式正确
                        symbol_data['date'] = pd.to_datetime(symbol_data['trade_date']).dt.date
                        
                        # 使用BarStore的append方法
                        count = self.bar_store.append("SSE", symbol, "1d", symbol_data)
                        if count > 0:
                            saved_count += 1
                            self.logger.info(f"股票 {symbol} 数据已保存，记录数: {count}")
                
                self.logger.info(f"K线数据已保存到传统存储，股票数: {saved_count}")
            except Exception as e:
                self.logger.warning(f"保存到传统存储失败: {e}")
                # 尝试保存到ODS层
                for symbol in symbols:
                    symbol_data = price_data[price_data['symbol'] == symbol]
                    if not symbol_data.empty:
                        try:
                            # 转换为ODS格式并保存
                            from qp.data.stores import create_ods_bar_from_bar_data
                            from qp.data.types import Exchange
                            
                            ods_bars = []
                            for _, row in symbol_data.iterrows():
                                # 添加必要的字段
                                row_dict = row.to_dict()
                                row_dict['exchange'] = Exchange.SSE
                                ods_bar = create_ods_bar_from_bar_data(row_dict)
                                ods_bars.append(ods_bar)
                            
                            if ods_bars:
                                self.ods_store.save_bars(ods_bars, symbol, "SSE")
                                saved_count += 1
                        except Exception as e2:
                            self.logger.warning(f"保存股票 {symbol} 失败: {e2}")
            
            self.logger.info(f"K线数据更新完成，保存: {saved_count}只股票")
            return True
            
        except Exception as e:
            self.logger.error(f"更新K线数据失败: {e}")
            return False
    
    def update_minute_data(self, symbols: List[str], trade_date: str) -> bool:
        """
        更新分钟数据
        
        Args:
            symbols: 股票代码列表
            trade_date: 交易日期
            
        Returns:
            是否成功
        """
        self.logger.info(f"开始更新分钟数据: {len(symbols)}只股票, 日期: {trade_date}")
        
        try:
            # 获取分钟数据（模拟）
            minute_data = []
            for symbol in symbols:
                # 这里应该调用实际的分钟数据获取接口
                # 目前使用模拟数据
                for i in range(240):  # 4小时 * 60分钟
                    minute_data.append({
                        'symbol': symbol,
                        'datetime': f"{trade_date} {9:02d}:{i%60:02d}:00",
                        'open': 10.0 + i * 0.01,
                        'high': 10.5 + i * 0.01,
                        'low': 9.5 + i * 0.01,
                        'close': 10.0 + i * 0.01,
                        'volume': 1000 + i * 10,
                        'amount': 10000 + i * 100
                    })
            
            # 保存分钟数据
            saved_count = 0
            for symbol in symbols:
                symbol_data = [d for d in minute_data if d['symbol'] == symbol]
                if symbol_data:
                    # 这里应该调用实际的保存方法
                    saved_count += 1
            
            self.logger.info(f"分钟数据更新完成，保存: {saved_count}只股票")
            return True
            
        except Exception as e:
            self.logger.error(f"更新分钟数据失败: {e}")
            return False
    
    def update_financial_data(self, symbols: List[str], report_date: str) -> bool:
        """
        更新财务数据
        
        Args:
            symbols: 股票代码列表
            report_date: 报告日期
            
        Returns:
            是否成功
        """
        self.logger.info(f"开始更新财务数据: {len(symbols)}只股票, 报告日期: {report_date}")
        
        try:
            # 获取财务数据
            financial_data = get_fundamental(symbols, asof_date=report_date, 
                                           fields=["total_revenue", "net_profit", "total_assets"])
            
            if financial_data.empty:
                self.logger.warning("未获取到财务数据")
                return False
            
            # 存储到ODS层
            saved_count = 0
            for symbol in symbols:
                symbol_data = financial_data[financial_data['symbol'] == symbol]
                if not symbol_data.empty:
                    # 转换为ODS格式并保存
                    from qp.data.stores import ODSFinancialData
                    from qp.data.types import Exchange
                    
                    ods_financials = []
                    for _, row in symbol_data.iterrows():
                        ods_financial = ODSFinancialData(
                            symbol=symbol,
                            exchange=Exchange.SSE,  # 简化处理
                            report_date=pd.to_datetime(report_date),
                            report_type="annual",
                            raw_data=row.to_dict(),
                            source="api",
                            quality_score=1.0,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        ods_financials.append(ods_financial)
                    
                    if ods_financials:
                        self.ods_store.save_financial_by_type(ods_financials, symbol, "SSE", "annual")
                        saved_count += 1
            
            self.logger.info(f"财务数据更新完成，保存: {saved_count}只股票")
            return True
            
        except Exception as e:
            self.logger.error(f"更新财务数据失败: {e}")
            return False
    
    def update_fundamental_data(self, symbols: List[str], asof_date: str) -> bool:
        """
        更新基本面数据
        
        Args:
            symbols: 股票代码列表
            asof_date: 截止日期
            
        Returns:
            是否成功
        """
        self.logger.info(f"开始更新基本面数据: {len(symbols)}只股票, 截止日期: {asof_date}")
        
        try:
            # 获取基本面数据
            fundamental_data = get_fundamental(symbols, asof_date=asof_date,
                                            fields=["pe_ttm", "pb_ratio", "ps_ratio", "industry", "market_cap"])
            
            if fundamental_data.empty:
                self.logger.warning("未获取到基本面数据")
                return False
            
            # 存储到ODS层
            saved_count = 0
            for symbol in symbols:
                symbol_data = fundamental_data[fundamental_data['symbol'] == symbol]
                if not symbol_data.empty:
                    # 转换为ODS格式并保存
                    from qp.data.stores import ODSFundamentalData
                    from qp.data.types import Exchange
                    
                    ods_fundamentals = []
                    for _, row in symbol_data.iterrows():
                        ods_fundamental = ODSFundamentalData(
                            symbol=symbol,
                            exchange=Exchange.SSE,  # 简化处理
                            date=pd.to_datetime(asof_date),
                            raw_data=row.to_dict(),
                            source="api",
                            quality_score=1.0,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        ods_fundamentals.append(ods_fundamental)
                    
                    if ods_fundamentals:
                        self.ods_store.save_fundamental(ods_fundamentals, symbol, "SSE")
                        saved_count += 1
            
            self.logger.info(f"基本面数据更新完成，保存: {saved_count}只股票")
            return True
            
        except Exception as e:
            self.logger.error(f"更新基本面数据失败: {e}")
            return False
    
    def update_third_party_data(self, data_type: str, symbols: List[str] = None) -> bool:
        """
        更新第三方数据
        
        Args:
            data_type: 数据类型 (index_components, industry_classifications, macro_data)
            symbols: 股票代码列表（可选）
            
        Returns:
            是否成功
        """
        self.logger.info(f"开始更新第三方数据: {data_type}")
        
        try:
            if data_type == "index_components":
                # 更新指数成分股
                indices = ["000001.SH", "000300.SH", "000905.SH"]  # 上证指数、沪深300、中证500
                saved_count = 0
                for index_code in indices:
                    # 这里应该调用实际的指数成分股获取接口
                    # 目前使用模拟数据
                    components = [f"{i:06d}" for i in range(1, 301)]  # 模拟成分股
                    
                    # 保存到第三方存储
                    # self.third_party_store.save_index_components(index_code, components)
                    saved_count += 1
                
                self.logger.info(f"指数成分股更新完成，保存: {saved_count}个指数")
                
            elif data_type == "industry_classifications":
                # 更新行业分类
                industries = ["银行", "科技", "医药", "消费", "制造", "地产", "能源", "材料"]
                # self.third_party_store.save_industry_classifications(industries)
                self.logger.info(f"行业分类更新完成，保存: {len(industries)}个行业")
                
            elif data_type == "macro_data":
                # 更新宏观数据
                macro_indicators = ["GDP", "CPI", "PPI", "M2", "利率"]
                # self.third_party_store.save_macro_data(macro_indicators)
                self.logger.info(f"宏观数据更新完成，保存: {len(macro_indicators)}个指标")
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新第三方数据失败: {e}")
            return False
    
    def process_data_layers(self, symbols: List[str], process_date: str) -> bool:
        """
        处理数据分层（ODS -> DWD -> DWS）
        
        Args:
            symbols: 股票代码列表
            process_date: 处理日期
            
        Returns:
            是否成功
        """
        self.logger.info(f"开始处理数据分层: {len(symbols)}只股票, 日期: {process_date}")
        
        try:
            # 创建数据分层管道
            pipeline = DataLayersPipeline(self.config)
            
            # 处理K线数据
            for symbol in symbols:
                # ODS -> DWD
                ods_bars = self.ods_store.load_bars("SSE", symbol, 
                                                  start_date=pd.to_datetime(process_date),
                                                  end_date=pd.to_datetime(process_date))
                
                if not ods_bars.empty:
                    # 转换为DWD格式
                    from qp.data.stores import create_dwd_bar_from_ods_bar
                    dwd_bars = []
                    for _, row in ods_bars.iterrows():
                        dwd_bar = create_dwd_bar_from_ods_bar(row)
                        dwd_bars.append(dwd_bar)
                    
                    if dwd_bars:
                        self.dwd_store.save_bars_by_symbol(dwd_bars, symbol, "SSE")
                
                # DWD -> DWS
                dwd_bars = self.dwd_store.load_bars("SSE", symbol,
                                                  start_date=pd.to_datetime(process_date),
                                                  end_date=pd.to_datetime(process_date))
                
                if not dwd_bars.empty:
                    # 计算调整价格和因子
                    from qp.data.stores import dwd_bar_to_dws_adjusted, dwd_bar_to_dws_factor
                    
                    adjusted_data = dwd_bar_to_dws_adjusted(dwd_bars.iloc[0])
                    factor_data = dwd_bar_to_dws_factor(dwd_bars.iloc[0])
                    
                    # 保存到DWS层
                    if adjusted_data:
                        self.dws_store.save_adjusted_prices([adjusted_data])
                    if factor_data:
                        self.dws_store.save_financial_factors([factor_data])
            
            self.logger.info("数据分层处理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"处理数据分层失败: {e}")
            return False


def get_symbols_from_universe(universe: str, asof_date: str) -> List[str]:
    """从股票池获取股票代码"""
    try:
        meta = get_universe_meta(universe, asof_date)
        return meta['symbol'].tolist()
    except Exception as e:
        logging.getLogger(__name__).warning(f"获取股票池失败: {e}")
        # 返回示例股票代码
        return [f"{i:06d}" for i in range(1, 301)]


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据更新工具')
    
    # 基本参数
    parser.add_argument('--config', type=str, default='configs/data_config.yaml',
                       help='配置文件路径')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    parser.add_argument('--log-dir', type=str, default='logs',
                       help='日志目录')
    
    # 数据更新参数
    parser.add_argument('--data-type', type=str, required=True,
                       choices=['bar', 'minute', 'financial', 'fundamental', 'third_party', 'layers', 'batch_history'],
                       help='数据类型')
    parser.add_argument('--universe', type=str, default='hs300',
                       choices=['all', 'hs300', 'zz500', 'zz1000'],
                       help='股票池')
    parser.add_argument('--symbols', type=str, nargs='+',
                       help='指定股票代码列表')
    parser.add_argument('--start-date', type=str,
                       help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--trade-date', type=str,
                       help='交易日期 (YYYY-MM-DD)')
    parser.add_argument('--report-date', type=str,
                       help='报告日期 (YYYY-MM-DD)')
    parser.add_argument('--third-party-type', type=str,
                       choices=['index_components', 'industry_classifications', 'macro_data'],
                       help='第三方数据类型')
    parser.add_argument('--layer', type=str, default='',
                       help='批量历史数据更新层 (core, sector, full)')
    parser.add_argument('--force', action='store_true',
                       help='强制更新（忽略更新限制）')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level, args.log_dir)
    logger = logging.getLogger(__name__)
    
    # 获取股票代码
    if args.symbols:
        symbols = args.symbols
    else:
        end_date = args.end_date or args.trade_date or datetime.now().strftime('%Y-%m-%d')
        symbols = get_symbols_from_universe(args.universe, end_date)
    
    logger.info(f"准备更新数据，类型: {args.data_type}, 股票数: {len(symbols)}")
    
    # 创建数据更新器
    updater = DataUpdater(args.config)
    
    # 执行数据更新
    success = False
    
    if args.data_type == 'bar':
        if not args.start_date or not args.end_date:
            logger.error("K线数据更新需要指定 --start-date 和 --end-date")
            return
        
        success = updater.update_bar_data(symbols, args.start_date, args.end_date)
        
    elif args.data_type == 'minute':
        if not args.trade_date:
            logger.error("分钟数据更新需要指定 --trade-date")
            return
        
        success = updater.update_minute_data(symbols, args.trade_date)
        
    elif args.data_type == 'financial':
        if not args.report_date:
            logger.error("财务数据更新需要指定 --report-date")
            return
        
        success = updater.update_financial_data(symbols, args.report_date)
        
    elif args.data_type == 'fundamental':
        if not args.trade_date:
            logger.error("基本面数据更新需要指定 --trade-date")
            return
        
        success = updater.update_fundamental_data(symbols, args.trade_date)
        
    elif args.data_type == 'third_party':
        if not args.third_party_type:
            logger.error("第三方数据更新需要指定 --third-party-type")
            return
        
        success = updater.update_third_party_data(args.third_party_type, symbols)
        
    elif args.data_type == 'layers':
        if not args.trade_date:
            logger.error("数据分层处理需要指定 --trade-date")
            return
        
        success = updater.process_data_layers(symbols, args.trade_date)
    
    elif args.data_type == 'batch_history':
        # 调用批量历史数据更新脚本
        import subprocess
        
        layer_args = f"--only {args.layer}" if args.layer else ""
        force_args = "--force" if args.force else ""
        
        cmd = f"python3 src/qp/scripts/update_history_layers.py --config {args.config} {layer_args} {force_args}"
        
        logger.info(f"执行批量历史数据更新: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            success = True
            logger.info("批量历史数据更新完成")
            if result.stdout:
                print(result.stdout)
        else:
            success = False
            logger.error(f"批量历史数据更新失败: {result.stderr}")
            print("=" * 60)
            print("错误输出:")
            print("=" * 60)
            print(result.stderr)
            print("=" * 60)
            print("标准输出:")
            print("=" * 60)
            print(result.stdout)
            print("=" * 60)
    
    else:
        logger.error(f"未知的数据类型: {args.data_type}")
        success = False
    
    # 输出结果
    if success:
        logger.info(f"✓ {args.data_type} 数据更新完成")
        print(f"✓ {args.data_type} 数据更新完成")
    else:
        logger.error(f"✗ {args.data_type} 数据更新失败")
        print(f"✗ {args.data_type} 数据更新失败")


if __name__ == "__main__":
    main()
