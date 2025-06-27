"""
数据管理器 - 处理曲库数据的初始化和更新
"""
import asyncio
from pathlib import Path
from typing import Optional
from astrbot.api import logger

from .libraries.maimaidx_music import mai


class DataManager:
    """数据管理器，负责曲库数据的初始化和更新"""
    
    def __init__(self, plugin_root: Path):
        self.plugin_root = plugin_root
        self.is_initialized = False
        self.initialization_lock = asyncio.Lock()
    
    async def initialize_data(self, force: bool = False) -> bool:
        """初始化曲库数据"""
        if self.is_initialized and not force:
            logger.debug("数据已初始化，跳过")
            return True
        
        async with self.initialization_lock:
            try:
                logger.info("开始初始化曲库数据...")
                
                # 检查数据文件是否存在
                from .libraries.config import music_file, alias_file, chart_file
                
                if not music_file.exists() or not alias_file.exists() or not chart_file.exists() or force:
                    logger.info("检测到数据文件不存在或强制更新，正在初始化...")
                    await mai.get_music()
                    await mai.get_music_alias()
                    await mai.get_plate_json()
                    mai.guess()
                    logger.info("数据初始化完成！")
                else:
                    logger.info("检测到本地缓存文件，正在加载数据...")
                    await mai.get_music()
                    await mai.get_music_alias()
                    await mai.get_plate_json()
                    mai.guess()
                    logger.info("数据加载完成！")
                
                self.is_initialized = True
                return True
                
            except Exception as e:
                logger.error(f"数据初始化失败: {e}")
                return False
    
    async def update_data(self) -> bool:
        """更新曲库数据"""
        try:
            logger.info("开始更新曲库数据...")
            await mai.get_music()
            await mai.get_music_alias()
            await mai.get_plate_json()
            mai.guess()
            logger.info("数据更新完成！")
            return True
        except Exception as e:
            logger.error(f"数据更新失败: {e}")
            return False
    
    def is_data_ready(self) -> bool:
        """检查数据是否准备就绪"""
        return self.is_initialized and hasattr(mai, 'total_list') and mai.total_list is not None
    
    async def ensure_data_ready(self) -> bool:
        """确保数据准备就绪"""
        if not self.is_data_ready():
            return await self.initialize_data()
        return True 