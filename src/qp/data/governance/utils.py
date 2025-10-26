# qp/data/governance/utils.py
"""数据治理工具模块"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
import pandas as pd
from pathlib import Path
import yaml
import os


class GovernanceConfig:
    """数据治理配置"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化数据治理配置
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        if config_path is None:
            # 使用默认配置路径
            config_path = self._get_default_config_path()
        
        self.config_data = self._load_config(config_path)
        self._apply_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的路径
        possible_paths = [
            "configs/governance_config.yaml",
            "configs/governance_config.yml",
            "../configs/governance_config.yaml",
            "../../configs/governance_config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 如果找不到配置文件，返回默认路径
        return "configs/governance_config.yaml"
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(config_path):
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"成功加载配置文件: {config_path}")
            return config
            
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "monitoring": {
                "interval": 60,
                "alert_thresholds": {
                    "data_quality_score": 0.8,
                    "data_age_hours": 24,
                    "storage_usage_percent": 90,
                    "api_error_rate": 0.1
                }
            },
            "quality": {
                "enabled": True,
                "rules": ["completeness", "accuracy", "consistency", "validity"],
                "custom_rules": []
            },
            "compliance": {
                "enabled": True,
                "retention_policies": {
                    "bars": "years_3",
                    "financial": "years_7",
                    "fundamental": "years_3"
                }
            },
            "audit": {
                "enabled": True,
                "retention_days": 365,
                "log_level": "INFO"
            },
            "reports": {
                "output_dir": "reports/governance",
                "formats": ["json", "html"],
                "auto_generate": True,
                "schedule": "daily"
            }
        }
    
    def _apply_config(self):
        """应用配置到属性"""
        # 监控配置
        monitoring = self.config_data.get("monitoring", {})
        self.monitoring_interval = monitoring.get("interval", 60)
        self.alert_thresholds = monitoring.get("alert_thresholds", {
            "data_quality_score": 0.8,
            "data_age_hours": 24,
            "storage_usage_percent": 90,
            "api_error_rate": 0.1
        })
        
        # 质量检查配置
        quality = self.config_data.get("quality", {})
        self.quality_check_enabled = quality.get("enabled", True)
        self.quality_rules = quality.get("rules", ["completeness", "accuracy", "consistency", "validity"])
        self.custom_quality_rules = quality.get("custom_rules", [])
        
        # 合规配置
        compliance = self.config_data.get("compliance", {})
        self.compliance_check_enabled = compliance.get("enabled", True)
        self.retention_policies = compliance.get("retention_policies", {
            "bars": "years_3",
            "financial": "years_7",
            "fundamental": "years_3"
        })
        
        # 审计配置
        audit = self.config_data.get("audit", {})
        self.audit_log_enabled = audit.get("enabled", True)
        self.audit_retention_days = audit.get("retention_days", 365)
        self.audit_log_level = audit.get("log_level", "INFO")
        
        # 报告配置
        reports = self.config_data.get("reports", {})
        self.report_output_dir = reports.get("output_dir", "reports/governance")
        self.report_formats = reports.get("formats", ["json", "html"])
        self.auto_generate_reports = reports.get("auto_generate", True)
        self.report_schedule = reports.get("schedule", "daily")
        
        # 数据分类配置
        data_classification = self.config_data.get("data_classification", {})
        self.default_data_classification = data_classification.get("default_level", "internal")
        self.classification_rules = data_classification.get("classification_rules", {})
        
        # 访问控制配置
        access_control = self.config_data.get("access_control", {})
        self.default_access_level = access_control.get("default_access_level", "read")
        self.session_timeout = access_control.get("session_timeout", 3600)
        self.max_concurrent_sessions = access_control.get("max_concurrent_sessions", 10)
        
        # 告警配置
        alerts = self.config_data.get("alerts", {})
        self.alerts_enabled = alerts.get("enabled", True)
        self.alert_channels = alerts.get("channels", ["console", "log"])
        self.alert_rules = alerts.get("rules", {})
        
        # 血缘追踪配置
        lineage = self.config_data.get("lineage", {})
        self.lineage_enabled = lineage.get("enabled", True)
        self.lineage_max_depth = lineage.get("max_depth", 10)
        self.auto_track_lineage = lineage.get("auto_track", True)
        self.lineage_retention_days = lineage.get("retention_days", 90)
        
        # 数据目录配置
        catalog = self.config_data.get("catalog", {})
        self.catalog_enabled = catalog.get("enabled", True)
        self.auto_discovery = catalog.get("auto_discovery", True)
        self.schema_validation = catalog.get("schema_validation", True)
        self.metadata_extraction = catalog.get("metadata_extraction", True)
        
        # 性能配置
        performance = self.config_data.get("performance", {})
        self.batch_size = performance.get("batch_size", 1000)
        self.cache_size = performance.get("cache_size", 10000)
        self.parallel_workers = performance.get("parallel_workers", 4)
        self.operation_timeout = performance.get("timeout", 30)
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，如 "monitoring.interval"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config_data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def update_config(self, key_path: str, value: Any):
        """
        更新配置值
        
        Args:
            key_path: 配置键路径，如 "monitoring.interval"
            value: 新值
        """
        keys = key_path.split('.')
        config = self.config_data
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        
        # 重新应用配置
        self._apply_config()
    
    def save_config(self, config_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用当前路径
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        # 确保目录存在
        config_dir = os.path.dirname(config_path)
        if config_dir:  # 只有当目录路径不为空时才创建
            os.makedirs(config_dir, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            if hasattr(self, 'logger'):
                self.logger.info(f"配置已保存到: {config_path}")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"保存配置文件失败: {e}")
            raise
    
    def reload_config(self, config_path: Optional[str] = None):
        """
        重新加载配置
        
        Args:
            config_path: 配置文件路径，如果为None则使用当前路径
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_data = self._load_config(config_path)
        self._apply_config()
        
        if hasattr(self, 'logger'):
            self.logger.info("配置已重新加载")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.config_data.copy()
    
    def __repr__(self) -> str:
        return f"GovernanceConfig(config_path={self._get_default_config_path()})"


@dataclass
class DataProfile:
    """数据画像"""
    asset_id: str
    row_count: int = 0
    column_count: int = 0
    null_count: int = 0
    duplicate_count: int = 0
    unique_count: int = 0
    data_types: Dict[str, str] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataStatistics:
    """数据统计"""
    total_records: int
    total_size_bytes: int
    last_updated: datetime
    update_frequency: str
    data_freshness_hours: float
    quality_score: float
    access_count: int = 0
    error_count: int = 0


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, report_type: str, 
                       governance_center) -> str:
        """生成治理报告"""
        if report_type == "comprehensive":
            return self._generate_comprehensive_report(governance_center)
        elif report_type == "quality":
            return self._generate_quality_report(governance_center)
        elif report_type == "compliance":
            return self._generate_compliance_report(governance_center)
        elif report_type == "lineage":
            return self._generate_lineage_report(governance_center)
        else:
            raise ValueError(f"不支持的报告类型: {report_type}")
    
    def _generate_comprehensive_report(self, governance_center) -> str:
        """生成综合报告"""
        report_data = {
            "report_type": "comprehensive",
            "generated_at": datetime.now().isoformat(),
            "governance_summary": {
                "total_assets": governance_center.data_catalog.get_asset_statistics()["total_assets"],
                "total_policies": len(governance_center.policy_manager.list_policies()),
                "total_lineages": len(governance_center.lineage_tracker.get_all_lineages()),
                "active_alerts": len(governance_center.data_monitor.alert_manager.get_active_alerts())
            },
            "asset_statistics": governance_center.data_catalog.get_asset_statistics(),
            "health_statuses": {
                name: {
                    "component": status.component,
                    "status": status.status,
                    "message": status.message,
                    "last_check": status.last_check.isoformat(),
                    "metrics": status.metrics
                }
                for name, status in governance_center.data_monitor.health_checker.get_all_health_statuses().items()
            },
            "recent_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat()
                }
                for alert in governance_center.data_monitor.alert_manager.get_active_alerts()[:10]
            ],
            "compliance_summary": self._get_compliance_summary(governance_center)
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_quality_report(self, governance_center) -> str:
        """生成质量报告"""
        report_data = {
            "report_type": "quality",
            "generated_at": datetime.now().isoformat(),
            "quality_summary": {
                "total_checks": 0,  # 这里需要从质量检查器中获取
                "passed_checks": 0,
                "failed_checks": 0,
                "warning_checks": 0
            },
            "quality_metrics": governance_center.data_monitor.get_metrics_summary(),
            "recommendations": [
                "定期检查数据质量",
                "建立数据质量监控机制",
                "制定数据质量改进计划"
            ]
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_compliance_report(self, governance_center) -> str:
        """生成合规报告"""
        report_data = {
            "report_type": "compliance",
            "generated_at": datetime.now().isoformat(),
            "compliance_summary": self._get_compliance_summary(governance_center),
            "policies": [
                {
                    "id": policy.id,
                    "name": policy.name,
                    "description": policy.description,
                    "data_classification": policy.data_classification.value,
                    "retention_policy": policy.retention_policy.value,
                    "enabled": policy.enabled
                }
                for policy in governance_center.policy_manager.list_policies()
            ],
            "access_rules": [
                {
                    "user_id": rule.user_id,
                    "asset_id": rule.asset_id,
                    "access_level": rule.access_level.value,
                    "granted_at": rule.granted_at.isoformat(),
                    "expires_at": rule.expires_at.isoformat() if rule.expires_at else None
                }
                for rule in governance_center.access_control.policy_manager.access_rules
            ]
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_lineage_report(self, governance_center) -> str:
        """生成血缘报告"""
        lineages = governance_center.lineage_tracker.get_all_lineages()
        
        report_data = {
            "report_type": "lineage",
            "generated_at": datetime.now().isoformat(),
            "lineage_summary": {
                "total_lineages": len(lineages),
                "total_nodes": sum(len(lineage.nodes) for lineage in lineages),
                "total_edges": sum(len(lineage.edges) for lineage in lineages)
            },
            "lineages": [
                {
                    "dataset_id": lineage.dataset_id,
                    "dataset_name": lineage.dataset_name,
                    "nodes_count": len(lineage.nodes),
                    "edges_count": len(lineage.edges),
                    "created_at": lineage.created_at.isoformat(),
                    "updated_at": lineage.updated_at.isoformat()
                }
                for lineage in lineages
            ]
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _get_compliance_summary(self, governance_center) -> Dict[str, Any]:
        """获取合规摘要"""
        checks = governance_center.compliance_checker.policy_manager.compliance_checks
        
        return {
            "total_checks": len(checks),
            "passed_checks": len([c for c in checks if c.status == "passed"]),
            "failed_checks": len([c for c in checks if c.status == "failed"]),
            "warning_checks": len([c for c in checks if c.status == "warning"])
        }
    
    def save_report(self, report_content: str, filename: str, 
                   output_dir: str = "reports/governance"):
        """保存报告到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"报告已保存到: {file_path}")


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self):
        self.audit_events: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def log_event(self, event_type: str, details: Dict[str, Any],
                 user_id: str = None, asset_id: str = None):
        """记录审计事件"""
        event = {
            "event_id": f"{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "asset_id": asset_id,
            "details": details
        }
        
        self.audit_events.append(event)
        
        # 保持最近的事件（避免内存过度使用）
        if len(self.audit_events) > 10000:
            self.audit_events = self.audit_events[-5000:]
        
        self.logger.info(f"审计事件: {event_type} - {details}")
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的审计事件"""
        return self.audit_events[-limit:] if self.audit_events else []
    
    def get_events_by_type(self, event_type: str, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """根据类型获取审计事件"""
        events = [event for event in self.audit_events 
                 if event["event_type"] == event_type]
        return events[-limit:] if events else []
    
    def get_events_by_user(self, user_id: str, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """根据用户获取审计事件"""
        events = [event for event in self.audit_events 
                 if event.get("user_id") == user_id]
        return events[-limit:] if events else []
    
    def get_events_by_asset(self, asset_id: str, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """根据资产获取审计事件"""
        events = [event for event in self.audit_events 
                 if event.get("asset_id") == asset_id]
        return events[-limit:] if events else []
    
    def export_audit_log(self, output_file: str, 
                        start_date: datetime = None,
                        end_date: datetime = None):
        """导出审计日志"""
        events = self.audit_events
        
        if start_date:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) >= start_date]
        
        if end_date:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) <= end_date]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"审计日志已导出到: {output_file}")


class DataProfiler:
    """数据画像生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def profile_dataframe(self, df: pd.DataFrame, asset_id: str) -> DataProfile:
        """为DataFrame生成数据画像"""
        profile = DataProfile(
            asset_id=asset_id,
            row_count=len(df),
            column_count=len(df.columns),
            null_count=df.isnull().sum().sum(),
            duplicate_count=df.duplicated().sum(),
            unique_count=df.nunique().sum(),
            data_types={col: str(dtype) for col, dtype in df.dtypes.items()},
            statistics=self._calculate_statistics(df)
        )
        
        return profile
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算数据统计信息"""
        stats = {}
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        # 分类列统计
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            stats["categorical_summary"] = {}
            for col in categorical_cols:
                stats["categorical_summary"][col] = {
                    "unique_count": df[col].nunique(),
                    "most_common": df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None,
                    "most_common_count": df[col].value_counts().iloc[0] if len(df[col].value_counts()) > 0 else 0
                }
        
        # 时间列统计
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            stats["datetime_summary"] = {}
            for col in datetime_cols:
                stats["datetime_summary"][col] = {
                    "min_date": df[col].min().isoformat() if pd.notna(df[col].min()) else None,
                    "max_date": df[col].max().isoformat() if pd.notna(df[col].max()) else None,
                    "date_range_days": (df[col].max() - df[col].min()).days if pd.notna(df[col].min()) and pd.notna(df[col].max()) else None
                }
        
        return stats
    
    def profile_bars_data(self, bars: List[Any], asset_id: str) -> DataProfile:
        """为K线数据生成数据画像"""
        if not bars:
            return DataProfile(asset_id=asset_id)
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'symbol': bar.symbol,
            'exchange': bar.exchange.value,
            'interval': bar.interval.value,
            'datetime': bar.datetime,
            'open': bar.open_price,
            'high': bar.high_price,
            'low': bar.low_price,
            'close': bar.close_price,
            'volume': bar.volume,
            'turnover': bar.turnover
        } for bar in bars])
        
        return self.profile_dataframe(df, asset_id)
    
    def profile_financial_data(self, financials: List[Any], asset_id: str) -> DataProfile:
        """为财务数据生成数据画像"""
        if not financials:
            return DataProfile(asset_id=asset_id)
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'symbol': f.symbol,
            'exchange': f.exchange.value,
            'report_date': f.report_date,
            'report_type': f.report_type.value,
            'total_revenue': f.total_revenue,
            'net_profit': f.net_profit,
            'total_assets': f.total_assets,
            'total_liabilities': f.total_liabilities
        } for f in financials])
        
        return self.profile_dataframe(df, asset_id)
