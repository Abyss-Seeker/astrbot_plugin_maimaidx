import os
import asyncio
from typing import Union, Optional
from PIL import Image
import io

class OutputManager:
    """AstrBot 插件输出管理器"""
    
    def __init__(self):
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def send_text(self, event, text: str) -> str:
        """
        发送文本消息
        
        Args:
            event: AstrBot 事件对象
            text: 要发送的文本
        Returns:
            str: 发送的消息内容
        """
        # 在AstrBot中，直接返回文本即可
        return text
    
    async def send_image(self, event, image: Image.Image, filename: str, description: str = "") -> str:
        """
        发送图片消息
        
        Args:
            event: AstrBot 事件对象
            image: PIL图片对象
            filename: 文件名
            description: 图片描述
        Returns:
            str: 发送的消息内容
        """
        try:
            # 保存图片到输出目录
            filepath = os.path.join(self.output_dir, filename)
            image.save(filepath)
            
            # 在AstrBot中，返回图片路径和描述
            if description:
                return f"[图片] {description}\n文件路径: {filepath}"
            else:
                return f"[图片] {filename}\n文件路径: {filepath}"
        except Exception as e:
            return f"图片发送失败: {str(e)}"
    
    async def send_file(self, event, filepath: str, description: str = "") -> str:
        """
        发送文件消息
        
        Args:
            event: AstrBot 事件对象
            filepath: 文件路径
            description: 文件描述
        Returns:
            str: 发送的消息内容
        """
        if os.path.exists(filepath):
            if description:
                return f"[文件] {description}\n文件路径: {filepath}"
            else:
                return f"[文件] {os.path.basename(filepath)}\n文件路径: {filepath}"
        else:
            return f"文件不存在: {filepath}"
    
    def save_image(self, image: Image.Image, filename: str) -> str:
        """
        保存图片到输出目录
        
        Args:
            image: PIL图片对象
            filename: 文件名
        Returns:
            str: 保存的文件路径
        """
        filepath = os.path.join(self.output_dir, filename)
        image.save(filepath)
        return filepath
    
    def get_output_path(self, filename: str) -> str:
        """
        获取输出文件路径
        
        Args:
            filename: 文件名
        Returns:
            str: 完整的文件路径
        """
        return os.path.join(self.output_dir, filename) 