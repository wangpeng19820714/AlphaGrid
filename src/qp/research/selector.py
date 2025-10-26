"""
量化研究层 - 选股模块

实现多因子选股策略，包括因子计算、标准化、中性化和综合评分
符合 PIT (Point-in-Time) 正确性要求，无前瞻偏差
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import logging
from pathlib import Path
import warnings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入sklearn，如果失败则使用简单实现
try:
    from sklearn.linear_model import LinearRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("sklearn未安装，将使用简化的中性化方法")


@dataclass
class SelectionConfig:
    """选股配置"""
    # 因子配置
    momentum_window: int = 120  # 动量因子窗口
    volatility_window: int = 20  # 波动率因子窗口
    
    # 标准化配置
    winsorize_limits: Tuple[float, float] = (0.01, 0.99)  # Winsorize限制 (1%/99%)
    zscore_threshold: float = 3.0  # Z-score阈值
    
    # 中性化配置
    neutralize_industry: bool = True  # 是否进行行业中性化
    neutralize_market_cap: bool = True  # 是否进行市值中性化
    
    # 选股配置
    top_n: int = 50  # 选择前N只股票
    lookback_days: int = 150  # 回看天数
    min_market_cap: float = 1e8  # 最小市值（1亿）
    min_volume: float = 1e6  # 最小成交量（100万）
    
    # 权重配置
    softmax_tau: float = 0.15  # Softmax温度参数
    cap_per_name: float = 0.05  # 单只股票最大权重
    
    # 输出配置
    output_dir: str = "data/dws/signals"
    model_name: str = "rank_topn_neutral"
    version: str = "v1.0"


def winsorize(s: pd.Series, p: float = 0.01) -> pd.Series:
    """
    对序列进行Winsorize处理
    
    Args:
        s: 输入序列
        p: 截尾比例，默认1%
        
    Returns:
        Winsorize后的序列
    """
    lower_bound = s.quantile(p)
    upper_bound = s.quantile(1 - p)
    return s.clip(lower=lower_bound, upper=upper_bound)


def zscore(s: pd.Series) -> pd.Series:
    """
    对序列进行Z-score标准化
    
    Args:
        s: 输入序列
        
    Returns:
        Z-score标准化后的序列
    """
    return (s - s.mean()) / s.std()


def neutralize(series: pd.Series, industry: pd.Series, cap: Optional[pd.Series] = None) -> pd.Series:
    """
    对因子进行行业和市值中性化
    
    Args:
        series: 待中性化的因子序列
        industry: 行业分类序列
        cap: 市值序列（可选）
        
    Returns:
        中性化后的因子序列
    """
    if not HAS_SKLEARN:
        # 简化的中性化方法
        logger.warning("使用简化的中性化方法（sklearn未安装）")
        return series - series.mean()
    
    try:
        # 准备特征矩阵
        features = []
        
        # 行业虚拟变量
        industry_dummies = pd.get_dummies(industry, prefix='industry')
        features.append(industry_dummies)
        
        # 对数市值
        if cap is not None:
            log_cap = np.log(cap + 1e-8)
            features.append(log_cap.to_frame('log_cap'))
        
        # 合并特征
        if features:
            X = pd.concat(features, axis=1)
            X = X.fillna(0)  # 填充缺失值
            
            # 添加截距项
            X['intercept'] = 1
            
            # OLS回归
            model = LinearRegression(fit_intercept=False)  # 手动添加了截距
            model.fit(X, series)
            
            # 计算残差
            predicted = model.predict(X)
            residuals = series - predicted
            
            return pd.Series(residuals, index=series.index)
        else:
            return series
            
    except Exception as e:
        logger.warning(f"中性化失败，使用原始序列: {e}")
        return series


def softmax_weight(score: pd.Series, tau: float = 0.15, cap_per_name: float = 0.05) -> pd.Series:
    """
    使用Softmax计算权重，带单只股票权重上限
    
    Args:
        score: 得分序列
        tau: 温度参数
        cap_per_name: 单只股票最大权重
        
    Returns:
        权重序列
    """
    # Softmax计算
    exp_scores = np.exp(score / tau)
    weights = exp_scores / exp_scores.sum()
    
    # 应用权重上限
    weights = weights.clip(upper=cap_per_name)
    
    # 重新归一化
    weights = weights / weights.sum()
    
    return weights


def select_daily(df_factors: pd.DataFrame, universe_mask: pd.Series, top_n: int = 50) -> pd.DataFrame:
    """
    执行日度选股
    
    Args:
        df_factors: 因子数据，必须包含列: symbol, momentum_120, volatility_20, pe_ttm, industry, mkt_cap
        universe_mask: 可交易股票掩码
        top_n: 选择前N只股票
        
    Returns:
        选股结果DataFrame，包含列: symbol, score, rank, direction, weight, model_name, version
    """
    # 验证必需的列
    required_cols = ['symbol', 'momentum_120', 'volatility_20', 'pe_ttm', 'industry', 'mkt_cap']
    missing_cols = [col for col in required_cols if col not in df_factors.columns]
    if missing_cols:
        raise ValueError(f"因子数据缺少必需列: {missing_cols}")
    
    # 应用可交易股票掩码
    df_filtered = df_factors[df_factors['symbol'].isin(universe_mask[universe_mask].index)].copy()
    
    if df_filtered.empty:
        logger.warning("没有可交易的股票")
        return pd.DataFrame()
    
    # 计算因子得分
    # 动量因子（正收益）
    momentum_score = df_filtered['momentum_120']
    
    # 波动率因子（低波动率更好，取负值）
    volatility_score = -df_filtered['volatility_20']
    
    # 估值因子（低PE更好，取负值）
    valuation_score = -df_filtered['pe_ttm']
    
    # 标准化处理
    momentum_norm = zscore(winsorize(momentum_score))
    volatility_norm = zscore(winsorize(volatility_score))
    valuation_norm = zscore(winsorize(valuation_score))
    
    # 中性化处理
    momentum_neutral = neutralize(momentum_norm, df_filtered['industry'], df_filtered['mkt_cap'])
    volatility_neutral = neutralize(volatility_norm, df_filtered['industry'], df_filtered['mkt_cap'])
    valuation_neutral = neutralize(valuation_norm, df_filtered['industry'], df_filtered['mkt_cap'])
    
    # 计算综合得分（等权重平均）
    composite_score = (momentum_neutral + volatility_neutral + valuation_neutral) / 3
    
    # 创建结果DataFrame
    result = df_filtered[['symbol']].copy()
    result['score'] = composite_score
    
    # 按得分排序
    result = result.sort_values('score', ascending=False)
    
    # 选择前N只股票
    result = result.head(top_n).copy()
    
    # 添加排名
    result['rank'] = range(1, len(result) + 1)
    
    # 添加方向（做多）
    result['direction'] = 1
    
    # 计算权重
    result['weight'] = softmax_weight(result['score'])
    
    # 添加模型信息
    result['model_name'] = "rank_topn_neutral"
    result['version'] = "v1.0"
    
    logger.info(f"选股完成，选择前 {len(result)} 只股票")
    return result


class FactorCalculator:
    """因子计算器"""
    
    def __init__(self, config: SelectionConfig):
        """
        初始化因子计算器
        
        Args:
            config: 选股配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_momentum_factor(self, price_data: pd.DataFrame) -> pd.Series:
        """
        计算动量因子（120日收益率）
        
        Args:
            price_data: 价格数据，包含close列
            
        Returns:
            动量因子Series
        """
        if 'close' not in price_data.columns:
            raise ValueError("价格数据必须包含close列")
        
        # 计算120日收益率
        momentum = price_data['close'].pct_change(periods=self.config.momentum_window)
        
        self.logger.info(f"计算动量因子完成，窗口期: {self.config.momentum_window}天")
        return momentum
    
    def calculate_volatility_factor(self, price_data: pd.DataFrame) -> pd.Series:
        """
        计算波动率因子（20日滚动波动率）
        
        Args:
            price_data: 价格数据，包含close列
            
        Returns:
            波动率因子Series
        """
        if 'close' not in price_data.columns:
            raise ValueError("价格数据必须包含close列")
        
        # 计算20日滚动波动率
        returns = price_data['close'].pct_change()
        volatility = returns.rolling(window=self.config.volatility_window).std()
        
        self.logger.info(f"计算波动率因子完成，窗口期: {self.config.volatility_window}天")
        return volatility
    
    def calculate_valuation_factor(self, fundamental_data: pd.DataFrame) -> pd.Series:
        """
        计算估值因子（PE倒数）
        
        Args:
            fundamental_data: 基本面数据，包含pe_ttm列
            
        Returns:
            估值因子Series
        """
        if 'pe_ttm' not in fundamental_data.columns:
            raise ValueError("基本面数据必须包含pe_ttm列")
        
        # 计算PE倒数（避免除零）
        pe_inverse = 1.0 / (fundamental_data['pe_ttm'] + 1e-8)
        
        self.logger.info("计算估值因子完成")
        return pe_inverse
    
    def winsorize_factor(self, factor: pd.Series) -> pd.Series:
        """
        对因子进行Winsorize处理
        
        Args:
            factor: 原始因子
            
        Returns:
            Winsorize后的因子
        """
        return winsorize(factor, self.config.winsorize_limits[0])
    
    def zscore_normalize(self, factor: pd.Series) -> pd.Series:
        """
        对因子进行Z-score标准化
        
        Args:
            factor: 原始因子
            
        Returns:
            Z-score标准化后的因子
        """
        return zscore(factor)
    
    def neutralize_factor(self, factor: pd.Series, 
                         industry: pd.Series, 
                         market_cap: pd.Series) -> pd.Series:
        """
        对因子进行行业和市值中性化
        
        Args:
            factor: 原始因子
            industry: 行业分类
            market_cap: 市值
            
        Returns:
            中性化后的因子
        """
        return neutralize(factor, industry, market_cap)


