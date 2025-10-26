# qp/data/governance/catalog.py
"""数据目录模块"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
from datetime import datetime
import json
import logging

from ..types import BarData, FinancialData, FundamentalData, Exchange, Interval


class DataAssetType(Enum):
    """数据资产类型"""
    BARS = "bars"                   # K线数据
    FINANCIAL = "financial"         # 财务数据
    FUNDAMENTAL = "fundamental"     # 基本面数据
    MINUTE = "minute"              # 分钟线数据
    DERIVATIVE = "derivative"       # 衍生数据
    THIRD_PARTY = "third_party"    # 第三方数据


class SchemaType(Enum):
    """模式类型"""
    STRUCTURED = "structured"       # 结构化
    SEMI_STRUCTURED = "semi_structured"  # 半结构化
    UNSTRUCTURED = "unstructured"   # 非结构化


@dataclass
class DataSchema:
    """数据模式"""
    name: str
    schema_type: SchemaType
    fields: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataAsset:
    """数据资产"""
    id: str
    name: str
    asset_type: DataAssetType
    description: str = ""
    schema: Optional[DataSchema] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    owner: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0


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


class SchemaRegistry:
    """模式注册表"""
    
    def __init__(self):
        self.schemas: Dict[str, DataSchema] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_schema(self, schema: DataSchema):
        """注册数据模式"""
        self.schemas[schema.name] = schema
        self.logger.info(f"注册数据模式: {schema.name}")
    
    def get_schema(self, name: str) -> Optional[DataSchema]:
        """获取数据模式"""
        return self.schemas.get(name)
    
    def list_schemas(self) -> List[DataSchema]:
        """列出所有数据模式"""
        return list(self.schemas.values())
    
    def validate_data(self, data: pd.DataFrame, schema_name: str) -> Dict[str, Any]:
        """验证数据是否符合模式"""
        schema = self.get_schema(schema_name)
        if not schema:
            return {"valid": False, "error": "模式不存在"}
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查字段
        expected_fields = {field["name"] for field in schema.fields}
        actual_fields = set(data.columns)
        
        missing_fields = expected_fields - actual_fields
        extra_fields = actual_fields - expected_fields
        
        if missing_fields:
            validation_result["errors"].append(f"缺少字段: {missing_fields}")
            validation_result["valid"] = False
        
        if extra_fields:
            validation_result["warnings"].append(f"额外字段: {extra_fields}")
        
        # 检查数据类型
        for field in schema.fields:
            field_name = field["name"]
            expected_type = field.get("type")
            
            if field_name in data.columns and expected_type:
                actual_type = str(data[field_name].dtype)
                if expected_type != actual_type:
                    validation_result["warnings"].append(
                        f"字段 {field_name} 类型不匹配: 期望 {expected_type}, 实际 {actual_type}"
                    )
        
        return validation_result


class MetadataManager:
    """元数据管理器"""
    
    def __init__(self):
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_metadata(self, asset_id: str, metadata: Dict[str, Any]):
        """添加元数据"""
        if asset_id not in self.metadata:
            self.metadata[asset_id] = {}
        
        self.metadata[asset_id].update(metadata)
        self.metadata[asset_id]["updated_at"] = datetime.now().isoformat()
    
    def get_metadata(self, asset_id: str) -> Dict[str, Any]:
        """获取元数据"""
        return self.metadata.get(asset_id, {})
    
    def search_metadata(self, keyword: str) -> List[str]:
        """搜索元数据"""
        results = []
        keyword_lower = keyword.lower()
        
        for asset_id, metadata in self.metadata.items():
            # 搜索键和值
            for key, value in metadata.items():
                if (keyword_lower in key.lower() or 
                    (isinstance(value, str) and keyword_lower in value.lower())):
                    results.append(asset_id)
                    break
        
        return results


class DataDiscovery:
    """数据发现"""
    
    def __init__(self, catalog: 'DataCatalog'):
        self.catalog = catalog
        self.logger = logging.getLogger(__name__)
    
    def discover_by_tags(self, tags: Set[str]) -> List[DataAsset]:
        """根据标签发现数据"""
        results = []
        
        for asset in self.catalog.list_assets():
            if tags.issubset(asset.tags):
                results.append(asset)
        
        return results
    
    def discover_by_type(self, asset_type: DataAssetType) -> List[DataAsset]:
        """根据类型发现数据"""
        return [asset for asset in self.catalog.list_assets() 
                if asset.asset_type == asset_type]
    
    def discover_by_owner(self, owner: str) -> List[DataAsset]:
        """根据所有者发现数据"""
        return [asset for asset in self.catalog.list_assets() 
                if asset.owner == owner]
    
    def discover_by_schema(self, schema_name: str) -> List[DataAsset]:
        """根据模式发现数据"""
        return [asset for asset in self.catalog.list_assets() 
                if asset.schema and asset.schema.name == schema_name]
    
    def search_assets(self, query: str) -> List[DataAsset]:
        """搜索数据资产"""
        results = []
        query_lower = query.lower()
        
        for asset in self.catalog.list_assets():
            # 搜索名称、描述、标签
            if (query_lower in asset.name.lower() or
                query_lower in asset.description.lower() or
                any(query_lower in tag.lower() for tag in asset.tags)):
                results.append(asset)
        
        return results


class DataCatalog:
    """数据目录"""
    
    def __init__(self):
        self.assets: Dict[str, DataAsset] = {}
        self.schema_registry = SchemaRegistry()
        self.metadata_manager = MetadataManager()
        self.discovery = DataDiscovery(self)
        self.logger = logging.getLogger(__name__)
        
        # 初始化默认模式
        self._init_default_schemas()
    
    def _init_default_schemas(self):
        """初始化默认数据模式"""
        # K线数据模式
        bars_schema = DataSchema(
            name="bars_schema",
            schema_type=SchemaType.STRUCTURED,
            fields=[
                {"name": "symbol", "type": "string", "required": True},
                {"name": "exchange", "type": "string", "required": True},
                {"name": "interval", "type": "string", "required": True},
                {"name": "datetime", "type": "datetime64[ns]", "required": True},
                {"name": "open", "type": "float64", "required": True},
                {"name": "high", "type": "float64", "required": True},
                {"name": "low", "type": "float64", "required": True},
                {"name": "close", "type": "float64", "required": True},
                {"name": "volume", "type": "int64", "required": True},
                {"name": "turnover", "type": "float64", "required": False}
            ]
        )
        self.schema_registry.register_schema(bars_schema)
        
        # 财务数据模式
        financial_schema = DataSchema(
            name="financial_schema",
            schema_type=SchemaType.STRUCTURED,
            fields=[
                {"name": "symbol", "type": "string", "required": True},
                {"name": "exchange", "type": "string", "required": True},
                {"name": "report_date", "type": "datetime64[ns]", "required": True},
                {"name": "report_type", "type": "string", "required": True},
                {"name": "total_revenue", "type": "float64", "required": False},
                {"name": "net_profit", "type": "float64", "required": False},
                {"name": "total_assets", "type": "float64", "required": False},
                {"name": "total_liabilities", "type": "float64", "required": False}
            ]
        )
        self.schema_registry.register_schema(financial_schema)
    
    def register_asset(self, asset: DataAsset):
        """注册数据资产"""
        self.assets[asset.id] = asset
        self.logger.info(f"注册数据资产: {asset.name} ({asset.id})")
    
    def get_asset(self, asset_id: str) -> Optional[DataAsset]:
        """获取数据资产"""
        return self.assets.get(asset_id)
    
    def list_assets(self) -> List[DataAsset]:
        """列出所有数据资产"""
        return list(self.assets.values())
    
    def update_asset(self, asset_id: str, updates: Dict[str, Any]):
        """更新数据资产"""
        if asset_id in self.assets:
            asset = self.assets[asset_id]
            for key, value in updates.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            asset.updated_at = datetime.now()
            self.logger.info(f"更新数据资产: {asset_id}")
    
    def delete_asset(self, asset_id: str):
        """删除数据资产"""
        if asset_id in self.assets:
            del self.assets[asset_id]
            self.logger.info(f"删除数据资产: {asset_id}")
    
    def create_asset_from_bars(self, bars: List[BarData], 
                             asset_name: str, description: str = "",
                             tags: Set[str] = None, owner: str = "") -> DataAsset:
        """从K线数据创建资产"""
        if not bars:
            raise ValueError("K线数据不能为空")
        
        # 生成资产ID
        asset_id = f"bars_{bars[0].symbol}_{bars[0].exchange.value}_{len(bars)}"
        
        # 创建数据画像
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
        
        profile = DataProfile(
            asset_id=asset_id,
            row_count=len(df),
            column_count=len(df.columns),
            null_count=df.isnull().sum().sum(),
            duplicate_count=df.duplicated().sum(),
            unique_count=df.nunique().sum(),
            data_types={col: str(dtype) for col, dtype in df.dtypes.items()},
            statistics=df.describe().to_dict()
        )
        
        # 创建资产
        asset = DataAsset(
            id=asset_id,
            name=asset_name,
            asset_type=DataAssetType.BARS,
            description=description,
            schema=self.schema_registry.get_schema("bars_schema"),
            metadata={
                "symbol": bars[0].symbol,
                "exchange": bars[0].exchange.value,
                "interval": bars[0].interval.value,
                "date_range": f"{bars[0].datetime} to {bars[-1].datetime}",
                "profile": profile
            },
            tags=tags or set(),
            owner=owner
        )
        
        self.register_asset(asset)
        return asset
    
    def create_asset_from_financials(self, financials: List[FinancialData],
                                   asset_name: str, description: str = "",
                                   tags: Set[str] = None, owner: str = "") -> DataAsset:
        """从财务数据创建资产"""
        if not financials:
            raise ValueError("财务数据不能为空")
        
        # 类似K线数据的处理逻辑
        asset_id = f"financial_{financials[0].symbol}_{financials[0].exchange.value}_{len(financials)}"
        
        asset = DataAsset(
            id=asset_id,
            name=asset_name,
            asset_type=DataAssetType.FINANCIAL,
            description=description,
            schema=self.schema_registry.get_schema("financial_schema"),
            metadata={
                "symbol": financials[0].symbol,
                "exchange": financials[0].exchange.value,
                "report_types": list(set(f.report_type.value for f in financials))
            },
            tags=tags or set(),
            owner=owner
        )
        
        self.register_asset(asset)
        return asset
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """获取资产统计信息"""
        assets = self.list_assets()
        
        stats = {
            "total_assets": len(assets),
            "by_type": {},
            "by_owner": {},
            "by_tag": {},
            "recent_activity": []
        }
        
        # 按类型统计
        for asset in assets:
            asset_type = asset.asset_type.value
            stats["by_type"][asset_type] = stats["by_type"].get(asset_type, 0) + 1
        
        # 按所有者统计
        for asset in assets:
            owner = asset.owner or "unknown"
            stats["by_owner"][owner] = stats["by_owner"].get(owner, 0) + 1
        
        # 按标签统计
        for asset in assets:
            for tag in asset.tags:
                stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1
        
        # 最近活动
        recent_assets = sorted(assets, key=lambda x: x.updated_at, reverse=True)[:10]
        stats["recent_activity"] = [
            {
                "asset_id": asset.id,
                "name": asset.name,
                "updated_at": asset.updated_at.isoformat()
            }
            for asset in recent_assets
        ]
        
        return stats
    
    def export_catalog(self, format: str = "json") -> str:
        """导出数据目录"""
        catalog_data = {
            "assets": [
                {
                    "id": asset.id,
                    "name": asset.name,
                    "asset_type": asset.asset_type.value,
                    "description": asset.description,
                    "tags": list(asset.tags),
                    "owner": asset.owner,
                    "created_at": asset.created_at.isoformat(),
                    "updated_at": asset.updated_at.isoformat(),
                    "metadata": asset.metadata
                }
                for asset in self.list_assets()
            ],
            "schemas": [
                {
                    "name": schema.name,
                    "schema_type": schema.schema_type.value,
                    "fields": schema.fields,
                    "constraints": schema.constraints
                }
                for schema in self.schema_registry.list_schemas()
            ],
            "export_time": datetime.now().isoformat()
        }
        
        if format == "json":
            return json.dumps(catalog_data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
