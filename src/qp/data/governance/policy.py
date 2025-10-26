# qp/data/governance/policy.py
"""数据策略模块"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

from ..types import BarData, FinancialData, FundamentalData, Exchange, Interval


class DataClassification(Enum):
    """数据分类"""
    PUBLIC = "public"           # 公开
    INTERNAL = "internal"       # 内部
    CONFIDENTIAL = "confidential"  # 机密
    RESTRICTED = "restricted"    # 受限


class AccessLevel(Enum):
    """访问级别"""
    READ = "read"               # 读取
    WRITE = "write"            # 写入
    DELETE = "delete"          # 删除
    ADMIN = "admin"            # 管理


class RetentionPolicy(Enum):
    """保留策略"""
    PERMANENT = "permanent"      # 永久保留
    YEARS_7 = "years_7"         # 保留7年
    YEARS_3 = "years_3"         # 保留3年
    YEARS_1 = "years_1"         # 保留1年
    MONTHS_6 = "months_6"       # 保留6个月
    MONTHS_3 = "months_3"       # 保留3个月
    DAYS_30 = "days_30"         # 保留30天


@dataclass
class DataPolicy:
    """数据策略"""
    id: str
    name: str
    description: str
    data_classification: DataClassification
    retention_policy: RetentionPolicy
    access_rules: List[Dict[str, Any]] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True


@dataclass
class AccessRule:
    """访问规则"""
    user_id: str
    asset_id: str
    access_level: AccessLevel
    granted_by: str
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceCheck:
    """合规检查"""
    check_id: str
    policy_id: str
    asset_id: str
    check_type: str
    status: str  # "passed", "failed", "warning"
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)


class DataPolicyManager:
    """数据策略管理器"""
    
    def __init__(self):
        self.policies: Dict[str, DataPolicy] = {}
        self.access_rules: List[AccessRule] = []
        self.compliance_checks: List[ComplianceCheck] = []
        self.logger = logging.getLogger(__name__)
        
        # 初始化默认策略
        self._init_default_policies()
    
    def _init_default_policies(self):
        """初始化默认数据策略"""
        # K线数据策略
        bars_policy = DataPolicy(
            id="bars_policy",
            name="K线数据策略",
            description="K线数据的访问控制和保留策略",
            data_classification=DataClassification.INTERNAL,
            retention_policy=RetentionPolicy.YEARS_3,
            access_rules=[
                {
                    "role": "analyst",
                    "access_level": AccessLevel.READ.value,
                    "conditions": {"time_restriction": "business_hours"}
                },
                {
                    "role": "developer",
                    "access_level": AccessLevel.WRITE.value,
                    "conditions": {"ip_whitelist": ["192.168.1.0/24"]}
                }
            ],
            compliance_requirements=["数据安全法", "个人信息保护法"]
        )
        self.policies[bars_policy.id] = bars_policy
        
        # 财务数据策略
        financial_policy = DataPolicy(
            id="financial_policy",
            name="财务数据策略",
            description="财务数据的访问控制和保留策略",
            data_classification=DataClassification.CONFIDENTIAL,
            retention_policy=RetentionPolicy.YEARS_7,
            access_rules=[
                {
                    "role": "financial_analyst",
                    "access_level": AccessLevel.READ.value,
                    "conditions": {"need_to_know": True}
                }
            ],
            compliance_requirements=["证券法", "会计法", "数据安全法"]
        )
        self.policies[financial_policy.id] = financial_policy
    
    def create_policy(self, policy: DataPolicy):
        """创建数据策略"""
        self.policies[policy.id] = policy
        self.logger.info(f"创建数据策略: {policy.name}")
    
    def get_policy(self, policy_id: str) -> Optional[DataPolicy]:
        """获取数据策略"""
        return self.policies.get(policy_id)
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]):
        """更新数据策略"""
        if policy_id in self.policies:
            policy = self.policies[policy_id]
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            policy.updated_at = datetime.now()
            self.logger.info(f"更新数据策略: {policy_id}")
    
    def delete_policy(self, policy_id: str):
        """删除数据策略"""
        if policy_id in self.policies:
            del self.policies[policy_id]
            self.logger.info(f"删除数据策略: {policy_id}")
    
    def list_policies(self) -> List[DataPolicy]:
        """列出所有数据策略"""
        return list(self.policies.values())


class AccessControl:
    """访问控制"""
    
    def __init__(self, policy_manager: DataPolicyManager):
        self.policy_manager = policy_manager
        self.logger = logging.getLogger(__name__)
    
    def grant_access(self, user_id: str, asset_id: str, access_level: AccessLevel,
                    granted_by: str, expires_at: Optional[datetime] = None,
                    conditions: Dict[str, Any] = None):
        """授予访问权限"""
        rule = AccessRule(
            user_id=user_id,
            asset_id=asset_id,
            access_level=access_level,
            granted_by=granted_by,
            expires_at=expires_at,
            conditions=conditions or {}
        )
        
        self.policy_manager.access_rules.append(rule)
        self.logger.info(f"授予用户 {user_id} 对资产 {asset_id} 的 {access_level.value} 权限")
    
    def revoke_access(self, user_id: str, asset_id: str):
        """撤销访问权限"""
        self.policy_manager.access_rules = [
            rule for rule in self.policy_manager.access_rules
            if not (rule.user_id == user_id and rule.asset_id == asset_id)
        ]
        self.logger.info(f"撤销用户 {user_id} 对资产 {asset_id} 的访问权限")
    
    def check_access(self, user_id: str, asset_id: str, 
                    required_level: AccessLevel) -> bool:
        """检查访问权限"""
        # 查找用户的访问规则
        user_rules = [
            rule for rule in self.policy_manager.access_rules
            if rule.user_id == user_id and rule.asset_id == asset_id
        ]
        
        if not user_rules:
            return False
        
        # 检查是否有足够的权限级别
        access_levels = [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN]
        required_index = access_levels.index(required_level)
        
        for rule in user_rules:
            # 检查是否过期
            if rule.expires_at and rule.expires_at < datetime.now():
                continue
            
            # 检查权限级别
            rule_index = access_levels.index(rule.access_level)
            if rule_index >= required_index:
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户权限列表"""
        user_rules = [
            rule for rule in self.policy_manager.access_rules
            if rule.user_id == user_id
        ]
        
        permissions = []
        for rule in user_rules:
            if not rule.expires_at or rule.expires_at > datetime.now():
                permissions.append({
                    "asset_id": rule.asset_id,
                    "access_level": rule.access_level.value,
                    "granted_at": rule.granted_at.isoformat(),
                    "expires_at": rule.expires_at.isoformat() if rule.expires_at else None,
                    "conditions": rule.conditions
                })
        
        return permissions


