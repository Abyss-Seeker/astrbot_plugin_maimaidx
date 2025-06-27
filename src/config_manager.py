"""
配置管理器 - 适配 AstrBot 配置系统
"""
from typing import Any, Dict, Optional
from astrbot.api import logger
from astrbot.api.star import Context


class ConfigManager:
    """配置管理器，适配 AstrBot 配置系统"""
    
    def __init__(self, context: Context):
        self.context = context
        self.config = context.get_config()
        self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        defaults = {
            "default_username": "default",
            "enable_image_output": True,
            "enable_text_output": True,
            "max_search_results": 10,
            "auto_update_data": False,
            "data_update_interval": 24
        }
        
        # 设置默认值
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                logger.debug(f"设置默认配置: {key} = {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            self.config.save_config()
            logger.debug("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_default_username(self) -> str:
        """获取默认用户名"""
        return self.get("default_username", "default")
    
    def is_image_output_enabled(self) -> bool:
        """是否启用图片输出"""
        return self.get("enable_image_output", True)
    
    def is_text_output_enabled(self) -> bool:
        """是否启用文本输出"""
        return self.get("enable_text_output", True)
    
    def get_max_search_results(self) -> int:
        """获取最大搜索结果数"""
        return self.get("max_search_results", 10)
    
    def is_auto_update_enabled(self) -> bool:
        """是否启用自动更新"""
        return self.get("auto_update_data", False)
    
    def get_update_interval(self) -> int:
        """获取更新间隔（小时）"""
        return self.get("data_update_interval", 24) 