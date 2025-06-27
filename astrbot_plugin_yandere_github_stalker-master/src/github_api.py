"""
GitHub API related functionality
"""
import aiohttp
from typing import Optional, List
from astrbot.api import logger
from .config_manager import ConfigManager
from .github_event_data import GitHubEventData


class GitHubAPI:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.token = self.config_manager.get_github_token().strip()
        self.timeout = self.config_manager.get_github_api_timeout()
        self.user_agent = self.config_manager.get_github_api_user_agent()

        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'
            logger.debug("Yandere Github Stalker: GitHub API已配置Token")
        else:
            logger.warning("Yandere Github Stalker: 未配置GitHub Token，API访问可能受限")

    async def get_user_events(self, username: str) -> Optional[List[GitHubEventData]]:
        """获取用户的GitHub活动"""
        try:
            url = f"https://api.github.com/users/{username}/events"
            logger.debug(
                f"Yandere Github Stalker: 正在获取用户 {username} 的活动，URL: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        events_data = await response.json()
                        events = [GitHubEventData.from_dict(
                            event) for event in events_data]
                        logger.debug(
                            f"Yandere Github Stalker: 成功获取用户 {username} 的活动，共 {len(events)} 条")
                        if events:
                            logger.debug(
                                f"Yandere Github Stalker: 最新5条事件类型：{[e.type for e in events[:5]]}")
                        return events
                    elif response.status == 404:
                        logger.warning(
                            f"Yandere Github Stalker: 用户 {username} 不存在")
                        return None
                    else:
                        response_text = await response.text()
                        logger.warning(
                            f"Yandere Github Stalker: GitHub API返回状态码 {response.status}，响应：{response_text}")
                        return None
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 获取用户 {username} 活动失败: {e}")
            return None

    async def get_user_info(self, username: str) -> Optional[dict]:
        """获取用户信息"""
        try:
            url = f"https://api.github.com/users/{username}"
            logger.debug(f"Yandere Github Stalker: 正在获取用户 {username} 的信息")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        logger.debug(
                            f"Yandere Github Stalker: 成功获取用户 {username} 的信息")
                        return user_info
                    else:
                        response_text = await response.text()
                        logger.warning(
                            f"Yandere Github Stalker: 获取用户信息失败，状态码: {response.status}，响应：{response_text}")
                        return None
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 获取用户信息失败: {e}")
            return None
