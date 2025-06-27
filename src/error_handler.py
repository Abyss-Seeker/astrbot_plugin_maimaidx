"""
错误处理器 - 统一处理异常和错误消息
"""
from typing import Optional, Callable, Any
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent


class ErrorHandler:
    """错误处理器，统一处理异常和错误消息"""
    
    @staticmethod
    def handle_error(event: AstrMessageEvent, error: Exception, 
                    user_message: str = "操作失败", 
                    log_message: Optional[str] = None) -> str:
        """处理错误并返回用户友好的消息"""
        if log_message:
            logger.error(f"{log_message}: {error}")
        else:
            logger.error(f"操作失败: {error}")
        
        # 根据错误类型返回不同的用户消息
        if "网络" in str(error) or "连接" in str(error):
            return f"{user_message}：网络连接异常，请稍后重试"
        elif "未找到" in str(error) or "不存在" in str(error):
            return f"{user_message}：未找到相关数据"
        elif "权限" in str(error) or "认证" in str(error):
            return f"{user_message}：权限不足或认证失败"
        elif "格式" in str(error) or "参数" in str(error):
            return f"{user_message}：输入格式错误，请检查参数"
        else:
            return f"{user_message}：{str(error)}"
    
    @staticmethod
    async def safe_execute(event: AstrMessageEvent, func: Callable, 
                          *args, user_message: str = "操作失败", 
                          **kwargs) -> Any:
        """安全执行函数，自动处理异常"""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = ErrorHandler.handle_error(event, e, user_message)
            return error_msg
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """验证用户名格式"""
        if not username or not username.strip():
            return False, "用户名不能为空"
        
        username = username.strip()
        if len(username) > 50:
            return False, "用户名过长，请使用50个字符以内的用户名"
        
        # 检查是否包含特殊字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in username:
                return False, f"用户名不能包含特殊字符: {char}"
        
        return True, username
    
    @staticmethod
    def validate_song_id(song_id: str) -> tuple[bool, str]:
        """验证歌曲ID格式"""
        if not song_id or not song_id.strip():
            return False, "歌曲ID不能为空"
        
        song_id = song_id.strip()
        if not song_id.isdigit():
            return False, "歌曲ID必须是数字"
        
        return True, song_id
    
    @staticmethod
    def validate_difficulty(difficulty: str) -> tuple[bool, str]:
        """验证难度格式"""
        valid_difficulties = ['绿', '黄', '红', '紫', '白', 'Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
        
        if not difficulty or not difficulty.strip():
            return False, "难度不能为空"
        
        difficulty = difficulty.strip()
        if difficulty not in valid_difficulties:
            return False, f"难度必须是以下之一: {', '.join(valid_difficulties)}"
        
        return True, difficulty 