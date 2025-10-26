# qp/data/stores/config_loader.py
"""数据分层配置加载器"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .data_layers_models import DataLayerConfig


class DataLayerConfigLoader:
    """数据分层配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 从项目根目录查找配置文件
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        
        # 可能的配置文件路径
        possible_paths = [
            project_root / "configs" / "data_config.yaml",
            project_root / "configs" / "data_layers.yaml",
            project_root / "data_config.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # 如果都找不到，返回默认路径
        return str(project_root / "configs" / "data_config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")
    
    def get_data_layer_config(self) -> DataLayerConfig:
        """
        获取数据分层配置
        
        Returns:
            DataLayerConfig: 数据分层配置对象
        """
        data_layers = self.config_data.get('data_layers', {})
        
        # 提取各层配置
        ods_config = data_layers.get('ods', {})
        dwd_config = data_layers.get('dwd', {})
        dws_config = data_layers.get('dws', {})
        
        return DataLayerConfig(
            # ODS层配置
            ods_root=ods_config.get('root', 'data/ods'),
            ods_retention_days=ods_config.get('retention_days', 3650),
            ods_compression=ods_config.get('compression', 'snappy'),
            ods_partition_by=ods_config.get('partition_by', ['market', 'date', 'symbol']),
            
            # DWD层配置
            dwd_root=dwd_config.get('root', 'data/dwd'),
            dwd_retention_days=dwd_config.get('retention_days', 1825),
            dwd_compression=dwd_config.get('compression', 'snappy'),
            dwd_partition_by=dwd_config.get('partition_by', ['market', 'symbol']),
            
            # DWS层配置
            dws_root=dws_config.get('root', 'data/dws'),
            dws_retention_days=dws_config.get('retention_days', 1095),
            dws_compression=dws_config.get('compression', 'snappy'),
            dws_partition_by=dws_config.get('partition_by', ['market', 'symbol']),
        )
    
    def get_legacy_config(self) -> Dict[str, Any]:
        """
        获取传统配置（向后兼容）
        
        Returns:
            Dict[str, Any]: 传统配置字典
        """
        return {
            'root': self.config_data.get('root', './data/history_root'),
            'provider': self.config_data.get('provider', 'akshare'),
            'adjust': self.config_data.get('adjust', 'qfq'),
            'interval': self.config_data.get('interval', '1d'),
            'start': self.config_data.get('start', '2024-01-01'),
            'end': self.config_data.get('end', 'today'),
            'concurrency': self.config_data.get('concurrency', 2),
            'retry': self.config_data.get('retry', 2),
            'tushare_token': self.config_data.get('tushare_token'),
        }
    
    def reload_config(self):
        """重新加载配置文件"""
        self.config_data = self._load_config()
    
    def save_config(self, config_data: Dict[str, Any]):
        """
        保存配置到文件
        
        Args:
            config_data: 配置数据
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            self.config_data = config_data
        except Exception as e:
            raise RuntimeError(f"保存配置文件失败: {e}")


def load_data_layer_config(config_path: Optional[str] = None) -> DataLayerConfig:
    """
    便捷函数：加载数据分层配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        DataLayerConfig: 数据分层配置对象
    """
    loader = DataLayerConfigLoader(config_path)
    return loader.get_data_layer_config()


def load_legacy_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    便捷函数：加载传统配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict[str, Any]: 传统配置字典
    """
    loader = DataLayerConfigLoader(config_path)
    return loader.get_legacy_config()


# 示例用法
if __name__ == "__main__":
    # 加载数据分层配置
    layer_config = load_data_layer_config()
    print("数据分层配置:")
    print(f"  ODS根目录: {layer_config.ods_root}")
    print(f"  DWD根目录: {layer_config.dwd_root}")
    print(f"  DWS根目录: {layer_config.dws_root}")
    
    # 加载传统配置
    legacy_config = load_legacy_config()
    print("\n传统配置:")
    print(f"  根目录: {legacy_config['root']}")
    print(f"  数据源: {legacy_config['provider']}")
    print(f"  复权方式: {legacy_config['adjust']}")
