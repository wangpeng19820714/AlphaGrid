# qp/data/governance/lineage.py
"""数据血缘模块"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
from datetime import datetime
import logging
from collections import defaultdict, deque

# 可选依赖
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    # 创建一个简单的图类作为替代
    class SimpleDiGraph:
        def __init__(self):
            self._nodes = {}
            self._edges = {}
        
        def add_node(self, node_id, **attrs):
            self._nodes[node_id] = attrs
        
        def add_edge(self, source, target, **attrs):
            if source not in self._edges:
                self._edges[source] = []
            self._edges[source].append((target, attrs))
        
        def predecessors(self, node_id):
            return [source for source, targets in self._edges.items() 
                   if any(target == node_id for target, _ in targets)]
        
        def successors(self, node_id):
            return [target for target, _ in self._edges.get(node_id, [])]
        
        def ancestors(self, node_id):
            visited = set()
            stack = [node_id]
            ancestors = set()
            
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                
                for pred in self.predecessors(current):
                    if pred not in visited:
                        ancestors.add(pred)
                        stack.append(pred)
            
            return ancestors
        
        def descendants(self, node_id):
            visited = set()
            stack = [node_id]
            descendants = set()
            
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                
                for succ in self.successors(current):
                    if succ not in visited:
                        descendants.add(succ)
                        stack.append(succ)
            
            return descendants

    nx = type('NetworkX', (), {
        'DiGraph': SimpleDiGraph,
        'NetworkXNoPath': Exception,
        'all_simple_paths': lambda G, source, target: []
    })()

from ..types import BarData, FinancialData, FundamentalData, Exchange, Interval


class NodeType(Enum):
    """节点类型"""
    DATA_SOURCE = "data_source"      # 数据源
    PROVIDER = "provider"           # 数据提供者
    SERVICE = "service"             # 数据服务
    STORE = "store"                 # 数据存储
    TRANSFORMATION = "transformation"  # 数据转换
    ANALYSIS = "analysis"          # 数据分析
    REPORT = "report"              # 报告


class EdgeType(Enum):
    """边类型"""
    DATA_FLOW = "data_flow"         # 数据流
    TRANSFORMATION = "transformation"  # 转换
    DEPENDENCY = "dependency"       # 依赖
    DERIVATION = "derivation"       # 派生


@dataclass
class LineageNode:
    """血缘节点"""
    id: str
    name: str
    node_type: NodeType
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LineageEdge:
    """血缘边"""
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataLineage:
    """数据血缘信息"""
    dataset_id: str
    dataset_name: str
    nodes: List[LineageNode] = field(default_factory=list)
    edges: List[LineageEdge] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class LineageGraph:
    """血缘图"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.logger = logging.getLogger(__name__)
    
    def add_node(self, node: LineageNode):
        """添加节点"""
        self.graph.add_node(
            node.id,
            name=node.name,
            node_type=node.node_type.value,
            metadata=node.metadata,
            created_at=node.created_at,
            updated_at=node.updated_at
        )
    
    def add_edge(self, edge: LineageEdge):
        """添加边"""
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type.value,
            metadata=edge.metadata,
            created_at=edge.created_at
        )
    
    def get_upstream(self, node_id: str) -> List[str]:
        """获取上游节点"""
        return list(self.graph.predecessors(node_id))
    
    def get_downstream(self, node_id: str) -> List[str]:
        """获取下游节点"""
        return list(self.graph.successors(node_id))
    
    def get_ancestors(self, node_id: str) -> Set[str]:
        """获取所有祖先节点"""
        if HAS_NETWORKX:
            return set(nx.ancestors(self.graph, node_id))
        else:
            return self.graph.ancestors(node_id)
    
    def get_descendants(self, node_id: str) -> Set[str]:
        """获取所有后代节点"""
        if HAS_NETWORKX:
            return set(nx.descendants(self.graph, node_id))
        else:
            return self.graph.descendants(node_id)
    
    def find_paths(self, source_id: str, target_id: str) -> List[List[str]]:
        """查找从源到目标的所有路径"""
        if HAS_NETWORKX:
            try:
                return list(nx.all_simple_paths(self.graph, source_id, target_id))
            except nx.NetworkXNoPath:
                return []
        else:
            # 简单的路径查找实现
            def find_paths_recursive(current, target, visited, path):
                if current == target:
                    return [path + [current]]
                
                paths = []
                visited.add(current)
                
                for neighbor in self.graph.successors(current):
                    if neighbor not in visited:
                        paths.extend(find_paths_recursive(neighbor, target, visited.copy(), path + [current]))
                
                return paths
            
            return find_paths_recursive(source_id, target_id, set(), [])
    
    def get_impact_analysis(self, node_id: str) -> Dict[str, Any]:
        """影响分析"""
        descendants = self.get_descendants(node_id)
        ancestors = self.get_ancestors(node_id)
        
        return {
            "node_id": node_id,
            "direct_impact": len(self.get_downstream(node_id)),
            "total_impact": len(descendants),
            "dependencies": len(self.get_upstream(node_id)),
            "total_dependencies": len(ancestors),
            "impact_nodes": list(descendants),
            "dependency_nodes": list(ancestors)
        }


