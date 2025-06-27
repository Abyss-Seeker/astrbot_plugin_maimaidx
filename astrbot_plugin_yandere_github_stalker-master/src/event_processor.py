"""
事件处理器
"""
from typing import List
from datetime import datetime
from astrbot.api import logger
from .pushed_event_id_manager import PushedEventIdManager
from .github_event_data import GitHubEventData


class EventProcessor:
    def __init__(self, event_limit: int, pushed_event_ids_manager: PushedEventIdManager, config_manager):
        self.event_limit = event_limit
        self.pushed_event_ids_manager = pushed_event_ids_manager
        self.config_manager = config_manager
        logger.debug(f"Yandere Github Stalker: 事件处理器初始化，事件限制：{event_limit}")

    async def process_events(self, events: List[GitHubEventData], username: str) -> List[GitHubEventData]:
        """处理事件列表，返回需要推送的新事件
        
        Args:
            events: 要处理的事件列表
            username: GitHub用户名
        """
        logger.debug(f"Yandere Github Stalker: 处理用户 {username} 的 {len(events)} 条排序后的事件")

        if not events:
            return []

        # 获取最后一次推送的事件时间
        last_pushed_time = await self.pushed_event_ids_manager.get_last_pushed_time(username)
        if last_pushed_time:
            logger.debug(f"Yandere Github Stalker: 用户 {username} 上次推送时间：{last_pushed_time}")
        else:
            logger.debug(f"Yandere Github Stalker: 用户 {username} 没有找到上次推送时间记录")

        earliest_event = events[-1]  # events 按时间倒序排列
        latest_event = events[0]
        logger.debug(
            f"Yandere Github Stalker: 最早事件时间：{earliest_event.created_at}，最新事件时间：{latest_event.created_at}")

        try:
            # 获取当前已推送的事件数量
            pushed_count = await self.pushed_event_ids_manager.get_pushed_event_count(username)
            logger.debug(f"Yandere Github Stalker: 用户 {username} 当前已推送事件数：{pushed_count}")
        except Exception as e:
            logger.warning(f"Yandere Github Stalker: 获取已推送事件数量失败: {str(e)}，继续处理")
            pushed_count = 0

        # 获取事件限制数量
        event_limit = self.config_manager.get_notification_event_limit()
        logger.debug(f"Yandere Github Stalker: 事件限制数量：{event_limit}")

        new_events = []
        for event in events:
            event_id = event.id
            event_type = event.type
            event_time = event.created_at

            try:
                # 将事件时间转换为datetime对象以进行比较
                event_datetime = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%SZ")

                # 如果有上次推送时间，且当前事件时间早于或等于上次推送时间，则跳过
                if last_pushed_time and event_datetime <= last_pushed_time:
                    continue

                logger.debug(
                    f"Yandere Github Stalker: 检查事件 {event_id}，类型：{event_type}，时间：{event_time}")

                # 检查事件是否已经推送过
                is_pushed = await self.pushed_event_ids_manager.is_event_pushed(event_id, username)
                logger.debug(
                    f"Yandere Github Stalker: 检查事件ID {event_id} 是否存在: {is_pushed}，当前总数：{pushed_count}")

                if not is_pushed:
                    logger.debug(
                        f"Yandere Github Stalker: 发现新事件 {event_id}，类型：{event_type}")
                    new_events.append(event)

                    # 检查是否达到事件限制
                    if event_limit > 0 and len(new_events) >= event_limit:
                        logger.debug(
                            f"Yandere Github Stalker: 达到事件限制 {event_limit}，停止处理")
                        break
            except Exception as e:
                logger.warning(f"Yandere Github Stalker: 处理事件 {event_id} 时出错: {str(e)}，跳过此事件")
                continue

        logger.info(
            f"Yandere Github Stalker: 发现 {len(new_events)} 条新事件，类型：{[e.type for e in new_events]} ")
        return new_events[:event_limit] if event_limit > 0 else new_events

    async def mark_event_as_pushed(self, event_id: str, username: str, event_time: str = None) -> bool:
        """将事件标记为已推送
        Args:
            event_id: 事件ID
            username: GitHub用户名
            event_time: 事件发生时间（ISO格式字符串）
        Returns:
            bool: 标记是否成功
        """
        success = await self.pushed_event_ids_manager.add_pushed_event_id(event_id, username, event_time)
        if success:
            logger.debug(f"Yandere Github Stalker: 已将事件 {event_id} (用户: {username}) 标记为已推送")
        else:
            logger.warning(f"Yandere Github Stalker: 事件 {event_id} (用户: {username}) 标记失败，但继续处理其他事件")
        return success

    async def mark_event_as_ignored(self, event_id: str, username: str, event_time: str = None) -> bool:
        """将事件标记为已忽略（例如因为模板缺失）
        Args:
            event_id: 事件ID
            username: GitHub用户名
            event_time: 事件发生时间（ISO格式字符串）
        Returns:
            bool: 标记是否成功
        """
        success = await self.pushed_event_ids_manager.add_pushed_event_id(event_id, username, event_time)
        if success:
            logger.debug(f"Yandere Github Stalker: 已将事件 {event_id} (用户: {username}) 标记为已忽略")
        else:
            logger.warning(f"Yandere Github Stalker: 事件 {event_id} (用户: {username}) 忽略标记失败，但继续处理其他事件")
        return success
