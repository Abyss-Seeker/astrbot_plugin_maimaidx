"""
配置管理器
"""
from typing import Any, List, Dict
from astrbot.api import AstrBotConfig


class ConfigManager:
    # 事件类型映射
    EVENT_TYPE_MAPPING = {
        'push': 'PushEvent',
        'issues': 'IssuesEvent',
        'pull_request': 'PullRequestEvent',
        'star': 'WatchEvent',  # GitHub API 中 Star 事件实际上是 WatchEvent
        'fork': 'ForkEvent',
        'create': 'CreateEvent',
        'delete': 'DeleteEvent',
        'public': 'PublicEvent',
        'member': 'MemberEvent',
        'commit_comment': 'CommitCommentEvent',
        'issue_comment': 'IssueCommentEvent'
    }

    def __init__(self, config: AstrBotConfig):
        """初始化配置管理器
        
        Args:
            config: AstrBot配置对象
        """
        self.config = config
        self.data_dir = config.get("data_dir", "")

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)

    def update_config(self, key: str, value: Any):
        """更新配置项
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self.config.update({key: value})

    def get_data_dir(self) -> str:
        """获取数据目录路径
        
        Returns:
            str: 数据目录路径
        """
        return self.data_dir

    def get_monitored_users(self) -> List[str]:
        """获取要监控的用户列表
        
        Returns:
            List[str]: 用户名列表
        """
        return self.config.get("monitored_users", [])

    def get_target_sessions(self) -> List[str]:
        """获取目标会话列表
        
        Returns:
            List[str]: 会话ID列表
        """
        return self.config.get("target_sessions", [])

    def get_check_interval(self) -> int:
        """获取检查间隔（秒）
        
        Returns:
            int: 检查间隔时间，默认300秒（5分钟）
        """
        return self.config.get("check_interval", 300)

    def get_notification_event_limit(self) -> int:
        """获取每次检查的事件限制数量
        
        Returns:
            int: 事件限制数量，默认2条，0表示不限制
        """
        return self.config.get("notification_event_limit", 2)

    def get_event_retention_days(self) -> int:
        """获取事件保留天数
        
        Returns:
            int: 事件保留天数，默认7天
        """
        return self.config.get("event_retention_days", 7)

    def is_image_notification_enabled(self) -> bool:
        """是否启用图片通知
        
        Returns:
            bool: 是否启用图片通知，默认True
        """
        return self.config.get("enable_image_notification", True)

    def is_startup_notification_enabled(self) -> bool:
        """是否启用启动通知
        
        Returns:
            bool: 是否在插件启动时发送通知，默认True
        """
        return self.config.get("enable_startup_notification", True)

    def get_notification_template(self) -> str:
        """获取通知开头模板
        
        Returns:
            str: 通知开头模板文本
        """
        return self.config.get("notification_template", 
            "啊啊啊！{username}君又有新的动态了呢！♥\n\n")

    def get_notification_remaining_template(self) -> str:
        """获取剩余动态提示模板
        
        Returns:
            str: 剩余动态提示模板文本
        """
        return self.config.get("notification_remaining_template", 
            "还有{count}个动态...{username}君真是太活跃了呢 ♥")

    def get_custom_templates(self) -> Dict[str, Any]:
        """获取自定义模板配置
        
        Returns:
            Dict[str, Any]: 事件类型到模板配置的映射
        """
        custom_templates = {}
        for key, value in self.config.items():
            if key.startswith('monitor_') and isinstance(value, dict) and value.get('enabled'):
                event_type = self._convert_monitor_to_event_type(
                    key[8:])  # 移除 "monitor_" 前缀
                custom_templates[event_type] = {
                    k: v for k, v in value.items() if k != 'enabled'}
        return custom_templates

    def _convert_monitor_to_event_type(self, event_type: str) -> str:
        """将monitor_配置键转换为事件类型
        
        Args:
            event_type: 配置键中的事件类型名
            
        Returns:
            str: GitHub API的事件类型名
        """
        return self.EVENT_TYPE_MAPPING.get(event_type, event_type.capitalize() + 'Event')

    def get_github_api_timeout(self) -> int:
        """获取GitHub API超时时间
        
        Returns:
            int: 超时时间（秒），默认10秒
        """
        return self.config.get("github_api_timeout", 10)

    def get_github_api_user_agent(self) -> str:
        """获取GitHub API User-Agent
        
        Returns:
            str: User-Agent字符串
        """
        return self.config.get("github_api_user_agent", "Yandere-Github-Stalker/1.0.0")

    def get_github_token(self) -> str:
        """获取GitHub Token
        
        Returns:
            str: GitHub Personal Access Token
        """
        return self.config.get("github_token", "")
