"""
GitHub 事件数据类型定义
"""
from typing import Optional, Any, Dict
from dataclasses import dataclass


@dataclass
class GitHubEventData:
    """GitHub 事件数据类"""
    id: str
    type: str
    actor: Dict[str, Any]
    repo: Dict[str, Any]
    payload: Dict[str, Any]
    public: bool
    created_at: str
    org: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubEventData':
        """从字典创建事件数据对象"""
        return cls(
            id=str(data.get("id")),
            type=data.get("type", ""),
            actor=data.get("actor", {}),
            repo=data.get("repo", {}),
            payload=data.get("payload", {}),
            public=data.get("public", True),
            created_at=data.get("created_at", ""),
            org=data.get("org")
        )