class DataLineageTracker:
    """数据血缘追踪器"""
    
    def __init__(self):
        self.lineage_graph = LineageGraph()
        self.lineage_data: Dict[str, DataLineage] = {}
        self.logger = logging.getLogger(__name__)
    
    def track_bars_lineage(self, symbol: str, exchange: Exchange, 
                          interval: Interval, start_date: str, end_date: str,
                          provider: str = "akshare") -> DataLineage:
        """追踪K线数据血缘"""
        dataset_id = f"bars_{symbol}_{exchange.value}_{interval.value}_{start_date}_{end_date}"
        
        # 创建血缘节点
        nodes = []
        edges = []
        
        # 1. 数据源节点
        source_node = LineageNode(
            id=f"source_{symbol}",
            name=f"数据源_{symbol}",
            node_type=NodeType.DATA_SOURCE,
            metadata={
                "symbol": symbol,
                "exchange": exchange.value,
                "interval": interval.value,
                "date_range": f"{start_date} to {end_date}"
            }
        )
        nodes.append(source_node)
        
        # 2. 数据提供者节点
        provider_node = LineageNode(
            id=f"provider_{provider}",
            name=f"数据提供者_{provider}",
            node_type=NodeType.PROVIDER,
            metadata={
                "provider": provider,
                "api_endpoint": f"{provider}_api"
            }
        )
        nodes.append(provider_node)
        
        # 3. 数据服务节点
        service_node = LineageNode(
            id=f"service_bars_{symbol}",
            name=f"K线服务_{symbol}",
            node_type=NodeType.SERVICE,
            metadata={
                "service_type": "bars",
                "symbol": symbol,
                "processing_time": datetime.now().isoformat()
            }
        )
        nodes.append(service_node)
        
        # 4. 数据存储节点
        store_node = LineageNode(
            id=f"store_bars_{symbol}",
            name=f"K线存储_{symbol}",
            node_type=NodeType.STORE,
            metadata={
                "store_type": "parquet",
                "symbol": symbol,
                "partition": f"{exchange.value}/{symbol}/{interval.value}"
            }
        )
        nodes.append(store_node)
        
        # 创建血缘边
        edges.extend([
            LineageEdge(
                source_id=source_node.id,
                target_id=provider_node.id,
                edge_type=EdgeType.DATA_FLOW,
                metadata={"data_type": "raw_data"}
            ),
            LineageEdge(
                source_id=provider_node.id,
                target_id=service_node.id,
                edge_type=EdgeType.DATA_FLOW,
                metadata={"data_type": "processed_data"}
            ),
            LineageEdge(
                source_id=service_node.id,
                target_id=store_node.id,
                edge_type=EdgeType.DATA_FLOW,
                metadata={"data_type": "stored_data"}
            )
        ])
        
        # 创建血缘信息
        lineage = DataLineage(
            dataset_id=dataset_id,
            dataset_name=f"K线数据_{symbol}",
            nodes=nodes,
            edges=edges
        )
        
        # 更新血缘图
        for node in nodes:
            self.lineage_graph.add_node(node)
        for edge in edges:
            self.lineage_graph.add_edge(edge)
        
        # 保存血缘信息
        self.lineage_data[dataset_id] = lineage
        
        return lineage
    
    def track_financial_lineage(self, symbol: str, exchange: Exchange,
                              start_date: str, end_date: str,
                              provider: str = "akshare") -> DataLineage:
        """追踪财务数据血缘"""
        dataset_id = f"financial_{symbol}_{exchange.value}_{start_date}_{end_date}"
        
        # 类似K线数据的血缘追踪逻辑
        nodes = []
        edges = []
        
        # 财务数据源节点
        source_node = LineageNode(
            id=f"source_financial_{symbol}",
            name=f"财务数据源_{symbol}",
            node_type=NodeType.DATA_SOURCE,
            metadata={
                "symbol": symbol,
                "exchange": exchange.value,
                "data_type": "financial"
            }
        )
        nodes.append(source_node)
        
        # 其他节点和边的创建逻辑...
        
        lineage = DataLineage(
            dataset_id=dataset_id,
            dataset_name=f"财务数据_{symbol}",
            nodes=nodes,
            edges=edges
        )
        
        self.lineage_data[dataset_id] = lineage
        return lineage
    
    def get_lineage_by_dataset(self, dataset_id: str) -> Optional[DataLineage]:
        """根据数据集ID获取血缘信息"""
        return self.lineage_data.get(dataset_id)
    
    def get_all_lineages(self) -> List[DataLineage]:
        """获取所有血缘信息"""
        return list(self.lineage_data.values())
    
    def search_lineage(self, keyword: str) -> List[DataLineage]:
        """搜索血缘信息"""
        results = []
        for lineage in self.lineage_data.values():
            if (keyword.lower() in lineage.dataset_name.lower() or
                keyword.lower() in lineage.dataset_id.lower()):
                results.append(lineage)
        return results


