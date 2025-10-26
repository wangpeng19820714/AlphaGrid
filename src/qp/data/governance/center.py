# qp/data/governance/center.py
"""数据治理中心"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .quality import DataQualityChecker, QualityReport
from .lineage import DataLineageTracker, DataLineage
from .catalog import DataCatalog, DataAsset
from .policy import DataPolicyManager, AccessControl, ComplianceChecker
from .monitoring import DataMonitor
from .utils import GovernanceConfig, ReportGenerator, AuditLogger


@dataclass
class GovernanceSummary:
    """治理摘要"""
    total_assets: int
    quality_issues: int
    active_alerts: int
    compliance_violations: int
    last_updated: datetime


class DataGovernanceCenter:
    """数据治理中心"""
    
    def __init__(self, config: Optional[GovernanceConfig] = None):
        self.config = config or GovernanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个治理模块
        self.quality_checker = DataQualityChecker()
        self.lineage_tracker = DataLineageTracker()
        self.data_catalog = DataCatalog()
        self.policy_manager = DataPolicyManager()
        self.access_control = AccessControl(self.policy_manager)
        self.compliance_checker = ComplianceChecker(self.policy_manager)
        self.data_monitor = DataMonitor()
        self.report_generator = ReportGenerator()
        self.audit_logger = AuditLogger()
        
        self.logger.info("数据治理中心初始化完成")
    
    def start_governance(self):
        """启动数据治理"""
        # 启动监控
        self.data_monitor.start_monitoring(interval=self.config.monitoring_interval)
        
        # 记录启动日志
        self.audit_logger.log_event(
            event_type="governance_start",
            details={"timestamp": datetime.now().isoformat()}
        )
        
        self.logger.info("数据治理已启动")
    
    def stop_governance(self):
        """停止数据治理"""
        # 停止监控
        self.data_monitor.stop_monitoring()
        
        # 记录停止日志
        self.audit_logger.log_event(
            event_type="governance_stop",
            details={"timestamp": datetime.now().isoformat()}
        )
        
        self.logger.info("数据治理已停止")
    
    def register_data_asset(self, asset: DataAsset) -> str:
        """注册数据资产"""
        # 注册到数据目录
        self.data_catalog.register_asset(asset)
        
        # 记录审计日志
        self.audit_logger.log_event(
            event_type="asset_registered",
            details={
                "asset_id": asset.id,
                "asset_name": asset.name,
                "asset_type": asset.asset_type.value,
                "owner": asset.owner
            }
        )
        
        self.logger.info(f"注册数据资产: {asset.name} ({asset.id})")
        return asset.id
    
    def check_data_quality(self, dataset_id: str, data: List[Any]) -> QualityReport:
        """检查数据质量"""
        # 执行质量检查
        if hasattr(data[0], 'open_price'):  # K线数据
            report = self.quality_checker.check_bars_quality(data)
        elif hasattr(data[0], 'total_revenue'):  # 财务数据
            report = self.quality_checker.check_financial_quality(data)
        else:
            # 通用质量检查
            report = QualityReport(
                dataset_name=dataset_id,
                check_time=datetime.now(),
                metrics=self.quality_checker._calculate_metrics([], len(data)),
                issues=[],
                recommendations=[]
            )
        
        # 记录质量指标
        self.data_monitor.record_data_quality_metric(
            report.metrics.overall_score(), dataset_id
        )
        
        # 记录审计日志
        self.audit_logger.log_event(
            event_type="quality_check",
            details={
                "dataset_id": dataset_id,
                "quality_score": report.metrics.overall_score(),
                "issues_count": len(report.issues)
            }
        )
        
        return report
    
    def track_data_lineage(self, dataset_id: str, **kwargs) -> DataLineage:
        """追踪数据血缘"""
        # 根据数据集类型进行血缘追踪
        if "symbol" in kwargs and "exchange" in kwargs:
            if "interval" in kwargs:
                # K线数据血缘
                lineage = self.lineage_tracker.track_bars_lineage(
                    symbol=kwargs["symbol"],
                    exchange=kwargs["exchange"],
                    interval=kwargs["interval"],
                    start_date=kwargs.get("start_date", ""),
                    end_date=kwargs.get("end_date", ""),
                    provider=kwargs.get("provider", "akshare")
                )
            else:
                # 财务数据血缘
                lineage = self.lineage_tracker.track_financial_lineage(
                    symbol=kwargs["symbol"],
                    exchange=kwargs["exchange"],
                    start_date=kwargs.get("start_date", ""),
                    end_date=kwargs.get("end_date", ""),
                    provider=kwargs.get("provider", "akshare")
                )
        else:
            # 创建通用血缘信息
            lineage = DataLineage(
                dataset_id=dataset_id,
                dataset_name=kwargs.get("name", dataset_id)
            )
        
        # 记录审计日志
        self.audit_logger.log_event(
            event_type="lineage_tracked",
            details={
                "dataset_id": dataset_id,
                "nodes_count": len(lineage.nodes),
                "edges_count": len(lineage.edges)
            }
        )
        
        return lineage
    
    def check_compliance(self, asset_id: str, user_id: str = None,
                        access_level: str = None) -> List[Dict[str, Any]]:
        """检查合规性"""
        from .policy import AccessLevel
        
        # 运行综合合规检查
        access_level_enum = None
        if access_level:
            access_level_enum = AccessLevel(access_level)
        
        checks = self.compliance_checker.run_comprehensive_check(
            asset_id, user_id, access_level_enum
        )
        
        # 记录审计日志
        self.audit_logger.log_event(
            event_type="compliance_check",
            details={
                "asset_id": asset_id,
                "user_id": user_id,
                "checks_count": len(checks),
                "passed_count": len([c for c in checks if c.status == "passed"])
            }
        )
        
        return [
            {
                "check_id": check.check_id,
                "check_type": check.check_type,
                "status": check.status,
                "details": check.details
            }
            for check in checks
        ]
    
    def grant_access(self, user_id: str, asset_id: str, access_level: str,
                    granted_by: str, expires_at: str = None):
        """授予访问权限"""
        from .policy import AccessLevel
        from datetime import datetime
        
        access_level_enum = AccessLevel(access_level)
        expires_datetime = None
        if expires_at:
            expires_datetime = datetime.fromisoformat(expires_at)
        
        self.access_control.grant_access(
            user_id=user_id,
            asset_id=asset_id,
            access_level=access_level_enum,
            granted_by=granted_by,
            expires_at=expires_datetime
        )
        
        # 记录审计日志
        self.audit_logger.log_event(
            event_type="access_granted",
            details={
                "user_id": user_id,
                "asset_id": asset_id,
                "access_level": access_level,
                "granted_by": granted_by,
                "expires_at": expires_at
            }
        )
    
    def revoke_access(self, user_id: str, asset_id: str):
        """撤销访问权限"""
        self.access_control.revoke_access(user_id, asset_id)
        
        # 记录审计日志
        self.audit_logger.log_event(
            event_type="access_revoked",
            details={
                "user_id": user_id,
                "asset_id": asset_id
            }
        )
    
    def get_governance_summary(self) -> GovernanceSummary:
        """获取治理摘要"""
        # 获取资产统计
        asset_stats = self.data_catalog.get_asset_statistics()
        
        # 获取活跃告警
        active_alerts = self.data_monitor.alert_manager.get_active_alerts()
        
        # 获取合规违规
        compliance_violations = len([
            check for check in self.compliance_checker.policy_manager.compliance_checks
            if check.status in ["failed", "warning"]
        ])
        
        return GovernanceSummary(
            total_assets=asset_stats["total_assets"],
            quality_issues=len(active_alerts),  # 简化处理
            active_alerts=len(active_alerts),
            compliance_violations=compliance_violations,
            last_updated=datetime.now()
        )
    
    def generate_governance_report(self, report_type: str = "comprehensive") -> str:
        """生成治理报告"""
        return self.report_generator.generate_report(
            report_type=report_type,
            governance_center=self
        )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        dashboard_data = self.data_monitor.get_dashboard_data()
        
        # 添加治理相关信息
        dashboard_data.update({
            "governance_summary": {
                "total_assets": self.data_catalog.get_asset_statistics()["total_assets"],
                "total_policies": len(self.policy_manager.list_policies()),
                "total_lineages": len(self.lineage_tracker.get_all_lineages())
            },
            "recent_audit_events": self.audit_logger.get_recent_events(limit=10)
        })
        
        return dashboard_data
    
    def search_assets(self, query: str) -> List[Dict[str, Any]]:
        """搜索数据资产"""
        assets = self.data_catalog.discovery.search_assets(query)
        
        return [
            {
                "id": asset.id,
                "name": asset.name,
                "asset_type": asset.asset_type.value,
                "description": asset.description,
                "tags": list(asset.tags),
                "owner": asset.owner,
                "created_at": asset.created_at.isoformat(),
                "updated_at": asset.updated_at.isoformat()
            }
            for asset in assets
        ]
    
    def get_asset_lineage(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """获取资产血缘"""
        lineage = self.lineage_tracker.get_lineage_by_dataset(asset_id)
        
        if not lineage:
            return None
        
        return {
            "dataset_id": lineage.dataset_id,
            "dataset_name": lineage.dataset_name,
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "node_type": node.node_type.value,
                    "metadata": node.metadata
                }
                for node in lineage.nodes
            ],
            "edges": [
                {
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "edge_type": edge.edge_type.value,
                    "metadata": edge.metadata
                }
                for edge in lineage.edges
            ],
            "created_at": lineage.created_at.isoformat(),
            "updated_at": lineage.updated_at.isoformat()
        }
    
    def get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户权限"""
        return self.access_control.get_user_permissions(user_id)
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        return self.audit_logger.get_recent_events(limit=limit)
