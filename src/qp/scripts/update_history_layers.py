# scripts/update_history_layers.py
# -*- coding: utf-8 -*-
"""
历史数据分层更新脚本
- 支持多数据源（akshare, tushare, yfinance）
- 多线程并发下载
- 分层管理（core, sector, full）
"""
from __future__ import annotations
import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone, date
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import pandas as pd

# 设置UTF-8输出（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent  # quant/scripts -> quant -> project_root
sys.path.insert(0, str(project_root))

from quant.storage.stores import ParquetYearWriter, StoreConfig  # 更新为 stores/ 模块

# ========== 常量定义 ==========
REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]

COLUMN_MAPPING = {
    "akshare": {"日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close", "成交量": "volume"},
    "tushare": {"trade_date": "date", "vol": "volume"},
    "yfinance": {"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
}

ADJUST_MAPPING = {
    "none": "",
    "qfq": "qfq",
    "hfq": "hfq"
}

# ========== 配置类 ==========
@dataclass
class GlobalConfig:
    """全局配置"""
    root: str
    provider: str = "akshare"
    adjust: str = "qfq"
    interval: str = "1d"
    start: str = "2024-01-01"
    end: str = "today"
    concurrency: int = 8
    retry: int = 2
    tushare_token: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> GlobalConfig:
        """从字典创建配置"""
        return cls(
            root=data["root"],
            provider=data.get("provider", "akshare"),
            adjust=data.get("adjust", "qfq"),
            interval=data.get("interval", "1d"),
            start=data.get("start", "2024-01-01"),
            end=data.get("end", "today"),
            concurrency=int(data.get("concurrency", 8)),
            retry=int(data.get("retry", 2)),
            tushare_token=data.get("tushare_token") or os.getenv("TUSHARE_TOKEN")
        )

@dataclass
class LayerConfig:
    """层配置"""
    path: str
    symbols: List[str] = field(default_factory=list)
    symbols_file: Optional[str] = None
    auto_discover: bool = False
    update_day_of_week: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> LayerConfig:
        """从字典创建配置"""
        return cls(
            path=data["path"],
            symbols=data.get("symbols", []),
            symbols_file=data.get("symbols_file"),
            auto_discover=data.get("auto_discover", False),
            update_day_of_week=data.get("update_day_of_week")
        )

# ========== 基础数据提取类 ==========
class DataFetcher:
    """数据提取器基类"""
    
    @staticmethod
    def normalize_date_format(date_str: str) -> str:
        """标准化日期格式"""
        return date_str.replace("-", "")
    
    @staticmethod
    def standardize_dataframe(df: pd.DataFrame, column_mapping: Dict) -> pd.DataFrame:
        """标准化DataFrame"""
        if df is None or df.empty:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
        
        # 复制DataFrame避免修改原数据
        df = df.copy()
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 检查是否包含所有必需列
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            # 如果缺少列，填充NaN
            for col in missing_cols:
                df[col] = 0 if col == "volume" else None
        
        # 选择需要的列
        df = df[REQUIRED_COLUMNS].copy()
        
        # 转换日期并排序
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
        
        return df
    
    @staticmethod
    def apply_adjust_factor(df: pd.DataFrame, factor_df: pd.DataFrame, adjust: str) -> pd.DataFrame:
        """应用复权因子"""
        if factor_df is None or factor_df.empty:
            return df
        
        # 合并因子
        df = df.merge(factor_df[["date", "adj_factor"]], on="date", how="left").ffill()
        
        # 计算复权价格
        base_factor = df["adj_factor"].iloc[-1]
        ratio = (df["adj_factor"] / base_factor) if adjust == "qfq" else (base_factor / df["adj_factor"])
        
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float) * ratio
        
        return df


class AkShareFetcher(DataFetcher):
    """AKShare数据提取器"""
    
    @staticmethod
    def fetch(symbol: str, start: str, end: str, adjust: str = "qfq") -> pd.DataFrame:
        import akshare as ak
        
        # 确保参数是字符串
        symbol = str(symbol)
        start = str(start)
        end = str(end)
        
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=DataFetcher.normalize_date_format(start),
            end_date=DataFetcher.normalize_date_format(end),
            adjust=ADJUST_MAPPING.get(adjust.lower(), "")
        )
        
        return DataFetcher.standardize_dataframe(df, COLUMN_MAPPING["akshare"])


class TuShareFetcher(DataFetcher):
    """TuShare数据提取器"""
    
    @staticmethod
    def fetch(symbol: str, start: str, end: str, adjust: str = "qfq", token: Optional[str] = None) -> pd.DataFrame:
        import tushare as ts
        
        if token:
            ts.set_token(token)
        
        pro = ts.pro_api()
        raw = pro.daily(
            ts_code=symbol,
            start_date=DataFetcher.normalize_date_format(start),
            end_date=DataFetcher.normalize_date_format(end)
        )
        
        df = DataFetcher.standardize_dataframe(raw, COLUMN_MAPPING["tushare"])
        
        # 应用复权
        if adjust.lower() != "none":
            factor_df = pro.adj_factor(
                ts_code=symbol,
                start_date=DataFetcher.normalize_date_format(start),
                end_date=DataFetcher.normalize_date_format(end)
            )
            
            if factor_df is not None and not factor_df.empty:
                factor_df = factor_df.rename(columns={"trade_date": "date"})
                factor_df["date"] = pd.to_datetime(factor_df["date"])
                factor_df = factor_df.sort_values("date").ffill()
                df = DataFetcher.apply_adjust_factor(df, factor_df, adjust)
        
        return df


