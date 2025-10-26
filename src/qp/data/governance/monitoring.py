# qp/data/governance/monitoring.py
"""数据监控模块"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import pandas as pd
import logging
import threading
import time
from collections import defaultdict, deque

from ..types import BarData, FinancialData, FundamentalData, Exchange, Interval


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"           # 信息
    WARNING = "warning"      # 警告
    ERROR = "error"         # 错误
    CRITICAL = "critical"   # 严重


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"     # 计数器
    GAUGE = "gauge"         # 仪表
    HISTOGRAM = "histogram" # 直方图
    TIMER = "timer"         # 计时器


@dataclass
class Metric:
    """监控指标"""
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """告警"""
    id: str
    name: str
    level: AlertLevel
    message: str
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """健康状态"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    last_check: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.logger = logging.getLogger(__name__)
    
    def record_metric(self, metric: Metric):
        """记录指标"""
        self.metrics[metric.name].append(metric)
        self.logger.debug(f"记录指标: {metric.name} = {metric.value}")
    
    def get_metric_history(self, name: str, 
                          duration: Optional[timedelta] = None) -> List[Metric]:
        """获取指标历史"""
        if name not in self.metrics:
            return []
        
        metrics = list(self.metrics[name])
        
        if duration:
            cutoff_time = datetime.now() - duration
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        return metrics
    
    def get_latest_metric(self, name: str) -> Optional[Metric]:
        """获取最新指标"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        return self.metrics[name][-1]
    
    def get_metric_statistics(self, name: str, 
                             duration: Optional[timedelta] = None) -> Dict[str, float]:
        """获取指标统计"""
        metrics = self.get_metric_history(name, duration)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "latest": values[-1]
        }


class AlertManager:
    """告警管理器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.logger = logging.getLogger(__name__)
        
        # 初始化默认告警规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        self.alert_rules = {
            "data_quality_low": {
                "metric_name": "data_quality_score",
                "threshold": 0.8,
                "level": AlertLevel.WARNING,
                "message": "数据质量分数过低"
            },
            "data_freshness_old": {
                "metric_name": "data_age_hours",
                "threshold": 24,
                "level": AlertLevel.ERROR,
                "message": "数据更新延迟"
            },
            "storage_space_low": {
                "metric_name": "storage_usage_percent",
                "threshold": 90,
                "level": AlertLevel.CRITICAL,
                "message": "存储空间不足"
            },
            "api_error_rate_high": {
                "metric_name": "api_error_rate",
                "threshold": 0.1,
                "level": AlertLevel.ERROR,
                "message": "API错误率过高"
            }
        }
    
    def add_alert_rule(self, name: str, rule: Dict[str, Any]):
        """添加告警规则"""
        self.alert_rules[name] = rule
        self.logger.info(f"添加告警规则: {name}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    def check_alerts(self):
        """检查告警"""
        for rule_name, rule in self.alert_rules.items():
            metric_name = rule["metric_name"]
            threshold = rule["threshold"]
            level = rule["level"]
            message = rule["message"]
            
            latest_metric = self.metrics_collector.get_latest_metric(metric_name)
            if not latest_metric:
                continue
            
            current_value = latest_metric.value
            
            # 检查是否触发告警
            should_alert = False
            if metric_name in ["data_age_hours", "storage_usage_percent", "api_error_rate"]:
                should_alert = current_value > threshold
            elif metric_name == "data_quality_score":
                should_alert = current_value < threshold
            
            if should_alert:
                # 检查是否已有未解决的告警
                existing_alert = self._find_active_alert(rule_name)
                
                if not existing_alert:
                    # 创建新告警
                    alert = Alert(
                        id=f"{rule_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        name=rule_name,
                        level=level,
                        message=f"{message}: {current_value} (阈值: {threshold})",
                        metric_name=metric_name,
                        threshold=threshold,
                        current_value=current_value
                    )
                    
                    self.alerts.append(alert)
                    self._trigger_alert(alert)
                    self.logger.warning(f"触发告警: {alert.name} - {alert.message}")
    
    def _find_active_alert(self, rule_name: str) -> Optional[Alert]:
        """查找活跃告警"""
        for alert in reversed(self.alerts):
            if alert.name == rule_name and not alert.resolved_at:
                return alert
        return None
    
    def _trigger_alert(self, alert: Alert):
        """触发告警"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"告警处理器执行失败: {e}")
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved_at:
                alert.resolved_at = datetime.now()
                self.logger.info(f"解决告警: {alert.name}")
                break
    
    def acknowledge_alert(self, alert_id: str):
        """确认告警"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"确认告警: {alert.name}")
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if not alert.resolved_at]
    
    def get_alert_statistics(self) -> Dict[str, int]:
        """获取告警统计"""
        stats = defaultdict(int)
        
        for alert in self.alerts:
            stats[f"{alert.level.value}_total"] += 1
            
            if not alert.resolved_at:
                stats[f"{alert.level.value}_active"] += 1
            
            if alert.acknowledged:
                stats[f"{alert.level.value}_acknowledged"] += 1
        
        return dict(stats)


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.health_statuses: Dict[str, HealthStatus] = {}
        self.health_checks: Dict[str, Callable[[], HealthStatus]] = {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化默认健康检查
        self._init_default_checks()
    
    def _init_default_checks(self):
        """初始化默认健康检查"""
        self.health_checks = {
            "data_service": self._check_data_service,
            "storage_service": self._check_storage_service,
            "provider_service": self._check_provider_service
        }
    
    def _check_data_service(self) -> HealthStatus:
        """检查数据服务健康状态"""
        # 检查数据质量指标
        quality_metric = self.metrics_collector.get_latest_metric("data_quality_score")
        if not quality_metric:
            return HealthStatus(
                component="data_service",
                status="unhealthy",
                message="无法获取数据质量指标"
            )
        
        if quality_metric.value >= 0.9:
            status = "healthy"
            message = "数据服务运行正常"
        elif quality_metric.value >= 0.7:
            status = "degraded"
            message = "数据质量略有下降"
        else:
            status = "unhealthy"
            message = "数据质量严重下降"
        
        return HealthStatus(
            component="data_service",
            status=status,
            message=message,
            metrics={"quality_score": quality_metric.value}
        )
    
    def _check_storage_service(self) -> HealthStatus:
        """检查存储服务健康状态"""
        # 检查存储使用率
        storage_metric = self.metrics_collector.get_latest_metric("storage_usage_percent")
        if not storage_metric:
            return HealthStatus(
                component="storage_service",
                status="unhealthy",
                message="无法获取存储使用率指标"
            )
        
        if storage_metric.value < 80:
            status = "healthy"
            message = "存储空间充足"
        elif storage_metric.value < 90:
            status = "degraded"
            message = "存储空间使用率较高"
        else:
            status = "unhealthy"
            message = "存储空间严重不足"
        
        return HealthStatus(
            component="storage_service",
            status=status,
            message=message,
            metrics={"usage_percent": storage_metric.value}
        )
    
    def _check_provider_service(self) -> HealthStatus:
        """检查数据提供者服务健康状态"""
        # 检查API错误率
        error_rate_metric = self.metrics_collector.get_latest_metric("api_error_rate")
        if not error_rate_metric:
            return HealthStatus(
                component="provider_service",
                status="unhealthy",
                message="无法获取API错误率指标"
            )
        
        if error_rate_metric.value < 0.05:
            status = "healthy"
            message = "数据提供者服务正常"
        elif error_rate_metric.value < 0.1:
            status = "degraded"
            message = "API错误率略有上升"
        else:
            status = "unhealthy"
            message = "API错误率过高"
        
        return HealthStatus(
            component="provider_service",
            status=status,
            message=message,
            metrics={"error_rate": error_rate_metric.value}
        )
    
    def add_health_check(self, name: str, check_func: Callable[[], HealthStatus]):
        """添加健康检查"""
        self.health_checks[name] = check_func
    
    def run_health_checks(self):
        """运行健康检查"""
        for name, check_func in self.health_checks.items():
            try:
                status = check_func()
                self.health_statuses[name] = status
                self.logger.debug(f"健康检查 {name}: {status.status}")
            except Exception as e:
                self.logger.error(f"健康检查 {name} 失败: {e}")
                self.health_statuses[name] = HealthStatus(
                    component=name,
                    status="unhealthy",
                    message=f"健康检查失败: {str(e)}"
                )
    
    def get_health_status(self, component: str) -> Optional[HealthStatus]:
        """获取组件健康状态"""
        return self.health_statuses.get(component)
    
    def get_all_health_statuses(self) -> Dict[str, HealthStatus]:
        """获取所有健康状态"""
        return self.health_statuses.copy()


class MonitoringDashboard:
    """监控仪表板"""
    
    def __init__(self, metrics_collector: MetricsCollector, 
                 alert_manager: AlertManager, health_checker: HealthChecker):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_checker = health_checker
        self.logger = logging.getLogger(__name__)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            "timestamp": datetime.now().isoformat(),
            "health_statuses": {
                name: {
                    "component": status.component,
                    "status": status.status,
                    "message": status.message,
                    "last_check": status.last_check.isoformat(),
                    "metrics": status.metrics
                }
                for name, status in self.health_checker.get_all_health_statuses().items()
            },
            "active_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in self.alert_manager.get_active_alerts()
            ],
            "key_metrics": self._get_key_metrics(),
            "alert_statistics": self.alert_manager.get_alert_statistics()
        }
    
    def _get_key_metrics(self) -> Dict[str, Any]:
        """获取关键指标"""
        key_metrics = {}
        
        metric_names = [
            "data_quality_score",
            "data_age_hours", 
            "storage_usage_percent",
            "api_error_rate",
            "data_processing_time",
            "daily_data_volume"
        ]
        
        for metric_name in metric_names:
            stats = self.metrics_collector.get_metric_statistics(metric_name)
            if stats:
                key_metrics[metric_name] = stats
        
        return key_metrics


