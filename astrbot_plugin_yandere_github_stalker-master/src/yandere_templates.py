"""
病娇风格的GitHub事件语言模板
"""
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .github_event_data import GitHubEventData


class YandereTemplates:
    def __init__(self, custom_templates: Dict[str, Any] = None):
        """
        初始化模板
        :param custom_templates: 用户自定义的模板，会覆盖默认模板
        """
        self.templates = self._load_default_templates()
        if custom_templates:
            self._merge_templates(custom_templates)

    def _load_default_templates(self) -> Dict[str, Any]:
        """
        从配置schema加载默认模板
        """
        schema_path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), '_conf_schema.json')
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            # 从schema中提取所有事件的默认模板
            templates = {}
            for key, value in schema.items():
                if key.startswith('monitor_') and isinstance(value, dict):
                    event_type = self._convert_monitor_to_event_type(key)
                    if 'items' in value:
                        templates[event_type] = self._extract_default_templates(
                            value['items'])
            return templates
        except Exception as e:
            raise RuntimeError(
                f"[YandereTemplates] 加载schema失败：{e}，请检查_conf_schema.json配置文件！")

    def _convert_monitor_to_event_type(self, monitor_key: str) -> str:
        """
        将monitor_配置键转换为事件类型
        例如: monitor_push -> PushEvent
        """
        # 移除 "monitor_" 前缀
        event_type = monitor_key[8:]

        # 特殊情况处理
        event_type_mapping = {
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
            'issue_comment': 'IssueCommentEvent',  # 添加 issue_comment 映射
            'pull_request_review': 'PullRequestReviewEvent'  # 添加 PR Review 映射
        }

        return event_type_mapping.get(event_type, event_type.capitalize() + 'Event')

    def _extract_default_templates(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        从schema字段中提取默认模板
        """
        templates = {}
        for key, value in fields.items():
            if isinstance(value, dict) and 'default' in value:
                templates[key] = value['default']
        return templates

    def _merge_templates(self, custom_templates: Dict[str, Any]):
        """
        合并自定义模板
        :param custom_templates: 用户自定义的模板
        """
        for event_type, templates in custom_templates.items():
            if event_type in self.templates:
                if isinstance(self.templates[event_type], dict):
                    self.templates[event_type].update(templates)
                else:
                    self.templates[event_type] = templates
            else:
                self.templates[event_type] = templates

    def get_template(self, event_type: str, action: Optional[str] = None) -> str:
        """
        获取指定事件类型的模板
        :param event_type: 事件类型
        :param action: 事件动作（如果有）
        :return: 模板字符串
        """
        template_data = self.templates.get(event_type)
        if not template_data:
            raise ValueError(
                f"[YandereTemplates] {event_type} 模板缺失，请在schema中配置！")
        if isinstance(template_data, dict):
            if action:
                if action in template_data:
                    return template_data[action]
                else:
                    raise ValueError(
                        f"[YandereTemplates] {event_type} 的 {action} 模板缺失，请在schema中配置！")
            if "template" in template_data:
                return template_data["template"]
            else:
                raise ValueError(
                    f"[YandereTemplates] {event_type} 的template模板缺失，请在schema中配置！")
        return template_data

    def _format_push_event(self, event: GitHubEventData) -> str:
        """处理Push事件"""
        commits = event.payload.get("commits", [])
        template_vars = {
            "username": event.actor["login"],
            "repo": event.repo["name"],
            "commit_count": len(commits)
        }
        template_data = self.templates.get("PushEvent")
        if not template_data or "template" not in template_data or "commit_message" not in template_data:
            raise ValueError(
                "[YandereTemplates] PushEvent模板缺失，请在schema中配置PushEvent的template和commit_message！")
        message = template_data["template"].format(**template_vars)
        if commits:
            commit_template = template_data["commit_message"]
            for commit in commits[:3]:  # 最多显示3个提交
                template_vars["message"] = commit["message"]
                message += "\n" + commit_template.format(**template_vars)
            if len(commits) > 3:
                message += "\n还有更多提交...让我慢慢看完♥"
        return message

    def _format_ref_event(self, event: GitHubEventData) -> str:
        """处理Create/Delete事件"""
        return self.get_template(event.type).format(
            username=event.actor["login"],
            repo=event.repo["name"],
            ref_type=event.payload.get("ref_type", ""),
            ref=event.payload.get("ref", "")
        )

    def _format_issue_or_pr_event(self, event: GitHubEventData) -> str:
        """处理Issue和PR事件"""
        action = event.payload.get("action", "")
        if event.type == "IssuesEvent":
            title = event.payload.get("issue", {}).get("title", "")
        else:
            title = event.payload.get("pull_request", {}).get("title", "")
        return self.get_template(event.type, action).format(
            username=event.actor["login"],
            repo=event.repo["name"],
            title=title
        )

    def _format_comment_event(self, event: GitHubEventData) -> str:
        """处理评论事件，兼容 CommitCommentEvent 和 IssueCommentEvent"""
        comment = event.payload.get("comment", {})
        # 判断是否为 IssueCommentEvent
        if event.type == "IssueCommentEvent":
            issue_title = event.payload.get("issue", {}).get("title", "")
            return self.get_template(event.type).format(
                username=event.actor["login"],
                repo=event.repo["name"],
                issue_title=issue_title,
                comment=comment.get("body", "")
            )
        else:
            # CommitCommentEvent
            return self.get_template(event.type).format(
                username=event.actor["login"],
                repo=event.repo["name"],
                commit_id=comment.get("commit_id", "")[:7],
                comment=comment.get("body", "")
            )

    def _format_member_event(self, event: GitHubEventData) -> str:
        """处理成员事件"""
        return self.get_template(event.type).format(
            username=event.actor["login"],
            repo=event.repo["name"],
            target=event.payload.get("member", {}).get("login", "某个人")
        )

    def _format_simple_event(self, event: GitHubEventData) -> str:
        """处理简单事件（只需要用户名和仓库名）"""
        return self.get_template(event.type).format(
            username=event.actor["login"],
            repo=event.repo["name"]
        )

    def _format_pr_review_event(self, event: GitHubEventData) -> str:
        """处理PR Review事件"""
        review_state = event.payload.get("review", {}).get("state", "").lower()
        title = event.payload.get("pull_request", {}).get("title", "")

        # 将review状态映射为更友好的描述
        state_mapping = {
            "approved": "同意了",
            "changes_requested": "要求修改",
            "commented": "评论了",
            "dismissed": "忽略了",
            "pending": "正在审查"
        }
        state = state_mapping.get(review_state, review_state)

        return self.get_template("PullRequestReviewEvent", "review").format(
            username=event.actor["login"],
            title=title,
            state=state
        )

    def format_event_message(self, event: GitHubEventData) -> str:
        """
        格式化事件消息
        :param event: GitHub事件数据
        :return: 格式化后的消息
        """
        match event.type:
            case "PushEvent":
                return self._format_push_event(event)

            case "CreateEvent" | "DeleteEvent":
                return self._format_ref_event(event)

            case "IssuesEvent" | "PullRequestEvent":
                return self._format_issue_or_pr_event(event)

            case "PullRequestReviewEvent":
                return self._format_pr_review_event(event)

            case "CommitCommentEvent" | "IssueCommentEvent":
                return self._format_comment_event(event)

            case "MemberEvent":
                return self._format_member_event(event)

            case "WatchEvent" | "ForkEvent" | "PublicEvent":
                return self._format_simple_event(event)

            case _:
                # 未知事件类型的默认处理
                return self._format_simple_event(event)
