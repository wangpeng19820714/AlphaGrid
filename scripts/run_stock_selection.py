#!/usr/bin/env python3
"""
量化选股主脚本

实现基于多因子的股票选择功能，包括因子计算、标准化、中性化和综合评分。
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, date
import logging
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qp.research.selector import StockSelector, SelectionConfig, run_stock_selection
from qp.research.data_interface import create_data_interface


def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """设置日志"""
    # 确保日志目录存在 - 使用项目根目录
    project_root = Path(__file__).parent.parent  # 从 scripts/ 回到项目根目录
    log_path = project_root / log_dir.lstrip('./')  # 移除 ./ 前缀
    log_path.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path / 'stock_selection.log', encoding='utf-8')
        ]
    )


def create_sample_data(symbols: list, trade_date: str, lookback_days: int = 150) -> tuple:
    """
    创建示例数据（用于测试）
    
    Args:
        symbols: 股票代码列表
        trade_date: 交易日期
        lookback_days: 回看天数
        
    Returns:
        (价格数据, 基本面数据)
    """
    logger = logging.getLogger(__name__)
    
    # 创建日期范围 - 增加更多天数确保有足够数据
    end_date = pd.to_datetime(trade_date)
    start_date = end_date - pd.Timedelta(days=lookback_days + 50)  # 额外增加50天
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 创建价格数据
    price_data = []
    for symbol in symbols:
        base_price = 10 + np.random.normal(0, 2)
        for i, trade_date in enumerate(dates):
            # 模拟价格走势
            price_change = np.random.normal(0, 0.02)
            base_price *= (1 + price_change)
            
            close = max(base_price, 0.1)  # 确保价格为正
            volume = np.random.randint(1000000, 10000000)
            amount = close * volume
            
            price_data.append({
                'symbol': symbol,
                'trade_date': trade_date,
                'close': close,
                'volume': volume,
                'amount': amount
            })
    
    price_df = pd.DataFrame(price_data)
    
    # 创建基本面数据 - 为每个日期创建基本面数据
    fundamental_data = []
    industries = ['银行', '科技', '医药', '消费', '制造', '地产', '能源', '材料', '公用事业', '金融']
    
    for symbol in symbols:
        pe_ttm = np.random.uniform(5, 50)
        industry = np.random.choice(industries)
        market_cap = np.random.uniform(1e8, 1e12)
        
        # 为每个日期创建基本面数据
        for date in dates:
            fundamental_data.append({
                'symbol': symbol,
                'trade_date': date,
                'pe_ttm': pe_ttm,
                'industry': industry,
                'market_cap': market_cap
            })
    
    fundamental_df = pd.DataFrame(fundamental_data)
    
    logger.info(f"创建示例数据完成，股票数: {len(symbols)}, 价格记录数: {len(price_df)}")
    return price_df, fundamental_df


def run_selection_with_sample_data(symbols: list, trade_date: str, config: SelectionConfig, output_dir: str = None) -> pd.DataFrame:
    """
    使用示例数据运行选股
    
    Args:
        symbols: 股票代码列表
        trade_date: 交易日期
        config: 选股配置
        
    Returns:
        选股结果DataFrame
    """
    logger = logging.getLogger(__name__)
    
    # 创建选择器
    selector = StockSelector(config)
    
    # 创建示例数据
    price_data, fundamental_data = create_sample_data(symbols, trade_date, config.lookback_days)
    
    # 合并数据
    merged_data = pd.merge(price_data, fundamental_data, on=['symbol', 'trade_date'], how='inner')
    
    # 筛选股票
    screened_data = merged_data.copy()
    screened_data = screened_data[screened_data['market_cap'] >= config.min_market_cap]
    screened_data = screened_data[screened_data['volume'] >= config.min_volume]
    screened_data = screened_data[(screened_data['pe_ttm'] > 0.1) & (screened_data['pe_ttm'] < 100)]
    
    if screened_data.empty:
        logger.warning("筛选后无股票数据")
        return pd.DataFrame()
    
    # 计算因子
    factor_data = selector.calculate_factors_from_merged(screened_data)
    
    if factor_data.empty:
        logger.warning("因子计算后无数据")
        return pd.DataFrame()
    
    # 计算综合得分
    results = selector.calculate_composite_score(factor_data)
    
    # 保存结果
    save_path = selector.save_results(results, trade_date, output_dir=output_dir)
    logger.info(f"选股结果已保存: {save_path}")
    
    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='量化选股工具')
    parser.add_argument('--trade-date', type=str, default='2024-01-15', 
                       help='交易日期 (YYYY-MM-DD)')
    parser.add_argument('--universe', type=str, default='hs300', 
                       choices=['all', 'hs300', 'zz500', 'zz1000'],
                       help='股票池类型')
    parser.add_argument('--top-n', type=int, default=50, 
                       help='选择前N只股票')
    parser.add_argument('--config', type=str, default=None,
                       help='配置文件路径')
    parser.add_argument('--output-dir', type=str, default='./reports/stock_selection',
                       help='输出目录')
    parser.add_argument('--model-name', type=str, default='multi_factor_model',
                       help='模型名称')
    parser.add_argument('--version', type=str, default='1.0.0',
                       help='模型版本')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    parser.add_argument('--log-dir', type=str, default='./logs',
                       help='日志文件目录')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level, args.log_dir)
    logger = logging.getLogger(__name__)
    
    # 创建输出目录 - 使用项目根目录
    project_root = Path(__file__).parent.parent  # 从 scripts/ 回到项目根目录
    output_path = project_root / args.output_dir.lstrip('./')  # 移除 ./ 前缀
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 加载配置
    if args.config and Path(args.config).exists():
        try:
            # 使用新的YAML配置加载方式
            from qp.research.pipeline import build_signals_from_cfg
            signals = build_signals_from_cfg(args.config)
            if not signals.empty:
                print(f"✓ 选股完成，选择股票数量: {len(signals)}")
                print(f"✓ 结果已保存到: data/dws/signals/")
                print("\n前10只股票:")
                print(signals.head(10)[['symbol', 'score', 'rank', 'weight']].to_string(index=False))
            else:
                print("✗ 选股失败，无结果")
            return
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return
    else:
        # 使用默认配置
        config = SelectionConfig(
            top_n=args.top_n,
            output_dir=args.output_dir,
            model_name=args.model_name,
            version=args.version
        )
        logger.info("使用默认配置")
    
    # 获取股票池
    try:
        data_interface = create_data_interface()
        symbols = data_interface.get_universe_symbols(args.universe)
        logger.info(f"获取股票池完成，类型: {args.universe}, 数量: {len(symbols)}")
    except Exception as e:
        logger.error(f"获取股票池失败: {e}")
        # 使用示例股票池
        symbols = [f"{i:06d}" for i in range(1, 301)]  # 000001-000300
        logger.info(f"使用示例股票池，数量: {len(symbols)}")
    
    # 运行选股
    try:
        logger.info(f"开始选股，交易日期: {args.trade_date}")
        
        # 使用示例数据运行选股
        results = run_selection_with_sample_data(symbols, args.trade_date, config, str(output_path))
        
        if not results.empty:
            logger.info(f"选股完成，选择股票数: {len(results)}")
            
            # 显示结果摘要
            print("\n" + "="*60)
            print("选股结果摘要")
            print("="*60)
            print(f"交易日期: {args.trade_date}")
            print(f"股票池: {args.universe} ({len(symbols)} 只)")
            print(f"选择股票数: {len(results)}")
            print(f"模型名称: {config.model_name}")
            print(f"模型版本: {config.version}")
            
            print(f"\n前10只股票:")
            print(results[['symbol', 'score', 'rank', 'momentum_120', 'volatility_20', 'pe_ttm']].head(10).to_string(index=False))
            
            print(f"\n因子统计:")
            print(f"  动量因子: 均值={results['momentum_120'].mean():.3f}, 标准差={results['momentum_120'].std():.3f}")
            print(f"  波动率因子: 均值={results['volatility_20'].mean():.3f}, 标准差={results['volatility_20'].std():.3f}")
            print(f"  估值因子: 均值={results['pe_ttm'].mean():.3f}, 标准差={results['pe_ttm'].std():.3f}")
            print(f"  综合得分: 均值={results['score'].mean():.3f}, 标准差={results['score'].std():.3f}")
            
        else:
            logger.warning("选股结果为空")
            
    except Exception as e:
        logger.error(f"选股过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