class DataRetentionPolicy:
    """数据保留策略"""
    
    def __init__(self, policy_manager: DataPolicyManager):
        self.policy_manager = policy_manager
        self.logger = logging.getLogger(__name__)
    
    def get_retention_period(self, policy_id: str) -> Optional[timedelta]:
        """获取保留期限"""
        policy = self.policy_manager.get_policy(policy_id)
        if not policy:
            return None
        
        retention_map = {
            RetentionPolicy.PERMANENT: None,
            RetentionPolicy.YEARS_7: timedelta(days=7*365),
            RetentionPolicy.YEARS_3: timedelta(days=3*365),
            RetentionPolicy.YEARS_1: timedelta(days=365),
            RetentionPolicy.MONTHS_6: timedelta(days=6*30),
            RetentionPolicy.MONTHS_3: timedelta(days=3*30),
            RetentionPolicy.DAYS_30: timedelta(days=30)
        }
        
        return retention_map.get(policy.retention_policy)
    
    def is_expired(self, asset_id: str, created_at: datetime, 
                   policy_id: str) -> bool:
        """检查数据是否过期"""
        retention_period = self.get_retention_period(policy_id)
        if retention_period is None:  # 永久保留
            return False
        
        return datetime.now() - created_at > retention_period
    
    def get_expiration_date(self, created_at: datetime, 
                          policy_id: str) -> Optional[datetime]:
        """获取过期日期"""
        retention_period = self.get_retention_period(policy_id)
        if retention_period is None:  # 永久保留
            return None
        
        return created_at + retention_period
    
    def list_expired_assets(self, assets: List[Dict[str, Any]], 
                          policy_id: str) -> List[Dict[str, Any]]:
        """列出过期的资产"""
        expired = []
        
        for asset in assets:
            created_at = asset.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            if self.is_expired(asset["id"], created_at, policy_id):
                expired.append(asset)
        
        return expired


