#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaGrid CLI 工具

提供命令行接口来使用AlphaGrid的各种功能
"""

import argparse
import sys
from datetime import datetime, timedelta
import pandas as pd

from datahub.services import MinuteDataService, BarDataService
from datahub.types import Exchange, Interval


def minute_data_command(args):
    """分钟线数据命令"""
    service = MinuteDataService()
    
    if args.action == "import":
        # 导入分钟线数据
        end_time = pd.Timestamp.now(tz="UTC")
        start_time = end_time - pd.Timedelta(days=args.days)
        
        print(f"正在导入 {args.symbol} 的 {args.interval} 数据...")
        print(f"时间范围: {start_time} 到 {end_time}")
        
        try:
            count = service.import_minute_data(
                symbol=args.symbol,
                exchange=Exchange(args.exchange),
                interval=Interval(args.interval),
                start=start_time,
                end=end_time
            )
            print(f"成功导入 {count} 条数据")
        except Exception as e:
            print(f"导入失败: {e}")
            return 1
    
    elif args.action == "query":
        # 查询分钟线数据
        print(f"正在查询 {args.symbol} 的 {args.interval} 数据...")
        
        try:
            if args.latest:
                bars = service.get_latest_n_minutes(
                    symbol=args.symbol,
                    exchange=Exchange(args.exchange),
                    interval=Interval(args.interval),
                    n=args.latest
                )
                print(f"获取到 {len(bars)} 条最新数据")
            else:
                bars = service.get_today_minutes(
                    symbol=args.symbol,
                    exchange=Exchange(args.exchange),
                    interval=Interval(args.interval)
                )
                print(f"获取到 {len(bars)} 条今日数据")
            
            if bars:
                print("\n最新数据:")
                latest = bars[-1]
                print(f"  时间: {latest.datetime}")
                print(f"  开盘: {latest.open_price}")
                print(f"  最高: {latest.high_price}")
                print(f"  最低: {latest.low_price}")
                print(f"  收盘: {latest.close_price}")
                print(f"  成交量: {latest.volume:,.0f}")
        except Exception as e:
            print(f"查询失败: {e}")
            return 1
    
    elif args.action == "realtime":
        # 获取实时数据
        print(f"正在获取 {args.symbol} 的实时数据...")
        
        try:
            realtime = service.get_realtime_minute(
                symbol=args.symbol,
                exchange=Exchange(args.exchange),
                interval=Interval(args.interval)
            )
            
            if realtime:
                print("实时数据:")
                print(f"  时间: {realtime.datetime}")
                print(f"  开盘: {realtime.open_price}")
                print(f"  最高: {realtime.high_price}")
                print(f"  最低: {realtime.low_price}")
                print(f"  收盘: {realtime.close_price}")
                print(f"  成交量: {realtime.volume:,.0f}")
            else:
                print("暂无实时数据")
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            return 1
    
    elif args.action == "stats":
        # 获取统计信息
        print(f"正在获取 {args.symbol} 的统计信息...")
        
        try:
            stats = service.get_minute_stats(
                symbol=args.symbol,
                exchange=Exchange(args.exchange),
                interval=Interval(args.interval)
            )
            
            print("统计信息:")
            print(f"  数据条数: {stats['count']}")
            print(f"  时间范围: {stats['start_time']} 到 {stats['end_time']}")
            print(f"  最新价格: {stats['latest_price']}")
            print(f"  价格区间: {stats['price_range']['min']:.2f} - {stats['price_range']['max']:.2f}")
            print(f"  总成交量: {stats['volume_total']:,.0f}")
            
            # 检查市场状态
            is_open = service.is_market_open(args.symbol, Exchange(args.exchange))
            print(f"  市场状态: {'开盘' if is_open else '收盘'}")
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return 1
    
    return 0


def bar_data_command(args):
    """K线数据命令"""
    service = BarDataService()
    
    if args.action == "import":
        # 导入日线数据
        end_time = pd.Timestamp.now(tz="UTC")
        start_time = end_time - pd.Timedelta(days=args.days)
        
        print(f"正在导入 {args.symbol} 的日线数据...")
        print(f"时间范围: {start_time} 到 {end_time}")
        
        try:
            from datahub.providers import get_provider
            provider = get_provider("akshare")
            
            count = service.import_from_provider(
                provider=provider,
                symbol=args.symbol,
                exchange=Exchange(args.exchange),
                interval=Interval.DAILY,
                start=start_time,
                end=end_time
            )
            print(f"成功导入 {count} 条数据")
        except Exception as e:
            print(f"导入失败: {e}")
            return 1
    
    elif args.action == "query":
        # 查询日线数据
        print(f"正在查询 {args.symbol} 的日线数据...")
        
        try:
            bars = service.load_bars(
                symbol=args.symbol,
                exchange=Exchange(args.exchange),
                interval=Interval.DAILY
            )
            print(f"获取到 {len(bars)} 条数据")
            
            if bars:
                print("\n最新数据:")
                latest = bars[-1]
                print(f"  时间: {latest.datetime}")
                print(f"  开盘: {latest.open_price}")
                print(f"  最高: {latest.high_price}")
                print(f"  最低: {latest.low_price}")
                print(f"  收盘: {latest.close_price}")
                print(f"  成交量: {latest.volume:,.0f}")
        except Exception as e:
            print(f"查询失败: {e}")
            return 1
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AlphaGrid CLI 工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 分钟线数据命令
    minute_parser = subparsers.add_parser("minute", help="分钟线数据操作")
    minute_parser.add_argument("action", choices=["import", "query", "realtime", "stats"],
                              help="操作类型")
    minute_parser.add_argument("--symbol", "-s", required=True, help="股票代码")
    minute_parser.add_argument("--exchange", "-e", default="SZSE", 
                              choices=["SSE", "SZSE", "HKEX", "NYSE", "NASDAQ"],
                              help="交易所")
    minute_parser.add_argument("--interval", "-i", default="1m",
                              choices=["1m", "5m", "15m", "30m", "1h"],
                              help="时间周期")
    minute_parser.add_argument("--days", "-d", type=int, default=1, help="导入天数")
    minute_parser.add_argument("--latest", "-n", type=int, help="获取最新N条数据")
    
    # K线数据命令
    bar_parser = subparsers.add_parser("bar", help="K线数据操作")
    bar_parser.add_argument("action", choices=["import", "query"], help="操作类型")
    bar_parser.add_argument("--symbol", "-s", required=True, help="股票代码")
    bar_parser.add_argument("--exchange", "-e", default="SZSE",
                          choices=["SSE", "SZSE", "HKEX", "NYSE", "NASDAQ"],
                          help="交易所")
    bar_parser.add_argument("--days", "-d", type=int, default=30, help="导入天数")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "minute":
        return minute_data_command(args)
    elif args.command == "bar":
        return bar_data_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
