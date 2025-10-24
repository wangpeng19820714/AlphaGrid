# 仓库指南

## 项目结构与模块组织
AlphaGrid 以 `quant/` 软件包为核心：`engine/` 承载回测核心（数据加载器、指标、执行），`strategies/` 包含投资组合逻辑，`configs/` 存放场景预设，`scripts/` 打包自动化工具。测试夹具位于 `quant/test/`，依赖存放在 `quant/cache/` 下的合成缓存。仓库层面的工具如 `scripts/update_requirements.py` 以及 `docs/` 中的参考文档用于支撑工具链。市场样例保存在 `data/`，而 `requirements/` 则提供分层的依赖锁（如 `requirements-dev.txt`、`requirements-prod.txt` 等）。

## 构建、测试与开发命令
先创建虚拟环境并安装开发工具：`python -m venv .venv && .\.venv\Scripts\Activate.ps1`，随后执行 `pip install -r requirements/requirements-dev.txt`。使用 `python quant/run_backtest.py` 运行默认场景，或通过 `python quant/run_backtest.py --config configs/basic.ini` 指定预设。通过运行 `python scripts/update_requirements.py --yes` 刷新锁文件。进行交互式试验时，优先选择 `python -m quant.cli`，以保持共享日志和配置加载的一致性。

## 代码风格与命名规范
使用 Python 3.10+ 及 4 空格缩进。模块、包和测试文件遵循 `snake_case`，类名使用 `PascalCase`，运行时配置文件采用 kebab-case 文件名。使用 `black`（行宽 88）格式化代码，并通过 `flake8` 进行 lint。为新逻辑补充类型注解；在提交前运行 `mypy quant`。保持文档字符串简洁但可执行，与代码中的英文摘要保持一致。

## 测试指南
测试套件由 Pytest 驱动；核心规格文件位于 `quant/test/`，命名为 `test_*.py` 或 `*_t1.py` 以覆盖联动场景。本地执行 `pytest quant/test`，并可添加 `--maxfail=1` 加快反馈。功能开发时，请通过 `pytest --cov=quant --cov-report=term-missing` 提供覆盖率。扩展 `test_base.py` 中的共享夹具，而非重复搭建；通过 `test_datahub_integration.py` 中的辅助工具模拟慢速 datahub 调用。

## 提交与 Pull Request 指南
延续历史记录中的精简风格（使用 `提交…` 形式的语句概述改动）。动词保持现在时并确保范围清晰，例如 `提交历史数据模块`。在合适的情况下用方括号引用相关 issue ID。Pull Request 必须包含：(1) 简要的目标概述；(2) 已执行命令/测试的清单；(3) 涉及的配置或数据目录说明；(4) 如 UI/报告输出有变化需附上截图或日志。对于高风险改动（如数据模式、引擎指标）需标注并在合并前至少邀请一名量化审核者。

## 配置与数据处理
切勿将敏感信息提交至 `config.ini`；本地覆写请保存在未跟踪文件中，并通过 `config_manager.py` 支持的 `CONFIG_PATH` 环境变量加载。大型数据集应放在 `data/`，必要时使用 Git LFS。推送前通过 `Remove-Item quant\\cache\\* -Recurse` 清理临时缓存，避免污染差异。
