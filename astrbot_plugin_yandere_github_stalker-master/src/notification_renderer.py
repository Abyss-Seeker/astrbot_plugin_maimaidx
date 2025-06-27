"""
Notification rendering functionality
"""
from typing import Dict, Any
from datetime import datetime
import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .yandere_templates import YandereTemplates
from .config_manager import ConfigManager
from .github_event_data import GitHubEventData


class NotificationRenderer:
    def __init__(self, config_manager: ConfigManager):
        """初始化渲染器"""
        self.config_manager = config_manager
        self.yandere_templates = YandereTemplates(self.config_manager.get_custom_templates())
        self.event_limit = self.config_manager.get_notification_event_limit()

        # 设置Jinja2环境
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        os.makedirs(template_dir, exist_ok=True)
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def get_event_description(self, event: GitHubEventData) -> str:
        """根据事件类型生成描述"""
        return self.yandere_templates.format_event_message(event)

    def render_html(self, username: str, event: GitHubEventData) -> str:
        """
        渲染HTML内容
        :param username: 用户名
        :param event: 事件（单个事件）
        :return: 渲染后的HTML字符串
        """
        template = self.jinja_env.get_template('notification.html')
        # 处理事件数据
        created_at = datetime.strptime(
            event.created_at,
            "%Y-%m-%dT%H:%M:%SZ"
        ).strftime("%Y-%m-%d %H:%M:%S")
        processed_event = {
            'type': event.type,
            'repo_name': event.repo['name'],
            'description': self.get_event_description(event),
            'created_at': created_at
        }
        # 渲染模板
        return template.render(
            username=username,
            events=[processed_event]  # 保持模板兼容性
        )

    def create_text_notification(self, username: str, event: GitHubEventData) -> str:
        """创建文本通知内容（单个事件）"""
        yandere = self.yandere_templates
        # 从schema加载默认模板
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_conf_schema.json')
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            # 使用配置中的通知模板
            notification_template = schema.get('notification_template', {}).get('default', "啊啊啊！{username}君又有新的动态了呢！♥\n\n")
        except Exception:
            # 如果无法读取schema，使用默认模板
            notification_template = "啊啊啊！{username}君又有新的动态了呢！♥\n\n"

        message = notification_template.format(username=username)
        message += f"{yandere.format_event_message(event)}\n\n"
        return message