class ImpactAnalyzer:
    """影响分析器"""
    
    def __init__(self, lineage_tracker: DataLineageTracker):
        self.lineage_tracker = lineage_tracker
        self.logger = logging.getLogger(__name__)
    
    def analyze_data_impact(self, dataset_id: str) -> Dict[str, Any]:
        """分析数据影响"""
        lineage = self.lineage_tracker.get_lineage_by_dataset(dataset_id)
        if not lineage:
            return {"error": "数据集不存在"}
        
        # 找到存储节点
        store_nodes = [node for node in lineage.nodes 
                      if node.node_type == NodeType.STORE]
        
        if not store_nodes:
            return {"error": "未找到存储节点"}
        
        store_node = store_nodes[0]
        
        # 使用血缘图进行影响分析
        impact_analysis = self.lineage_tracker.lineage_graph.get_impact_analysis(store_node.id)
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": lineage.dataset_name,
            "impact_analysis": impact_analysis,
            "affected_datasets": self._get_affected_datasets(store_node.id),
            "recommendations": self._generate_impact_recommendations(impact_analysis)
        }
    
    def analyze_provider_impact(self, provider: str) -> Dict[str, Any]:
        """分析数据提供者影响"""
        affected_datasets = []
        
        for lineage in self.lineage_tracker.get_all_lineages():
            provider_nodes = [node for node in lineage.nodes 
                            if (node.node_type == NodeType.PROVIDER and 
                                provider in node.metadata.get("provider", ""))]
            
            if provider_nodes:
                affected_datasets.append({
                    "dataset_id": lineage.dataset_id,
                    "dataset_name": lineage.dataset_name,
                    "provider_node": provider_nodes[0].id
                })
        
        return {
            "provider": provider,
            "affected_datasets": affected_datasets,
            "total_impact": len(affected_datasets),
            "recommendations": self._generate_provider_recommendations(len(affected_datasets))
        }
    
    def _get_affected_datasets(self, node_id: str) -> List[str]:
        """获取受影响的数据集"""
        descendants = self.lineage_tracker.lineage_graph.get_descendants(node_id)
        affected = []
        
        for lineage in self.lineage_tracker.get_all_lineages():
            node_ids = [node.id for node in lineage.nodes]
            if any(node_id in descendants for node_id in node_ids):
                affected.append(lineage.dataset_id)
        
        return affected
    
    def _generate_impact_recommendations(self, impact_analysis: Dict[str, Any]) -> List[str]:
        """生成影响分析建议"""
        recommendations = []
        
        if impact_analysis["total_impact"] > 10:
            recommendations.append("该数据集影响范围较大，修改前请谨慎评估")
        
        if impact_analysis["total_dependencies"] > 5:
            recommendations.append("该数据集依赖较多，建议检查上游数据质量")
        
        if impact_analysis["direct_impact"] == 0:
            recommendations.append("该数据集未被其他组件使用，可以考虑归档")
        
        return recommendations
    
    def _generate_provider_recommendations(self, impact_count: int) -> List[str]:
        """生成数据提供者建议"""
        recommendations = []
        
        if impact_count > 20:
            recommendations.append("该数据提供者影响范围很大，建议建立备用方案")
        
        if impact_count == 0:
            recommendations.append("该数据提供者未被使用，可以考虑移除")
        
        return recommendations
