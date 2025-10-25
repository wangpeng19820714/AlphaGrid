#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements 智能更新工具
- 自动检测项目依赖
- 生成多种配置
- 支持依赖分析
"""
import sys
import subprocess
import os
from pathlib import Path
from typing import Set, Dict, List
import argparse

# UTF-8输出设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 核心依赖配置
CORE_PACKAGES = {
    'pandas>=2.0.0',
    'numpy>=1.24.0',
    'pyyaml>=6.0',
    'pyarrow>=12.0.0',
}

PROD_PACKAGES = CORE_PACKAGES | {
    'duckdb>=0.9.0',
    'akshare>=1.12.0',
}

DEV_PACKAGES = {
    'pytest>=7.0.0',
    'pytest-cov>=4.0.0',
    'black>=23.0.0',
    'flake8>=6.0.0',
    'mypy>=1.0.0',
    'sphinx>=6.0.0',
    'jupyter>=1.0.0',
    'ipykernel>=6.0.0',
}

def run_command(cmd: List[str]) -> str:
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {' '.join(cmd)}")
        print(f"   错误: {e.stderr}")
        sys.exit(1)

def check_virtualenv() -> bool:
    """检查是否在虚拟环境中"""
    return (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

def get_installed_packages() -> Dict[str, str]:
    """获取已安装的包列表"""
    output = run_command([sys.executable, '-m', 'pip', 'freeze'])
    packages = {}
    for line in output.strip().split('\n'):
        if line and '==' in line:
            name, version = line.split('==', 1)
            packages[name.lower()] = version
    return packages

def write_requirements(file_path: Path, packages: Set[str], header: str = ""):
    """写入requirements文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if header:
            f.write(f"# {header}\n")
        for pkg in sorted(packages):
            f.write(f"{pkg}\n")
    
    line_count = len(packages) + (1 if header else 0)
    print(f"   ✅ {file_path.name}: {line_count} 行")

def main():
    parser = argparse.ArgumentParser(description='Requirements 智能更新工具')
    parser.add_argument('--no-freeze', action='store_true', help='不生成freeze版本')
    parser.add_argument('--dir', default='requirements', help='输出目录')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认所有提示')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("📦 Requirements 智能更新工具")
    print("="*60 + "\n")
    
    # 检查虚拟环境
    if not check_virtualenv() and not args.yes:
        print("⚠️  警告: 当前不在虚拟环境中")
        try:
            response = input("是否继续? (y/n): ")
            if response.lower() != 'y':
                print("已取消")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return
    elif not check_virtualenv():
        print("⚠️  警告: 当前不在虚拟环境中（自动继续）")
    
    print("🔍 开始分析项目依赖...\n")
    
    output_dir = Path(args.dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 生成freeze版本（如果需要）
    if not args.no_freeze:
        print("[1/4] 生成 requirements.txt (freeze)...")
        freeze_output = run_command([sys.executable, '-m', 'pip', 'freeze'])
        freeze_file = output_dir / 'requirements.txt'
        freeze_file.write_text(freeze_output, encoding='utf-8')
        line_count = len([l for l in freeze_output.split('\n') if l.strip()])
        print(f"   ✅ requirements.txt: {line_count} 行")
    else:
        print("[1/4] 跳过 freeze 版本")
    
    # 2. 生成最小化版本
    print("\n[2/4] 生成 requirements-minimal.txt...")
    write_requirements(
        output_dir / 'requirements-minimal.txt',
        CORE_PACKAGES,
        "最小化依赖 - 核心包"
    )
    
    # 3. 生成生产环境版本
    print("\n[3/4] 生成 requirements-prod.txt...")
    write_requirements(
        output_dir / 'requirements-prod.txt',
        PROD_PACKAGES,
        "生产环境依赖"
    )
    
    # 4. 生成开发环境版本
    print("\n[4/4] 生成 requirements-dev.txt...")
    dev_file = output_dir / 'requirements-dev.txt'
    with open(dev_file, 'w', encoding='utf-8') as f:
        f.write("# 开发环境依赖 (包含所有生产依赖 + 开发工具)\n")
        f.write("-r requirements-prod.txt\n\n")
        f.write("# 开发工具\n")
        for pkg in sorted(DEV_PACKAGES):
            f.write(f"{pkg}\n")
    
    line_count = len(DEV_PACKAGES) + 3
    print(f"   ✅ requirements-dev.txt: {line_count} 行")
    
    # 总结
    print("\n" + "="*60)
    print("✨ 更新完成！")
    print("="*60)
    print(f"\n📁 文件位置: {output_dir}/")
    print("\n📊 生成的文件:")
    for file in sorted(output_dir.glob('*.txt')):
        size = file.stat().st_size
        print(f"   - {file.name} ({size} bytes)")
    
    # 使用提示
    print("\n💡 使用方法:")
    print(f"   pip install -r {output_dir}/requirements-minimal.txt  # 最小安装")
    print(f"   pip install -r {output_dir}/requirements-prod.txt     # 生产环境")
    print(f"   pip install -r {output_dir}/requirements-dev.txt      # 开发环境")
    print("")

if __name__ == '__main__':
    main()