class DataMonitor:
    """数据监控器"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.health_checker = HealthChecker(self.metrics_collector)
        self.dashboard = MonitoringDashboard(
            self.metrics_collector, 
            self.alert_manager, 
            self.health_checker
        )
        
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # 添加默认告警处理器
        self.alert_manager.add_alert_handler(self._default_alert_handler)
    
    def _default_alert_handler(self, alert: Alert):
        """默认告警处理器"""
        self.logger.warning(f"告警: {alert.level.value.upper()} - {alert.message}")
    
    def start_monitoring(self, interval: int = 60):
        """开始监控"""
        if self.is_running:
            self.logger.warning("监控已在运行中")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info(f"开始数据监控，检查间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        self.logger.info("停止数据监控")
    
    def _monitoring_loop(self, interval: int):
        """监控循环"""
        while self.is_running:
            try:
                # 运行健康检查
                self.health_checker.run_health_checks()
                
                # 检查告警
                self.alert_manager.check_alerts()
                
                # 记录监控指标
                self._record_monitoring_metrics()
                
            except Exception as e:
                self.logger.error(f"监控循环执行失败: {e}")
            
            time.sleep(interval)
    
    def _record_monitoring_metrics(self):
        """记录监控指标"""
        # 记录系统指标
        self.metrics_collector.record_metric(Metric(
            name="monitoring_uptime",
            metric_type=MetricType.GAUGE,
            value=time.time(),
            labels={"component": "data_monitor"}
        ))
        
        # 记录活跃告警数量
        active_alerts = len(self.alert_manager.get_active_alerts())
        self.metrics_collector.record_metric(Metric(
            name="active_alerts_count",
            metric_type=MetricType.GAUGE,
            value=active_alerts,
            labels={"component": "alert_manager"}
        ))
    
    def record_data_quality_metric(self, quality_score: float, dataset: str):
        """记录数据质量指标"""
        self.metrics_collector.record_metric(Metric(
            name="data_quality_score",
            metric_type=MetricType.GAUGE,
            value=quality_score,
            labels={"dataset": dataset}
        ))
    
    def record_data_age_metric(self, age_hours: float, dataset: str):
        """记录数据年龄指标"""
        self.metrics_collector.record_metric(Metric(
            name="data_age_hours",
            metric_type=MetricType.GAUGE,
            value=age_hours,
            labels={"dataset": dataset}
        ))
    
    def record_storage_usage_metric(self, usage_percent: float, storage_type: str):
        """记录存储使用率指标"""
        self.metrics_collector.record_metric(Metric(
            name="storage_usage_percent",
            metric_type=MetricType.GAUGE,
            value=usage_percent,
            labels={"storage_type": storage_type}
        ))
    
    def record_api_error_rate_metric(self, error_rate: float, provider: str):
        """记录API错误率指标"""
        self.metrics_collector.record_metric(Metric(
            name="api_error_rate",
            metric_type=MetricType.GAUGE,
            value=error_rate,
            labels={"provider": provider}
        ))
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return self.dashboard.get_dashboard_data()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        metric_names = [
            "data_quality_score",
            "data_age_hours",
            "storage_usage_percent", 
            "api_error_rate"
        ]
        
        for metric_name in metric_names:
            stats = self.metrics_collector.get_metric_statistics(metric_name)
            if stats:
                summary[metric_name] = stats
        
        return summary