class YFinanceFetcher(DataFetcher):
    """Yahoo Finance数据提取器"""
    
    @staticmethod
    def fetch(symbol: str, start: str, end: str, adjust: str = "none") -> pd.DataFrame:
        import yfinance as yf
        
        auto_adjust = (adjust.lower() != "none")
        df = yf.download(
            symbol,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            interval="1d",
            progress=False
        )
        
        df = df.reset_index()
        return DataFetcher.standardize_dataframe(df, COLUMN_MAPPING["yfinance"])


# 提取器映射
FETCHER_MAP = {
    "akshare": AkShareFetcher.fetch,
    "tushare": TuShareFetcher.fetch,
    "yfinance": YFinanceFetcher.fetch,
}

# ========== 工具函数 ==========
def get_today_str() -> str:
    """获取今日日期字符串"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def ensure_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    确保DataFrame包含有效的OHLCV数据
    
    Args:
        df: 原始DataFrame
        
    Returns:
        清洗后的DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    # 验证必需列
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"缺少必需列: {col}")
    
    # 数据清洗
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].notna()]  # 移除无效日期
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    df = df[df["close"] > 0]  # 移除无效价格
    df["volume"] = df["volume"].fillna(0).astype(float)
    
    return df


def guess_exchange(symbol) -> str:
    """根据股票代码推断交易所"""
    symbol_str = str(symbol).upper()
    
    if symbol_str.endswith(".SZ"):
        return "SZSE"
    elif symbol_str.endswith(".SH"):
        return "SSE"
    elif symbol_str.endswith(".HK"):
        return "HKEX"
    
    # 根据A股代码前缀判断
    if symbol_str.startswith("6"):
        return "SSE"  # 上交所
    elif symbol_str.startswith("0") or symbol_str.startswith("2") or symbol_str.startswith("3"):
        return "SZSE"  # 深交所
    
    return "NASDAQ"


def load_symbols_from_file(file_path: Optional[str]) -> List[str]:
    """
    从文件加载股票代码列表
    
    Args:
        file_path: 文件路径
        
    Returns:
        股票代码列表
    """
    if not file_path:
        return []
    
    path = Path(file_path)
    if not path.exists():
        return []
    
    symbols = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            symbols.append(line)
    
    return symbols

# ========== 更新任务 ==========
@dataclass
class UpdateTask:
    """更新任务"""
    symbol: str
    exchange: str
    layer_name: str


@dataclass
class UpdateResult:
    """更新结果"""
    symbol: str
    rows_appended: int = 0
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.error is None


class LayerUpdater:
    """数据层更新器"""
    
    def __init__(self, global_config: GlobalConfig, layer_config: LayerConfig):
        self.global_config = global_config
        self.layer_config = layer_config
        self.writer = self._create_writer()
        self.fetch_fn = self._get_fetch_function()
    
    def _create_writer(self) -> ParquetYearWriter:
        """创建数据写入器"""
        store_path = Path(self.global_config.root) / self.layer_config.path
        config = StoreConfig(root=str(store_path))
        return ParquetYearWriter(config)
    
    def _get_fetch_function(self) -> Callable:
        """获取数据提取函数"""
        provider = self.global_config.provider
        if provider not in FETCHER_MAP:
            raise ValueError(f"未知的数据提供者: {provider}")
        return FETCHER_MAP[provider]
    
    def _fetch_and_save(self, task: UpdateTask) -> UpdateResult:
        """提取并保存数据"""
        try:
            # 确保symbol是字符串
            symbol_str = str(task.symbol)
            
            # 提取数据
            if self.global_config.provider == "tushare":
                df = self.fetch_fn(
                    symbol_str,
                    self.global_config.start,
                    self.global_config.end,
                    self.global_config.adjust,
                    self.global_config.tushare_token
                )
            else:
                df = self.fetch_fn(
                    symbol_str,
                    self.global_config.start,
                    self.global_config.end,
                    self.global_config.adjust
                )
            
            # 数据清洗
            df = ensure_ohlcv(df)
            
            # 保存数据
            count = 0
            if not df.empty:
                count = self.writer.append(
                    task.exchange,
                    symbol_str,
                    self.global_config.interval,
                    df
                )
            
            return UpdateResult(symbol=symbol_str, rows_appended=count)
        
        except Exception as e:
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return UpdateResult(
                symbol=str(task.symbol),
                error=error_detail
            )
    
    def should_update(self, force: bool = False) -> bool:
        """检查是否应该更新"""
        # 如果不是full层，总是更新
        if not self.layer_config.update_day_of_week:
            return True
        
        # 如果强制更新，跳过日期检查
        if force:
            return True
        
        # 检查是否是指定的更新日
        today = date.today()
        return today.weekday() == self.layer_config.update_day_of_week
    
    def get_symbols(self) -> List[str]:
        """获取要更新的股票列表"""
        symbols = list(self.layer_config.symbols)
        
        # 从文件加载
        if self.layer_config.symbols_file:
            symbols.extend(load_symbols_from_file(self.layer_config.symbols_file))
        
        # 自动发现（占位）
        if self.layer_config.auto_discover and not symbols:
            raise ValueError("auto_discover=true 但未实现自动发现功能")
        
        return symbols
    
    def update(self, force: bool = False) -> Dict:
        """执行更新"""
        # 检查是否应该更新
        if not self.should_update(force):
            return {
                "skipped": True,
                "reason": f"today weekday != {self.layer_config.update_day_of_week}"
            }
        
        # 获取股票列表
        symbols = self.get_symbols()
        if not symbols:
            return {"skipped": True, "reason": "no symbols"}
        
        # 创建任务列表
        tasks = [
            UpdateTask(
                symbol=symbol,
                exchange=guess_exchange(symbol),
                layer_name=self.layer_config.path
            )
            for symbol in symbols
        ]
        
        # 使用线程池执行任务
        results = []
        with ThreadPoolExecutor(max_workers=self.global_config.concurrency) as executor:
            future_to_task = {
                executor.submit(self._fetch_and_save, task): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                result = future.result()
                results.append(result)
        
        # 统计结果
        success_count = sum(1 for r in results if r.success)
        fail_count = sum(1 for r in results if not r.success)
        
        return {
            "skipped": False,
            "ok": success_count,
            "fail": fail_count,
            "detail": [
                {
                    "symbol": r.symbol,
                    "rows_appended": r.rows_appended,
                    "error": r.error
                }
                for r in results
            ]
        }

# ========== 主程序 ==========
def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="更新历史数据分层存储（Parquet + Manifest）"
    )
    parser.add_argument(
        "--config",
        default="configs/data_layers.yaml",
        help="配置文件路径"
    )
    parser.add_argument(
        "--only",
        default="",
        help="只更新指定层（core|sector|full），逗号分隔"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新（忽略full层的周更限制）"
    )
    args = parser.parse_args()
    
    # 加载配置
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {args.config}")
        sys.exit(1)
    
    config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    
    # 解析全局配置和层配置
    global_config = GlobalConfig.from_dict(config_data)
    layers = {
        name: LayerConfig.from_dict(data)
        for name, data in config_data.get("layers", {}).items()
    }
    
    # 处理end="today"的情况
    if global_config.end == "today":
        global_config.end = get_today_str()
    
    # 确定要更新的层
    if args.only:
        layer_names = [name.strip() for name in args.only.split(",") if name.strip()]
    else:
        layer_names = list(layers.keys())
    
    # 执行更新
    print(f"\n{'='*60}")
    print(f"📊 历史数据分层更新")
    print(f"{'='*60}")
    print(f"Provider: {global_config.provider}")
    print(f"Period: {global_config.start} ~ {global_config.end}")
    print(f"Layers: {', '.join(layer_names)}")
    print(f"{'='*60}\n")
    
    summary = {}
    start_time = time.time()
    
    for layer_name in layer_names:
        if layer_name not in layers:
            print(f"⚠️  跳过未知层: {layer_name}")
            continue
        
        print(f"🔄 更新层: {layer_name}")
        
        try:
            updater = LayerUpdater(global_config, layers[layer_name])
            result = updater.update(force=args.force)
            summary[layer_name] = result
            
            if result.get("skipped"):
                print(f"   ⏭️  跳过: {result.get('reason')}")
            else:
                ok = result.get("ok", 0)
                fail = result.get("fail", 0)
                print(f"   ✅ 成功: {ok} | ❌ 失败: {fail}")
                
                # 显示失败详情
                if fail > 0 and args.only:  # 只在单层更新时显示详情
                    for detail in result.get("detail", []):
                        if detail.get("error"):
                            print(f"      {detail['symbol']}: {detail['error']}")
        
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
            summary[layer_name] = {"error": str(e)}
    
    # 输出总结
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✨ 完成，耗时 {elapsed:.1f}秒")
    print(f"{'='*60}")
    
    # 详细统计
    for layer_name, result in summary.items():
        if result.get("error"):
            print(f"- {layer_name}: ❌ {result['error']}")
        elif result.get("skipped"):
            print(f"- {layer_name}: ⏭️  {result['reason']}")
        else:
            ok = result.get("ok", 0)
            fail = result.get("fail", 0)
            total = ok + fail
            success_rate = (ok / total * 100) if total > 0 else 0
            print(f"- {layer_name}: ✅ {ok}/{total} ({success_rate:.1f}%)")


if __name__ == "__main__":
    main()

