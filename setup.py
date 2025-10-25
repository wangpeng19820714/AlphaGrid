#!/usr/bin/env python3
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
        return [line.strip() for line in req_file.read_text(encoding='utf-8').split('\n') 
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
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=read_requirements("requirements-prod.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "minimal": read_requirements("requirements-minimal.txt"),
    },
    entry_points={
        "console_scripts": [
            "qp=qp.cli:main",
        ],
    },
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
