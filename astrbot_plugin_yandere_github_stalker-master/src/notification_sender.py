"""
通知发送器
"""
import os
from typing import List
from astrbot.api import logger
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.message.components import Image, Plain
from .notification_renderer import NotificationRenderer
from .github_event_data import GitHubEventData


class NotificationSender:
    def __init__(self, notification_renderer: NotificationRenderer, context, html_render):
        self.notification_renderer = notification_renderer
        self.context = context
        self.html_render = html_render
        logger.debug("Yandere Github Stalker: 通知发送器初始化完成")

    def _validate_session(self, session: str) -> bool:
        """
        验证会话ID格式是否正确
        :param session: 会话ID字符串
        :return: 是否合法
        """
        try:
            is_valid = len(session.split(":")) == 3
            logger.debug(
                f"Yandere Github Stalker: 验证会话ID {session} 格式：{'合法' if is_valid else '不合法'}")
            return is_valid
        except Exception as e:
            logger.warning(
                f"Yandere Github Stalker: 会话ID格式验证失败: {session}, 错误: {e}")
            return False

    async def _send_notification(self, message_chain: MessageChain, target_sessions: List[str]) -> bool:
        """
        发送通知到目标会话
        :return: 是否全部发送成功
        """
        success = True
        logger.debug(
            f"Yandere Github Stalker: 准备发送通知到 {len(target_sessions)} 个会话")

        for session in target_sessions:
            try:
                if not self._validate_session(session):
                    logger.warning(
                        f"Yandere Github Stalker: 跳过无效会话ID: {session}")
                    continue

                logger.debug(f"Yandere Github Stalker: 正在发送通知到会话: {session}")
                await self.context.send_message(session, message_chain)
                logger.debug(f"Yandere Github Stalker: 成功发送通知到会话: {session}")
            except Exception as e:
                logger.error(
                    f"Yandere Github Stalker: 发送通知到会话 {session} 失败: {e}")
                success = False

        logger.debug(
            f"Yandere Github Stalker: 通知发送{'成功' if success else '失败'}")
        return success

    async def send_image_notification(self, username: str, event: GitHubEventData, target_sessions: List[str]) -> bool:
        """
        发送图片通知
        :return: 是否发送成功
        """
        try:
            event_id = event.id
            event_type = event.type
            logger.debug(
                f"Yandere Github Stalker: 准备为用户 {username} 的事件 {event_id}（类型：{event_type}）生成图片通知")

            html_content = self.notification_renderer.render_html(
                username, event)
            logger.debug(f"Yandere Github Stalker: 已生成HTML内容，准备渲染图片")

            image_path = await self.html_render(
                tmpl=html_content,
                data={},
                return_url=False
            )
            if not image_path:
                logger.error("Yandere Github Stalker: 图片渲染失败，未获得图片路径")
                return False

            logger.debug(f"Yandere Github Stalker: 图片已渲染，路径：{image_path}")
            img = Image.fromFileSystem(image_path)
            if not img:
                logger.error(
                    f"Yandere Github Stalker: 无法从路径 {image_path} 加载图片")
                return False

            logger.debug("Yandere Github Stalker: 图片加载成功，准备发送通知")
            success = await self._send_notification(MessageChain([img]), target_sessions)

            # 清理临时文件
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.debug(
                        f"Yandere Github Stalker: 已清理临时图片文件: {image_path}")
                except Exception as e:
                    logger.warning(f"Yandere Github Stalker: 删除图片文件失败: {e}")

            return success
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 发送图片通知失败: {e}")
            return False

    async def send_text_notification(self, username: str, event: GitHubEventData, target_sessions: List[str]) -> bool:
        """
        发送文本通知
        :return: 是否发送成功
        """
        try:
            event_id = event.id
            event_type = event.type
            logger.debug(
                f"Yandere Github Stalker: 准备为用户 {username} 的事件 {event_id}（类型：{event_type}）生成文本通知")

            text = self.notification_renderer.create_text_notification(
                username, event)
            logger.debug("Yandere Github Stalker: 文本通知生成成功，准备发送")

            success = await self._send_notification(MessageChain([Plain(text)]), target_sessions)
            if success:
                logger.debug(
                    f"Yandere Github Stalker: 文本通知发送成功，事件ID：{event_id}")
            else:
                logger.warning(
                    f"Yandere Github Stalker: 文本通知发送失败，事件ID：{event_id}")
            return success
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 发送文本通知失败: {e}")
            return False