class ComplianceChecker:
    """合规检查器"""
    
    def __init__(self, policy_manager: DataPolicyManager):
        self.policy_manager = policy_manager
        self.logger = logging.getLogger(__name__)
    
    def check_data_classification(self, asset_id: str, 
                                data_classification: DataClassification) -> ComplianceCheck:
        """检查数据分类合规性"""
        # 查找相关策略
        relevant_policies = [
            policy for policy in self.policy_manager.list_policies()
            if policy.data_classification == data_classification
        ]
        
        if not relevant_policies:
            return ComplianceCheck(
                check_id=f"classification_{asset_id}",
                policy_id="",
                asset_id=asset_id,
                check_type="data_classification",
                status="warning",
                details={"message": "未找到相关数据分类策略"}
            )
        
        # 执行检查逻辑
        policy = relevant_policies[0]
        status = "passed"
        details = {"policy_id": policy.id, "classification": data_classification.value}
        
        # 这里可以添加具体的合规检查逻辑
        if data_classification == DataClassification.CONFIDENTIAL:
            # 检查机密数据的特殊要求
            details["encryption_required"] = True
            details["access_logging_required"] = True
        
        return ComplianceCheck(
            check_id=f"classification_{asset_id}",
            policy_id=policy.id,
            asset_id=asset_id,
            check_type="data_classification",
            status=status,
            details=details
        )
    
    def check_access_compliance(self, user_id: str, asset_id: str, 
                               access_level: AccessLevel) -> ComplianceCheck:
        """检查访问合规性"""
        # 查找资产相关策略
        asset_policies = [
            policy for policy in self.policy_manager.list_policies()
            if asset_id in [rule.get("asset_id") for rule in policy.access_rules]
        ]
        
        if not asset_policies:
            return ComplianceCheck(
                check_id=f"access_{user_id}_{asset_id}",
                policy_id="",
                asset_id=asset_id,
                check_type="access_compliance",
                status="warning",
                details={"message": "未找到相关访问策略"}
            )
        
        policy = asset_policies[0]
        
        # 检查访问规则
        access_rules = policy.access_rules
        user_has_access = False
        
        for rule in access_rules:
            if rule.get("user_id") == user_id or rule.get("role"):
                required_level = AccessLevel(rule.get("access_level", "read"))
                access_levels = [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN]
                
                if access_levels.index(access_level) <= access_levels.index(required_level):
                    user_has_access = True
                    break
        
        status = "passed" if user_has_access else "failed"
        details = {
            "policy_id": policy.id,
            "user_id": user_id,
            "required_level": access_level.value,
            "has_access": user_has_access
        }
        
        return ComplianceCheck(
            check_id=f"access_{user_id}_{asset_id}",
            policy_id=policy.id,
            asset_id=asset_id,
            check_type="access_compliance",
            status=status,
            details=details
        )
    
    def check_retention_compliance(self, asset_id: str, created_at: datetime,
                                 policy_id: str) -> ComplianceCheck:
        """检查保留合规性"""
        policy = self.policy_manager.get_policy(policy_id)
        if not policy:
            return ComplianceCheck(
                check_id=f"retention_{asset_id}",
                policy_id=policy_id,
                asset_id=asset_id,
                check_type="retention_compliance",
                status="failed",
                details={"message": "策略不存在"}
            )
        
        retention_policy = DataRetentionPolicy(self.policy_manager)
        is_expired = retention_policy.is_expired(asset_id, created_at, policy_id)
        expiration_date = retention_policy.get_expiration_date(created_at, policy_id)
        
        status = "passed" if not is_expired else "warning"
        details = {
            "policy_id": policy_id,
            "retention_policy": policy.retention_policy.value,
            "is_expired": is_expired,
            "expiration_date": expiration_date.isoformat() if expiration_date else None
        }
        
        return ComplianceCheck(
            check_id=f"retention_{asset_id}",
            policy_id=policy_id,
            asset_id=asset_id,
            check_type="retention_compliance",
            status=status,
            details=details
        )
    
    def run_comprehensive_check(self, asset_id: str, user_id: str = None,
                              access_level: AccessLevel = None) -> List[ComplianceCheck]:
        """运行综合合规检查"""
        checks = []
        
        # 数据分类检查
        # 这里需要从资产信息中获取数据分类
        classification = DataClassification.INTERNAL  # 默认值
        checks.append(self.check_data_classification(asset_id, classification))
        
        # 访问合规检查
        if user_id and access_level:
            checks.append(self.check_access_compliance(user_id, asset_id, access_level))
        
        # 保留合规检查
        policy_id = "bars_policy"  # 默认策略
        created_at = datetime.now()  # 这里应该从资产信息中获取
        checks.append(self.check_retention_compliance(asset_id, created_at, policy_id))
        
        # 保存检查结果
        self.policy_manager.compliance_checks.extend(checks)
        
        return checks
