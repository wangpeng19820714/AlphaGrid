"""
量化研究层 - 选股管道

实现选股流程的编排，包括数据获取、因子计算、选股和结果保存
符合 PIT (Point-in-Time) 正确性要求，无前瞻偏差
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import os

from .selector import select_daily, SelectionConfig
from .data_interface import get_price, get_fundamental, get_universe_meta
import yaml

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(cfg_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    Args:
        cfg_path: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"配置文件加载成功: {cfg_path}")
        return config
    except Exception as e:
        logger.error(f"配置文件加载失败: {e}")
        raise


def compute_factors(px: pd.DataFrame, f: Dict[str, Any]) -> pd.DataFrame:
    """
    计算因子数据
    
    Args:
        px: 价格数据
        f: 因子配置
        
    Returns:
        包含因子的DataFrame
    """
    logger.info("计算因子...")
    
    # 计算动量因子
    momentum_window = f.get("lookback_momentum", 120)
    volatility_window = f.get("lookback_volatility", 20)
    
    # 按股票分组计算因子
    factors = []
    for symbol, group in px.groupby("symbol"):
        if len(group) < momentum_window:
            continue
            
        # 按日期排序
        group = group.sort_values("trade_date")
        
        # 计算动量因子
        momentum = (group["close"].iloc[-1] / group["close"].iloc[-(momentum_window+1)]) - 1.0
        
        # 计算波动率因子
        volatility = group["close"].pct_change().tail(volatility_window).std()
        
        # 获取最新交易日期
        trade_date = group["trade_date"].iloc[-1]
        
        factors.append({
            "symbol": symbol,
            "trade_date": trade_date,
            "momentum_120": momentum,
            "volatility_20": volatility
        })
    
    factor_df = pd.DataFrame(factors)
    
    if not factor_df.empty:
        logger.info(f"因子计算完成，股票数: {len(factor_df)}")
    else:
        logger.warning("因子计算完成，但无有效数据")
    
    return factor_df


def build_signals_from_cfg(cfg_path: str = "configs/selection.yaml") -> pd.DataFrame:
    """
    从配置文件构建选股信号
    
    Args:
        cfg_path: 配置文件路径
        
    Returns:
        选股信号DataFrame
    """
    logger.info(f"从配置文件构建选股信号: {cfg_path}")
    
    try:
        # 加载配置
        cfg = load_config(cfg_path)
        s = cfg["selection"]
        f = cfg["factors"]
        rules = cfg["selection_rules"]
        w = cfg["weighting"]

        trade_date = s["trade_date"]
        universe = s["universe"]
        top_n = rules["top_n"]

        # 调用数据接口
        meta = get_universe_meta(universe=universe, asof_date=trade_date)
        symbols = meta.loc[meta["is_tradable"], "symbol"].tolist()
        px = get_price(symbols, start_offset=-f["lookback_momentum"]-10, end_date=trade_date, freq="1d", adjust="adj")

        # 计算因子
        df = compute_factors(px, f)   # 例如封装动量、波动率、PE
        
        # 获取基本面数据
        fin = get_fundamental(symbols, asof_date=trade_date, fields=["pe_ttm", "industry", "free_float_mkt_cap"])
        fin = fin.rename(columns={"free_float_mkt_cap": "mkt_cap"})
        
        # 为基本面数据添加trade_date列
        fin['trade_date'] = pd.to_datetime(trade_date)
        
        # 合并因子和基本面数据
        df = df.merge(fin, on=["symbol", "trade_date"], how="inner")
        
        if df.empty:
            logger.warning("合并因子和基本面数据后无有效数据")
            return pd.DataFrame()
        
        # 应用可交易股票掩码
        uni_mask = meta.set_index("symbol")["is_tradable"]
        
        # 执行选股
        sel = select_daily(df, uni_mask, top_n=top_n)

        if sel.empty:
            logger.warning("选股结果为空")
            return pd.DataFrame()

        sel.insert(0, "trade_date", trade_date)
        sel["model_name"] = s["strategy_name"]
        sel["version"] = s["model_version"]

        # 从配置中获取保存路径
        output_config = cfg.get("output", {})
        save_path = output_config.get("save_path", "data/dws/signals/")
        save_signals(sel, strategy=s["strategy_name"], save_path=save_path)
        logger.info(f"选股信号构建完成，选择股票数量: {len(sel)}")
        return sel
        
    except Exception as e:
        logger.error(f"从配置文件构建选股信号失败: {e}")
        return pd.DataFrame()


def build_signals(trade_date: str, universe: str = "CSI300", top_n: int = 50) -> pd.DataFrame:
    """
    构建选股信号
    
    Args:
        trade_date: 交易日期
        universe: 股票池名称，默认CSI300
        top_n: 选择前N只股票
        
    Returns:
        选股信号DataFrame，包含列: trade_date, symbol, score, rank, direction, weight, model_name, version
    """
    logger.info(f"开始构建选股信号，日期: {trade_date}, 股票池: {universe}, 选择数量: {top_n}")
    
    try:
        # 1) 获取股票池元数据
        logger.info("获取股票池元数据...")
        meta = get_universe_meta(universe=universe, asof_date=trade_date)
        
        if meta.empty:
            logger.warning(f"股票池 {universe} 在 {trade_date} 无数据")
            return pd.DataFrame()
        
        # 筛选可交易股票
        tradable_stocks = meta.loc[meta["is_tradable"], "symbol"].tolist()
        logger.info(f"可交易股票数量: {len(tradable_stocks)}")
        
        if not tradable_stocks:
            logger.warning("没有可交易的股票")
            return pd.DataFrame()
        
        # 2) 获取价格数据用于因子计算
        logger.info("获取价格数据...")
        px = get_price(symbols=tradable_stocks, start_offset=-130, end_date=trade_date, freq="1d", adjust="adj")
        
        if px.empty:
            logger.warning("价格数据为空")
            return pd.DataFrame()
        
        # 确保有足够的历史数据
        last_px = px.groupby("symbol").tail(120).reset_index(drop=True)
        
        # 计算技术因子
        logger.info("计算技术因子...")
        feat = last_px.groupby("symbol").apply(lambda g: pd.Series({
            "momentum_120": (g["close"].iloc[-1] / g["close"].iloc[0]) - 1.0 if len(g) >= 120 else np.nan,
            "volatility_20": g["close"].pct_change().tail(20).std() if len(g) >= 20 else np.nan,
        })).reset_index()
        
        # 去除无效数据
        feat = feat.dropna()
        
        if feat.empty:
            logger.warning("技术因子计算后无有效数据")
            return pd.DataFrame()
        
        # 3) 获取基本面数据
        logger.info("获取基本面数据...")
        fin = get_fundamental(symbols=tradable_stocks, asof_date=trade_date, 
                             fields=["pe_ttm", "industry", "free_float_mkt_cap"])
        
        if fin.empty:
            logger.warning("基本面数据为空")
            return pd.DataFrame()
        
        # 重命名列以保持一致性
        fin = fin.rename(columns={"free_float_mkt_cap": "mkt_cap"})
        
        # 4) 合并数据
        logger.info("合并因子数据...")
        df = feat.merge(fin, on="symbol", how="inner")
        
        if df.empty:
            logger.warning("合并后无有效数据")
            return pd.DataFrame()
        
        # 去除缺失值
        df = df.dropna()
        
        if df.empty:
            logger.warning("去除缺失值后无有效数据")
            return pd.DataFrame()
        
        # 5) 应用可交易股票掩码
        uni_mask = meta.set_index("symbol")["is_tradable"]
        
        # 6) 执行选股
        logger.info("执行选股...")
        sel = select_daily(df, uni_mask, top_n=top_n)
        
        if sel.empty:
            logger.warning("选股结果为空")
            return pd.DataFrame()
        
        # 7) 添加交易日期和模型信息
        sel.insert(0, "trade_date", trade_date)
        sel["model_name"] = "rank_topn_neutral"
        sel["version"] = "v1.0"
        
        logger.info(f"选股信号构建完成，选择股票数量: {len(sel)}")
        return sel
        
    except Exception as e:
        logger.error(f"构建选股信号失败: {e}")
        return pd.DataFrame()


def save_signals(df: pd.DataFrame, strategy: str, save_path: str = "data/dws/signals/") -> str:
    """
    保存选股信号到Parquet文件
    
    Args:
        df: 选股信号DataFrame
        strategy: 策略名称
        save_path: 保存路径前缀
        
    Returns:
        保存的文件路径
    """
    if df.empty:
        logger.warning("选股信号为空，无法保存")
        return ""
    
    try:
        # 获取交易日期
        trade_date = df['trade_date'].iloc[0]
        
        # 构建保存路径
        path = f"{save_path.rstrip('/')}/{strategy}/dt={trade_date}.parquet"
        
        # 创建目录
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # 保存为Parquet文件
        df.to_parquet(path, index=False)
        
        logger.info(f"选股信号已保存: {path}")
        return path
        
    except Exception as e:
        logger.error(f"保存选股信号失败: {e}")
        return ""


def run_daily_selection(trade_date: str, universe: str = "CSI300", 
                       top_n: int = 50, strategy: str = "rank_topn_neutral") -> tuple:
    """
    运行日度选股流程
    
    Args:
        trade_date: 交易日期
        universe: 股票池名称
        top_n: 选择前N只股票
        strategy: 策略名称
        
    Returns:
        (选股信号DataFrame, 保存路径)
    """
    logger.info(f"开始日度选股流程，日期: {trade_date}")
    
    # 构建信号
    signals = build_signals(trade_date=trade_date, universe=universe, top_n=top_n)
    
    if signals.empty:
        logger.warning("选股信号为空")
        return signals, ""
    
    # 保存信号
    save_path = save_signals(signals, strategy)
    
    return signals, save_path


def validate_signals(df: pd.DataFrame) -> bool:
    """
    验证选股信号的格式和内容
    
    Args:
        df: 选股信号DataFrame
        
    Returns:
        验证是否通过
    """
    if df.empty:
        logger.warning("选股信号为空")
        return False
    
    # 检查必需的列
    required_cols = ['trade_date', 'symbol', 'score', 'rank', 'direction', 'weight', 'model_name', 'version']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"选股信号缺少必需列: {missing_cols}")
        return False
    
    # 检查数据类型
    if not pd.api.types.is_datetime64_any_dtype(df['trade_date']):
        logger.warning("trade_date列不是日期类型")
    
    if not pd.api.types.is_numeric_dtype(df['score']):
        logger.warning("score列不是数值类型")
    
    if not pd.api.types.is_numeric_dtype(df['rank']):
        logger.warning("rank列不是数值类型")
    
    if not pd.api.types.is_numeric_dtype(df['weight']):
        logger.warning("weight列不是数值类型")
    
    # 检查权重和
    weight_sum = df['weight'].sum()
    if abs(weight_sum - 1.0) > 0.01:
        logger.warning(f"权重和不为1: {weight_sum}")
    
    # 检查排名
    if not df['rank'].is_monotonic_increasing:
        logger.warning("排名不是单调递增")
    
    logger.info("选股信号验证通过")
    return True


def get_signal_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    获取选股信号摘要信息
    
    Args:
        df: 选股信号DataFrame
        
    Returns:
        摘要信息字典
    """
    if df.empty:
        return {}
    
    summary = {
        'trade_date': df['trade_date'].iloc[0],
        'total_stocks': len(df),
        'model_name': df['model_name'].iloc[0],
        'version': df['version'].iloc[0],
        'score_stats': {
            'mean': df['score'].mean(),
            'std': df['score'].std(),
            'min': df['score'].min(),
            'max': df['score'].max()
        },
        'weight_stats': {
            'sum': df['weight'].sum(),
            'mean': df['weight'].mean(),
            'max': df['weight'].max(),
            'min': df['weight'].min()
        },
        'top_5_stocks': df.head(5)[['symbol', 'score', 'rank', 'weight']].to_dict('records')
    }
    
    return summary


# 示例用法
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行选股
    trade_date = "2024-01-15"
    signals, save_path = run_daily_selection(
        trade_date=trade_date, 
        universe="CSI300", 
        top_n=50, 
        strategy="rank_topn_neutral"
    )
    
    if not signals.empty:
        print(f"选股完成，结果保存至: {save_path}")
        print(f"选择股票数量: {len(signals)}")
        print("\n前10只股票:")
        print(signals.head(10))
        
        # 验证信号
        if validate_signals(signals):
            print("\n信号验证通过")
        
        # 获取摘要
        summary = get_signal_summary(signals)
        print(f"\n信号摘要:")
        print(f"交易日期: {summary['trade_date']}")
        print(f"选择股票数: {summary['total_stocks']}")
        print(f"模型名称: {summary['model_name']}")
        print(f"版本: {summary['version']}")
        print(f"得分统计: {summary['score_stats']}")
        print(f"权重统计: {summary['weight_stats']}")
    else:
        print("选股失败，无结果")
