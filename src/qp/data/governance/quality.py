# qp/data/governance/quality.py
"""数据质量模块"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from ..types import BarData, FinancialData, FundamentalData, Exchange, Interval


class QualityLevel(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"           # 良好
    FAIR = "fair"           # 一般
    POOR = "poor"           # 较差
    CRITICAL = "critical"   # 严重


class QualityRuleType(Enum):
    """质量规则类型"""
    COMPLETENESS = "completeness"    # 完整性
    ACCURACY = "accuracy"           # 准确性
    CONSISTENCY = "consistency"     # 一致性
    VALIDITY = "validity"           # 有效性
    TIMELINESS = "timeliness"       # 时效性


@dataclass
class QualityRule:
    """数据质量规则"""
    name: str
    rule_type: QualityRuleType
    description: str
    threshold: float = 0.95
    weight: float = 1.0
    enabled: bool = True
    custom_check: Optional[callable] = None


@dataclass
class QualityMetrics:
    """数据质量指标"""
    completeness: float = 0.0      # 完整性
    accuracy: float = 0.0         # 准确性
    consistency: float = 0.0      # 一致性
    validity: float = 0.0         # 有效性
    timeliness: float = 0.0       # 时效性
    
    def overall_score(self) -> float:
        """计算总体质量分数"""
        scores = [self.completeness, self.accuracy, self.consistency, 
                 self.validity, self.timeliness]
        return np.mean([s for s in scores if s > 0])


@dataclass
class QualityIssue:
    """数据质量问题"""
    rule_name: str
    issue_type: QualityRuleType
    severity: QualityLevel
    description: str
    affected_records: int
    total_records: int
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QualityReport:
    """数据质量报告"""
    dataset_name: str
    check_time: datetime
    metrics: QualityMetrics
    issues: List[QualityIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def quality_level(self) -> QualityLevel:
        """根据总体分数确定质量等级"""
        score = self.metrics.overall_score()
        if score >= 0.95:
            return QualityLevel.EXCELLENT
        elif score >= 0.85:
            return QualityLevel.GOOD
        elif score >= 0.70:
            return QualityLevel.FAIR
        elif score >= 0.50:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_bar_data(self, bars: List[BarData]) -> List[QualityIssue]:
        """验证K线数据质量"""
        issues = []
        
        if not bars:
            issues.append(QualityIssue(
                rule_name="completeness_check",
                issue_type=QualityRuleType.COMPLETENESS,
                severity=QualityLevel.CRITICAL,
                description="数据为空",
                affected_records=0,
                total_records=0
            ))
            return issues
        
        df = pd.DataFrame([{
            'symbol': bar.symbol,
            'datetime': bar.datetime,
            'open': bar.open_price,
            'high': bar.high_price,
            'low': bar.low_price,
            'close': bar.close_price,
            'volume': bar.volume,
            'turnover': bar.turnover
        } for bar in bars])
        
        # 1. 完整性检查
        issues.extend(self._check_completeness(df))
        
        # 2. 准确性检查
        issues.extend(self._check_accuracy(df))
        
        # 3. 一致性检查
        issues.extend(self._check_consistency(df))
        
        # 4. 有效性检查
        issues.extend(self._check_validity(df))
        
        return issues
    
    def _check_completeness(self, df: pd.DataFrame) -> List[QualityIssue]:
        """检查数据完整性"""
        issues = []
        
        # 检查缺失值
        missing_counts = df.isnull().sum()
        total_records = len(df)
        
        for column, missing_count in missing_counts.items():
            if missing_count > 0:
                completeness_rate = 1 - (missing_count / total_records)
                severity = QualityLevel.CRITICAL if completeness_rate < 0.8 else QualityLevel.POOR
                
                issues.append(QualityIssue(
                    rule_name="missing_values",
                    issue_type=QualityRuleType.COMPLETENESS,
                    severity=severity,
                    description=f"字段 {column} 有 {missing_count} 个缺失值",
                    affected_records=missing_count,
                    total_records=total_records,
                    details={"column": column, "completeness_rate": completeness_rate}
                ))
        
        return issues
    
    def _check_accuracy(self, df: pd.DataFrame) -> List[QualityIssue]:
        """检查数据准确性"""
        issues = []
        
        # 检查价格关系
        invalid_price_count = 0
        for idx, row in df.iterrows():
            if not (row['low'] <= row['open'] <= row['high'] and 
                   row['low'] <= row['close'] <= row['high']):
                invalid_price_count += 1
        
        if invalid_price_count > 0:
            accuracy_rate = 1 - (invalid_price_count / len(df))
            severity = QualityLevel.CRITICAL if accuracy_rate < 0.9 else QualityLevel.POOR
            
            issues.append(QualityIssue(
                rule_name="price_relationship",
                issue_type=QualityRuleType.ACCURACY,
                severity=severity,
                description=f"有 {invalid_price_count} 条记录价格关系异常",
                affected_records=invalid_price_count,
                total_records=len(df),
                details={"accuracy_rate": accuracy_rate}
            ))
        
        return issues
    
    def _check_consistency(self, df: pd.DataFrame) -> List[QualityIssue]:
        """检查数据一致性"""
        issues = []
        
        # 检查时间序列连续性
        if 'datetime' in df.columns:
            df_sorted = df.sort_values('datetime')
            time_diffs = df_sorted['datetime'].diff().dropna()
            
            # 检查是否有异常的时间间隔
            expected_interval = time_diffs.mode().iloc[0] if len(time_diffs) > 0 else None
            if expected_interval:
                outliers = time_diffs[abs(time_diffs - expected_interval) > expected_interval * 0.5]
                
                if len(outliers) > 0:
                    consistency_rate = 1 - (len(outliers) / len(time_diffs))
                    severity = QualityLevel.POOR if consistency_rate < 0.95 else QualityLevel.FAIR
                    
                    issues.append(QualityIssue(
                        rule_name="time_consistency",
                        issue_type=QualityRuleType.CONSISTENCY,
                        severity=severity,
                        description=f"有 {len(outliers)} 个时间间隔异常",
                        affected_records=len(outliers),
                        total_records=len(time_diffs),
                        details={"consistency_rate": consistency_rate}
                    ))
        
        return issues
    
    def _check_validity(self, df: pd.DataFrame) -> List[QualityIssue]:
        """检查数据有效性"""
        issues = []
        
        # 检查数值范围
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'turnover']
        
        for column in numeric_columns:
            if column in df.columns:
                # 检查负值
                negative_count = (df[column] < 0).sum()
                if negative_count > 0:
                    validity_rate = 1 - (negative_count / len(df))
                    severity = QualityLevel.CRITICAL if validity_rate < 0.9 else QualityLevel.POOR
                    
                    issues.append(QualityIssue(
                        rule_name="negative_values",
                        issue_type=QualityRuleType.VALIDITY,
                        severity=severity,
                        description=f"字段 {column} 有 {negative_count} 个负值",
                        affected_records=negative_count,
                        total_records=len(df),
                        details={"column": column, "validity_rate": validity_rate}
                    ))
                
                # 检查异常值（使用IQR方法）
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
                outlier_count = len(outliers)
                
                if outlier_count > 0:
                    validity_rate = 1 - (outlier_count / len(df))
                    severity = QualityLevel.FAIR if validity_rate > 0.9 else QualityLevel.POOR
                    
                    issues.append(QualityIssue(
                        rule_name="outliers",
                        issue_type=QualityRuleType.VALIDITY,
                        severity=severity,
                        description=f"字段 {column} 有 {outlier_count} 个异常值",
                        affected_records=outlier_count,
                        total_records=len(df),
                        details={"column": column, "validity_rate": validity_rate}
                    ))
        
        return issues


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_price_anomalies(self, bars: List[BarData], 
                             method: str = "statistical") -> List[Dict[str, Any]]:
        """检测价格异常"""
        if not bars:
            return []
        
        df = pd.DataFrame([{
            'datetime': bar.datetime,
            'close': bar.close_price,
            'volume': bar.volume
        } for bar in bars])
        
        anomalies = []
        
        if method == "statistical":
            anomalies.extend(self._statistical_anomaly_detection(df))
        elif method == "isolation_forest":
            anomalies.extend(self._isolation_forest_detection(df))
        
        return anomalies
    
    def _statistical_anomaly_detection(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """基于统计方法的异常检测"""
        anomalies = []
        
        # 计算价格变化率
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        
        # 检测价格异常变化
        price_std = df['price_change'].std()
        price_mean = df['price_change'].mean()
        
        price_outliers = df[abs(df['price_change'] - price_mean) > 3 * price_std]
        
        for idx, row in price_outliers.iterrows():
            anomalies.append({
                'datetime': row['datetime'],
                'type': 'price_spike',
                'value': row['close'],
                'change_rate': row['price_change'],
                'severity': 'high' if abs(row['price_change']) > 5 * price_std else 'medium'
            })
        
        return anomalies
    
    def _isolation_forest_detection(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """基于隔离森林的异常检测"""
        # 这里可以集成scikit-learn的IsolationForest
        # 为了简化，暂时返回空列表
        return []


class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validator = DataValidator()
        self.anomaly_detector = AnomalyDetector()
        self.logger = logging.getLogger(__name__)
        
        # 默认质量规则
        self.default_rules = self._init_default_rules()
    
    def _init_default_rules(self) -> List[QualityRule]:
        """初始化默认质量规则"""
        return [
            QualityRule(
                name="completeness_check",
                rule_type=QualityRuleType.COMPLETENESS,
                description="数据完整性检查",
                threshold=0.95
            ),
            QualityRule(
                name="accuracy_check",
                rule_type=QualityRuleType.ACCURACY,
                description="数据准确性检查",
                threshold=0.90
            ),
            QualityRule(
                name="consistency_check",
                rule_type=QualityRuleType.CONSISTENCY,
                description="数据一致性检查",
                threshold=0.95
            ),
            QualityRule(
                name="validity_check",
                rule_type=QualityRuleType.VALIDITY,
                description="数据有效性检查",
                threshold=0.90
            )
        ]
    
    def check_bars_quality(self, bars: List[BarData], 
                          rules: Optional[List[QualityRule]] = None) -> QualityReport:
        """检查K线数据质量"""
        rules = rules or self.default_rules
        
        # 执行质量检查
        issues = self.validator.validate_bar_data(bars)
        
        # 计算质量指标
        metrics = self._calculate_metrics(issues, len(bars))
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return QualityReport(
            dataset_name="bars_data",
            check_time=datetime.now(),
            metrics=metrics,
            issues=issues,
            recommendations=recommendations
        )
    
    def check_financial_quality(self, financials: List[FinancialData]) -> QualityReport:
        """检查财务数据质量"""
        # 类似K线数据的质量检查逻辑
        # 这里简化实现
        return QualityReport(
            dataset_name="financial_data",
            check_time=datetime.now(),
            metrics=QualityMetrics(),
            issues=[],
            recommendations=[]
        )
    
    def _calculate_metrics(self, issues: List[QualityIssue], 
                          total_records: int) -> QualityMetrics:
        """计算质量指标"""
        metrics = QualityMetrics()
        
        if total_records == 0:
            return metrics
        
        # 按规则类型分组计算指标
        rule_types = {}
        for issue in issues:
            rule_type = issue.issue_type
            if rule_type not in rule_types:
                rule_types[rule_type] = []
            rule_types[rule_type].append(issue)
        
        # 计算各项指标
        for rule_type, type_issues in rule_types.items():
            total_affected = sum(issue.affected_records for issue in type_issues)
            rate = 1 - (total_affected / total_records)
            
            if rule_type == QualityRuleType.COMPLETENESS:
                metrics.completeness = rate
            elif rule_type == QualityRuleType.ACCURACY:
                metrics.accuracy = rate
            elif rule_type == QualityRuleType.CONSISTENCY:
                metrics.consistency = rate
            elif rule_type == QualityRuleType.VALIDITY:
                metrics.validity = rate
        
        # 如果没有问题，设置为满分
        if not issues:
            metrics.completeness = 1.0
            metrics.accuracy = 1.0
            metrics.consistency = 1.0
            metrics.validity = 1.0
        
        return metrics
    
    def _generate_recommendations(self, issues: List[QualityIssue]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 按严重程度分组
        critical_issues = [i for i in issues if i.severity == QualityLevel.CRITICAL]
        poor_issues = [i for i in issues if i.severity == QualityLevel.POOR]
        
        if critical_issues:
            recommendations.append("发现严重数据质量问题，建议立即修复")
        
        if poor_issues:
            recommendations.append("发现数据质量问题，建议尽快处理")
        
        # 具体建议
        completeness_issues = [i for i in issues if i.issue_type == QualityRuleType.COMPLETENESS]
        if completeness_issues:
            recommendations.append("建议检查数据源，确保数据完整性")
        
        accuracy_issues = [i for i in issues if i.issue_type == QualityRuleType.ACCURACY]
        if accuracy_issues:
            recommendations.append("建议验证数据准确性，检查价格关系")
        
        return recommendations