class StockScreener:
    """股票筛选器"""
    
    def __init__(self, config: SelectionConfig):
        """
        初始化股票筛选器
        
        Args:
            config: 选股配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def screen_stocks(self, price_data: pd.DataFrame, 
                     fundamental_data: pd.DataFrame) -> pd.DataFrame:
        """
        筛选符合条件的股票
        
        Args:
            price_data: 价格数据
            fundamental_data: 基本面数据
            
        Returns:
            筛选后的股票数据
        """
        # 合并数据
        merged_data = pd.merge(price_data, fundamental_data, 
                              on=['symbol', 'trade_date'], how='inner')
        
        # 基本筛选条件
        filtered_data = merged_data.copy()
        
        # 市值筛选
        if 'market_cap' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['market_cap'] >= self.config.min_market_cap
            ]
        
        # 成交量筛选
        if 'volume' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['volume'] >= self.config.min_volume
            ]
        
        # PE筛选（去除异常值）
        if 'pe_ttm' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['pe_ttm'] > 0) & 
                (filtered_data['pe_ttm'] < 100)
            ]
        
        self.logger.info(f"股票筛选完成，筛选前: {len(merged_data)} 只，筛选后: {len(filtered_data)} 只")
        return filtered_data


class StockSelector:
    """股票选择器"""
    
    def __init__(self, config: SelectionConfig):
        """
        初始化股票选择器
        
        Args:
            config: 选股配置
        """
        self.config = config
        self.factor_calculator = FactorCalculator(config)
        self.stock_screener = StockScreener(config)
        self.logger = logging.getLogger(__name__)
    
    def get_price_data(self, symbols: List[str], 
                      start_date: str, 
                      end_date: str) -> pd.DataFrame:
        """
        获取价格数据（模拟API）
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            价格数据DataFrame
        """
        # 模拟价格数据API
        # 实际使用时替换为真实的数据获取逻辑
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = []
        for symbol in symbols:
            for trade_date in dates:
                # 模拟数据
                close = 10 + np.random.normal(0, 2)
                volume = np.random.randint(1000000, 10000000)
                amount = close * volume
                
                data.append({
                    'symbol': symbol,
                    'trade_date': trade_date,
                    'close': close,
                    'volume': volume,
                    'amount': amount
                })
        
        df = pd.DataFrame(data)
        self.logger.info(f"获取价格数据完成，股票数: {len(symbols)}, 日期范围: {start_date} 到 {end_date}")
        return df
    
    def get_fundamental_data(self, symbols: List[str], 
                           trade_date: str) -> pd.DataFrame:
        """
        获取基本面数据（模拟API）
        
        Args:
            symbols: 股票代码列表
            trade_date: 交易日期
            
        Returns:
            基本面数据DataFrame
        """
        # 模拟基本面数据API
        # 实际使用时替换为真实的数据获取逻辑
        data = []
        for symbol in symbols:
            pe_ttm = np.random.uniform(5, 50)
            industry = np.random.choice(['银行', '科技', '医药', '消费', '制造'])
            market_cap = np.random.uniform(1e8, 1e12)
            
            data.append({
                'symbol': symbol,
                'trade_date': pd.to_datetime(trade_date),
                'pe_ttm': pe_ttm,
                'industry': industry,
                'market_cap': market_cap
            })
        
        df = pd.DataFrame(data)
        self.logger.info(f"获取基本面数据完成，股票数: {len(symbols)}, 日期: {trade_date}")
        return df
    
    def calculate_factors_from_merged(self, merged_data: pd.DataFrame) -> pd.DataFrame:
        """
        从已合并的数据计算因子
        
        Args:
            merged_data: 已合并的价格和基本面数据
            
        Returns:
            包含所有因子的DataFrame
        """
        # 按股票分组计算因子
        factor_data = []
        
        for symbol, group in merged_data.groupby('symbol'):
            if len(group) < self.config.momentum_window:
                self.logger.warning(f"股票 {symbol} 数据不足，跳过")
                continue  # 跳过数据不足的股票
            
            # 按日期排序
            group = group.sort_values('trade_date')
            
            # 计算原始因子
            momentum = self.factor_calculator.calculate_momentum_factor(group)
            volatility = self.factor_calculator.calculate_volatility_factor(group)
            
            # 检查基本面数据
            if 'pe_ttm' not in group.columns:
                self.logger.warning(f"股票 {symbol} 缺少pe_ttm数据，跳过")
                continue
            
            valuation = self.factor_calculator.calculate_valuation_factor(group)
            
            # 标准化处理
            momentum_norm = self.factor_calculator.zscore_normalize(
                self.factor_calculator.winsorize_factor(momentum)
            )
            volatility_norm = self.factor_calculator.zscore_normalize(
                self.factor_calculator.winsorize_factor(volatility)
            )
            valuation_norm = self.factor_calculator.zscore_normalize(
                self.factor_calculator.winsorize_factor(valuation)
            )
            
            # 中性化处理
            industry = group['industry'].iloc[0] if 'industry' in group.columns else 'Unknown'
            market_cap = group['market_cap'].iloc[0] if 'market_cap' in group.columns else 1e9
            
            # 只取最后一个日期的因子值
            last_idx = len(group) - 1
            if last_idx >= 0:
                momentum_neutral = self.factor_calculator.neutralize_factor(
                    pd.Series([momentum_norm.iloc[last_idx]]), 
                    pd.Series([industry]), 
                    pd.Series([market_cap])
                ).iloc[0]
                
                volatility_neutral = self.factor_calculator.neutralize_factor(
                    pd.Series([volatility_norm.iloc[last_idx]]), 
                    pd.Series([industry]), 
                    pd.Series([market_cap])
                ).iloc[0]
                
                valuation_neutral = self.factor_calculator.neutralize_factor(
                    pd.Series([valuation_norm.iloc[last_idx]]), 
                    pd.Series([industry]), 
                    pd.Series([market_cap])
                ).iloc[0]
                
                factor_data.append({
                    'symbol': symbol,
                    'trade_date': group['trade_date'].iloc[last_idx],
                    'momentum_120': momentum_neutral,
                    'volatility_20': volatility_neutral,
                    'pe_ttm': group['pe_ttm'].iloc[last_idx],
                    'industry': industry,
                    'mkt_cap': market_cap
                })
        
        factor_df = pd.DataFrame(factor_data)
        if not factor_df.empty:
            self.logger.info(f"因子计算完成，股票数: {len(factor_df['symbol'].unique())}")
        else:
            self.logger.warning("因子计算完成，但无有效数据")
        return factor_df
    
    def calculate_factors(self, price_data: pd.DataFrame, 
                        fundamental_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有因子
        
        Args:
            price_data: 价格数据
            fundamental_data: 基本面数据
            
        Returns:
            包含所有因子的DataFrame
        """
        # 合并数据
        merged_data = pd.merge(price_data, fundamental_data, 
                              on=['symbol', 'trade_date'], how='inner')
        
        # 按股票分组计算因子
        factor_data = []
        
        for symbol, group in merged_data.groupby('symbol'):
            if len(group) < self.config.momentum_window:
                self.logger.warning(f"股票 {symbol} 数据不足，跳过")
                continue  # 跳过数据不足的股票
            
            # 按日期排序
            group = group.sort_values('trade_date')
            
            # 计算原始因子
            momentum = self.factor_calculator.calculate_momentum_factor(group)
            volatility = self.factor_calculator.calculate_volatility_factor(group)
            
            # 检查基本面数据
            if 'pe_ttm' not in group.columns:
                self.logger.warning(f"股票 {symbol} 缺少pe_ttm数据，跳过")
                continue
            
            valuation = self.factor_calculator.calculate_valuation_factor(group)
            
            # 标准化处理
            momentum_norm = self.factor_calculator.zscore_normalize(
                self.factor_calculator.winsorize_factor(momentum)
            )
            volatility_norm = self.factor_calculator.zscore_normalize(
                self.factor_calculator.winsorize_factor(volatility)
            )
            valuation_norm = self.factor_calculator.zscore_normalize(
                self.factor_calculator.winsorize_factor(valuation)
            )
            
            # 中性化处理
            industry = group['industry'].iloc[0] if 'industry' in group.columns else 'Unknown'
            market_cap = group['market_cap'].iloc[0] if 'market_cap' in group.columns else 1e9
            
            # 只取最后一个日期的因子值
            last_idx = len(group) - 1
            if last_idx >= 0:
                momentum_neutral = self.factor_calculator.neutralize_factor(
                    pd.Series([momentum_norm.iloc[last_idx]]), 
                    pd.Series([industry]), 
                    pd.Series([market_cap])
                ).iloc[0]
                
                volatility_neutral = self.factor_calculator.neutralize_factor(
                    pd.Series([volatility_norm.iloc[last_idx]]), 
                    pd.Series([industry]), 
                    pd.Series([market_cap])
                ).iloc[0]
                
                valuation_neutral = self.factor_calculator.neutralize_factor(
                    pd.Series([valuation_norm.iloc[last_idx]]), 
                    pd.Series([industry]), 
                    pd.Series([market_cap])
                ).iloc[0]
                
                factor_data.append({
                    'symbol': symbol,
                    'trade_date': group['trade_date'].iloc[last_idx],
                    'momentum_120': momentum_neutral,
                    'volatility_20': volatility_neutral,
                    'pe_ttm': group['pe_ttm'].iloc[last_idx],
                    'industry': industry,
                    'mkt_cap': market_cap
                })
        
        factor_df = pd.DataFrame(factor_data)
        if not factor_df.empty:
            self.logger.info(f"因子计算完成，股票数: {len(factor_df['symbol'].unique())}")
        else:
            self.logger.warning("因子计算完成，但无有效数据")
        return factor_df
    
    def calculate_composite_score(self, factor_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算综合得分
        
        Args:
            factor_data: 因子数据
            
        Returns:
            包含综合得分的DataFrame
        """
        # 因子权重（可配置）
        weights = {
            'momentum_120': 0.4,
            'volatility_20': -0.3,  # 负权重，低波动率更好
            'pe_ttm': -0.3  # 负权重，低PE更好
        }
        
        # 计算综合得分
        factor_data['score'] = (
            factor_data['momentum_120'] * weights['momentum_120'] +
            factor_data['volatility_20'] * weights['volatility_20'] +
            factor_data['pe_ttm'] * weights['pe_ttm']
        )
        
        # 按得分排序
        factor_data = factor_data.sort_values('score', ascending=False)
        
        # 添加排名
        factor_data['rank'] = range(1, len(factor_data) + 1)
        
        # 选择前N只股票
        top_stocks = factor_data.head(self.config.top_n).copy()
        
        # 添加其他字段
        top_stocks['direction'] = 'long'  # 做多方向
        top_stocks['weight'] = 1.0 / len(top_stocks)  # 等权重
        top_stocks['model_name'] = self.config.model_name
        top_stocks['version'] = self.config.version
        
        self.logger.info(f"综合得分计算完成，选择前 {self.config.top_n} 只股票")
        return top_stocks
    
    def select_stocks(self, symbols: List[str], 
                     trade_date: str,
                     lookback_days: int = 150) -> pd.DataFrame:
        """
        执行股票选择
        
        Args:
            symbols: 股票代码列表
            trade_date: 交易日期
            lookback_days: 回看天数
            
        Returns:
            选股结果DataFrame
        """
        # 计算开始日期
        start_date = (pd.to_datetime(trade_date) - pd.Timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        # 获取数据
        price_data = self.get_price_data(symbols, start_date, trade_date)
        fundamental_data = self.get_fundamental_data(symbols, trade_date)
        
        # 筛选股票
        screened_data = self.stock_screener.screen_stocks(price_data, fundamental_data)
        
        # 计算因子
        factor_data = self.calculate_factors(screened_data, fundamental_data)
        
        # 计算综合得分
        result = self.calculate_composite_score(factor_data)
        
        self.logger.info(f"股票选择完成，选择日期: {trade_date}")
        return result
    
    def save_results(self, results: pd.DataFrame, trade_date: str, output_dir: str = None) -> str:
        """
        保存选股结果
        
        Args:
            results: 选股结果
            trade_date: 交易日期
            output_dir: 自定义输出目录，如果为None则使用配置中的目录
            
        Returns:
            保存路径
        """
        # 创建输出目录
        if output_dir is None:
            output_dir = Path(self.config.output_dir)
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        filename = f"stock_selection_{trade_date.replace('-', '')}.parquet"
        filepath = output_dir / filename
        
        # 保存为Parquet文件
        results.to_parquet(filepath, index=False)
        
        self.logger.info(f"选股结果已保存: {filepath}")
        return str(filepath)


def create_stock_selector(config: Optional[SelectionConfig] = None) -> StockSelector:
    """
    创建股票选择器
    
    Args:
        config: 选股配置，如果为None则使用默认配置
        
    Returns:
        股票选择器实例
    """
    if config is None:
        config = SelectionConfig()
    
    return StockSelector(config)


def run_stock_selection(symbols: List[str], 
                       trade_date: str,
                       config: Optional[SelectionConfig] = None) -> Tuple[pd.DataFrame, str]:
    """
    运行股票选择
    
    Args:
        symbols: 股票代码列表
        trade_date: 交易日期
        config: 选股配置
        
    Returns:
        (选股结果DataFrame, 保存路径)
    """
    # 创建选择器
    selector = create_stock_selector(config)
    
    # 执行选股
    results = selector.select_stocks(symbols, trade_date)
    
    # 保存结果
    save_path = selector.save_results(results, trade_date)
    
    return results, save_path


# 示例用法
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建配置
    config = SelectionConfig(
        top_n=50,
        momentum_window=120,
        volatility_window=20,
        model_name="rank_topn_neutral",
        version="v1.0"
    )
    
    # 示例股票列表
    symbols = [f"{i:06d}" for i in range(1, 101)]  # 000001-000100
    
    # 运行选股
    results, save_path = run_stock_selection(symbols, "2024-01-15", config)
    
    print(f"选股完成，结果保存至: {save_path}")
    print(f"选择的前10只股票:")
    print(results[['symbol', 'score', 'rank', 'momentum_120', 'volatility_20', 'pe_ttm']].head(10))