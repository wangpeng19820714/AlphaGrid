# quant/test/test_base.py
# -*- coding: utf-8 -*-
"""
测试基类 - 减少代码重复
提供通用的测试工具和格式化输出
"""
import sys
import os
from typing import Dict, Any

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def print_header(title: str, width: int = 50):
    """打印标题头"""
    print("=" * width)
    print(f"📊 {title}")
    print("=" * width)


def print_summary(summary: Dict[str, Any]):
    """打印绩效摘要"""
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"{k}: {v:,.2f}" if abs(v) > 1 else f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")


def print_footer(width: int = 50):
    """打印分隔线"""
    print("=" * width)


def print_final_equity(equity: float):
    """打印最终权益"""
    print(f"\n最终权益: {equity:,.2f}")

