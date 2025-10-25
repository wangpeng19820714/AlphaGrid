#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements 智能更新工具
- 自动检测项目依赖
- 生成多种配置
- 支持依赖分析
- 适配新的目录结构 (src/qp/)
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
    'tushare>=1.4.0',
    'yfinance>=0.2.0',
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

def detect_project_structure() -> Dict[str, str]:
    """检测项目结构并返回路径信息"""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent  # install/ -> project_root
    
    # 检测新的目录结构
    src_dir = project_root / "src"
    qp_dir = src_dir / "qp" if src_dir.exists() else None
    
    # 检测旧的目录结构
    quant_dir = project_root / "quant"
    
    structure_info = {
        "project_root": str(project_root),
        "script_dir": str(script_dir),
        "structure": "unknown"
    }
    
    if qp_dir and qp_dir.exists():
        structure_info.update({
            "structure": "new",
            "src_dir": str(src_dir),
            "qp_dir": str(qp_dir),
            "data_dir": str(qp_dir / "data"),
            "stores_dir": str(qp_dir / "data" / "stores"),
        })
    elif quant_dir and quant_dir.exists():
        structure_info.update({
            "structure": "old",
            "quant_dir": str(quant_dir),
            "data_dir": str(quant_dir / "datahub"),
            "stores_dir": str(quant_dir / "storage" / "stores"),
        })
    
    return structure_info

def get_installed_packages() -> Dict[str, str]:
    """获取已安装的包列表"""
    output = run_command([sys.executable, '-m', 'pip', 'freeze'])
    packages = {}
    for line in output.strip().split('\n'):
        if line and '==' in line:
            name, version = line.split('==', 1)
            packages[name.lower()] = version
    return packages

def detect_project_dependencies(structure_info: Dict[str, str]) -> Set[str]:
    """检测项目中的实际依赖"""
    detected_deps = set()
    
    # 根据项目结构扫描文件
    if structure_info['structure'] == 'new':
        scan_dirs = [
            structure_info['qp_dir'],
            structure_info['data_dir'],
        ]
    elif structure_info['structure'] == 'old':
        scan_dirs = [
            structure_info['quant_dir'],
            structure_info['data_dir'],
        ]
    else:
        return detected_deps
    
    # 扫描Python文件中的import语句
    for scan_dir in scan_dirs:
        if not Path(scan_dir).exists():
            continue
            
        for py_file in Path(scan_dir).rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 简单的import检测
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # 提取包名
                        if line.startswith('import '):
                            pkg = line.split()[1].split('.')[0]
                        else:  # from ... import
                            pkg = line.split()[1].split('.')[0]
                        
                        # 过滤掉标准库和项目内部模块
                        if pkg not in ['sys', 'os', 'pathlib', 'typing', 'datetime', 'json', 'math', 're', 'collections', 'itertools', 'functools', 'operator', 'qp', 'quant']:
                            detected_deps.add(pkg)
            except Exception:
                continue
    
    return detected_deps

def generate_install_scripts(structure_info: Dict[str, str], output_dir: Path):
    """生成安装脚本"""
    project_root = structure_info['project_root']
    
    # 生成 setup.py
    setup_py_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaGrid 量化平台安装脚本
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# 读取requirements
def read_requirements(filename):
    req_file = Path(__file__).parent / "install" / "requirements" / filename
    if req_file.exists():
        return [line.strip() for line in req_file.read_text(encoding='utf-8').split('\\n') 
                if line.strip() and not line.startswith('#')]
    return []

setup(
    name="alphagrid",
    version="0.1.0",
    description="AlphaGrid 量化交易平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AlphaGrid Team",
    author_email="team@alphagrid.com",
    url="https://github.com/alphagrid/alphagrid",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.10",
    install_requires=read_requirements("requirements-prod.txt"),
    extras_require={{
        "dev": read_requirements("requirements-dev.txt"),
        "minimal": read_requirements("requirements-minimal.txt"),
    }},
    entry_points={{
        "console_scripts": [
            "qp=qp.cli:main",
        ],
    }},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
'''
    
    setup_py_path = Path(project_root) / "setup.py"
    setup_py_path.write_text(setup_py_content, encoding='utf-8')
    print(f"   ✅ setup.py: 已生成")
    
    # 生成 pyproject.toml
    pyproject_toml_content = f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "alphagrid"
version = "0.1.0"
description = "AlphaGrid 量化交易平台"
readme = "README.md"
requires-python = ">=3.10"
authors = [
    {{name = "AlphaGrid Team", email = "team@alphagrid.com"}},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Financial :: Investment",
]

[project.scripts]
qp = "qp.cli:main"

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0", "black>=23.0.0", "flake8>=6.0.0", "mypy>=1.0.0"]
minimal = ["pandas>=2.0.0", "numpy>=1.24.0", "pyyaml>=6.0", "pyarrow>=12.0.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py310']

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
'''
    
    pyproject_toml_path = Path(project_root) / "pyproject.toml"
    pyproject_toml_path.write_text(pyproject_toml_content, encoding='utf-8')
    print(f"   ✅ pyproject.toml: 已生成")

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
    parser.add_argument('--dir', default='install/requirements', help='输出目录')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认所有提示')
    args = parser.parse_args()
    
    # 检测项目结构
    structure_info = detect_project_structure()
    
    print("\n" + "="*60)
    print("📦 Requirements 智能更新工具")
    print("="*60 + "\n")
    
    # 显示项目结构信息
    print(f"🔍 项目结构: {structure_info['structure']}")
    print(f"📁 项目根目录: {structure_info['project_root']}")
    if structure_info['structure'] == 'new':
        print(f"📁 数据目录: {structure_info['data_dir']}")
        print(f"📁 存储目录: {structure_info['stores_dir']}")
    elif structure_info['structure'] == 'old':
        print(f"📁 数据目录: {structure_info['data_dir']}")
        print(f"📁 存储目录: {structure_info['stores_dir']}")
    else:
        print("⚠️  未检测到已知的项目结构")
    print()
    
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
    
    # 检测项目中的实际依赖
    detected_deps = detect_project_dependencies(structure_info)
    if detected_deps:
        print(f"📋 检测到的项目依赖: {', '.join(sorted(detected_deps))}")
        print()
    
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
    
    # 生成安装脚本（针对新目录结构）
    if structure_info['structure'] == 'new':
        print("\n[5/5] 生成安装脚本...")
        generate_install_scripts(structure_info, output_dir)
    
    # 使用提示
    print("\n💡 使用方法:")
    print(f"   pip install -r {output_dir}/requirements-minimal.txt  # 最小安装")
    print(f"   pip install -r {output_dir}/requirements-prod.txt     # 生产环境")
    print(f"   pip install -r {output_dir}/requirements-dev.txt      # 开发环境")
    
    # 显示相对路径（更友好）
    rel_output_dir = output_dir.relative_to(Path.cwd()) if output_dir.is_relative_to(Path.cwd()) else output_dir
    print(f"\n📁 相对路径:")
    print(f"   pip install -r {rel_output_dir}/requirements-minimal.txt")
    print(f"   pip install -r {rel_output_dir}/requirements-prod.txt")
    print(f"   pip install -r {rel_output_dir}/requirements-dev.txt")
    
    if structure_info['structure'] == 'new':
        print(f"\n🚀 快速安装:")
        print(f"   cd {structure_info['project_root']}")
        print(f"   python -m pip install -e .  # 开发模式安装")
        print(f"   python -m qp.cli --help    # 使用CLI工具")
    print("")

if __name__ == '__main__':
    main()

