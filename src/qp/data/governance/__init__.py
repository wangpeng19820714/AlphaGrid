# qp/data/governance/__init__.py
"""
数据治理模块统一接口

提供数据质量、血缘、目录、策略和监控的完整治理解决方案

主要功能：
- 数据质量：完整性、准确性、一致性检查
- 数据血缘：数据流向追踪和影响分析
- 数据目录：元数据管理和数据发现
- 数据策略：合规性和访问控制
- 数据监控：实时监控和告警

快速开始：
    from qp.data.governance import DataGovernanceCenter
    from qp.data.governance import DataQualityChecker, DataLineageTracker
    
    # 初始化治理中心
    governance = DataGovernanceCenter()
    
    # 数据质量检查
    quality_checker = DataQualityChecker()
    result = quality_checker.check_bars_quality(symbol, start_date, end_date)
    
    # 数据血缘追踪
    lineage_tracker = DataLineageTracker()
    lineage = lineage_tracker.trace_data_lineage(symbol, start_date, end_date)
"""

# ========== 核心治理中心 ==========
from .center import DataGovernanceCenter

# ========== 数据质量模块 ==========
from .quality import (
    DataQualityChecker,
    QualityRule,
    QualityReport,
    QualityMetrics,
    DataValidator,
    AnomalyDetector,
)

# ========== 数据血缘模块 ==========
from .lineage import (
    DataLineageTracker,
    LineageNode,
    LineageEdge,
    LineageGraph,
    ImpactAnalyzer,
)

# ========== 数据目录模块 ==========
from .catalog import (
    DataCatalog,
    MetadataManager,
    DataAsset,
    SchemaRegistry,
    DataDiscovery,
)

# ========== 数据策略模块 ==========
from .policy import (
    DataPolicyManager,
    AccessControl,
    AccessLevel,
    DataRetentionPolicy,
    ComplianceChecker,
    DataClassification,
)

# ========== 数据监控模块 ==========
from .monitoring import (
    DataMonitor,
    MonitoringDashboard,
    AlertManager,
    MetricsCollector,
    HealthChecker,
)

# ========== 工具和工具类 ==========
from .utils import (
    GovernanceConfig,
    DataProfile,
    DataStatistics,
    ReportGenerator,
    AuditLogger,
)

# ========== 导出清单 ==========
__all__ = [
    # 核心治理中心
    "DataGovernanceCenter",
    
    # 数据质量
    "DataQualityChecker",
    "QualityRule",
    "QualityReport", 
    "QualityMetrics",
    "DataValidator",
    "AnomalyDetector",
    
    # 数据血缘
    "DataLineageTracker",
    "LineageNode",
    "LineageEdge", 
    "LineageGraph",
    "ImpactAnalyzer",
    
    # 数据目录
    "DataCatalog",
    "MetadataManager",
    "DataAsset",
    "SchemaRegistry",
    "DataDiscovery",
    
    # 数据策略
    "DataPolicyManager",
    "AccessControl",
    "AccessLevel",
    "DataRetentionPolicy",
    "ComplianceChecker",
    "DataClassification",
    
    # 数据监控
    "DataMonitor",
    "MonitoringDashboard",
    "AlertManager",
    "MetricsCollector",
    "HealthChecker",
    
    # 工具类
    "GovernanceConfig",
    "DataProfile",
    "DataStatistics",
    "ReportGenerator",
    "AuditLogger",
]
