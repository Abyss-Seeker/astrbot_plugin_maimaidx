"""
Yandere Github Stalker Plugin
"""
import asyncio
import json
import os
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.star.filter.permission import PermissionType
from datetime import datetime

from .src.github_api import GitHubAPI
from .src.notification_renderer import NotificationRenderer
from .src.pushed_event_id_manager import PushedEventIdManager
from .src.event_processor import EventProcessor
from .src.notification_sender import NotificationSender
from .src.config_manager import ConfigManager
from .src.github_event_data import GitHubEventData


@register("astrbot_plugin_yandere_github_stalker", "SXP-Simon", "Yandere Github Stalker Plugin", "1.1.0")
class YandereGithubStalker(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        """初始化插件"""
        super().__init__(context)

        # 初始化组件
        self.config_manager = ConfigManager(config)
        self.github_api = GitHubAPI(self.config_manager)

        # 初始化事件ID管理器
        os.makedirs("data", exist_ok=True)
        self.pushed_event_ids_path = os.path.join(
            "data", "github_pushed_event_ids.json")
        self.pushed_event_ids_manager = PushedEventIdManager(context)

        # 初始化其他组件
        self.event_processor = EventProcessor(
            event_limit=self.config_manager.get_notification_event_limit(),
            pushed_event_ids_manager=self.pushed_event_ids_manager,
            config_manager=self.config_manager
        )
        self.notification_renderer = NotificationRenderer(self.config_manager)
        self.notification_sender = NotificationSender(
            notification_renderer=self.notification_renderer,
            context=self.context,
            html_render=self.html_render
        )

        # 初始化状态
        self.is_monitoring = False
        self.monitoring_task = None
        self.last_cleanup_time = datetime.now()  # 添加上次清理时间记录

        # 启动监控任务
        asyncio.create_task(self.start())
        logger.debug(
            f"Yandere Github Stalker: 插件初始化完成，事件限制：{self.config_manager.get_notification_event_limit()}")

    def _prepare_command(self, event: AstrMessageEvent):
        """准备命令执行环境"""
        event.stop_event()
        event.should_call_llm(False)

    @filter.command_group("yandere")
    def yandere_group(self):
        """Yandere Github Stalker 命令组"""
        pass

    @yandere_group.command("test")
    async def test_notification(self, event: AstrMessageEvent):
        """测试GitHub活动通知图片生成"""
        try:
            self._prepare_command(event)

            test_data_path = os.path.join(
                os.path.dirname(__file__), "test_data.json")
            if not os.path.exists(test_data_path):
                return event.plain_result("❌ 测试数据文件不存在").stop_event()

            with open(test_data_path, "r", encoding="utf-8") as f:
                test_events = json.load(f)

            test_events = sorted(test_events, key=lambda x: x.get(
                "created_at", ""), reverse=True)[:3]
            username = test_events[0].get("actor", {}).get(
                "login", "test") if test_events else "test"

            if self.config_manager.is_image_notification_enabled():
                for test_event in test_events:
                    success = await self.notification_sender.send_image_notification(
                        username,
                        GitHubEventData.from_dict(test_event),
                        [event.unified_msg_origin]
                    )
                    if not success:
                        return event.plain_result("❌ 图片生成失败").stop_event()
            else:
                for test_event in test_events:
                    success = await self.notification_sender.send_text_notification(
                        username,
                        test_event,
                        [event.unified_msg_origin]
                    )
                    if not success:
                        return event.plain_result("❌ 文本通知发送失败").stop_event()

            return event.plain_result("✅ 测试完成").stop_event()
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 测试通知失败: {e}")
            return event.plain_result(f"❌ 测试失败: {e}").stop_event()

    @yandere_group.command("status")
    async def github_status(self, event: AstrMessageEvent):
        """获取监控状态"""
        try:
            self._prepare_command(event)

            # 获取基本信息
            monitored_users = self.config_manager.get_monitored_users()
            total_events = len(self.pushed_event_ids_manager)
            is_monitoring = self.is_monitoring

            # 构建状态信息
            status_lines = [
                "📊 Yandere Github Stalker 状态",
                f"├── 监控状态：{'🟢 运行中' if is_monitoring else '🔴 已停止'}",
                f"├── 总事件数：{total_events}",
                "└── 监控列表："
            ]

            # 添加用户列表
            if monitored_users:
                for i, user in enumerate(monitored_users, 1):
                    try:
                        # 获取每个用户的事件数
                        event_count = await self.pushed_event_ids_manager.get_pushed_event_count(user)
                        prefix = "└──" if i == len(monitored_users) else "├──"
                        status_lines.append(f"    {prefix} {user}（{event_count}条事件）")
                    except Exception as e:
                        logger.error(f"获取用户 {user} 事件数量失败: {e}")
                        prefix = "└──" if i == len(monitored_users) else "├──"
                        status_lines.append(f"    {prefix} {user}（获取事件数失败）")
            else:
                status_lines.append("    └── 暂无监控用户")

            # 发送状态信息
            return event.plain_result("\n".join(status_lines)).stop_event()

        except Exception as e:
            logger.error(f"获取监控状态失败: {e}")
            return event.plain_result("❌ 获取监控状态失败，请查看日志").stop_event()

    @yandere_group.command("add")
    async def add_user(self, event: AstrMessageEvent, username: str):
        """添加一个GitHub用户到视奸列表"""
        self._prepare_command(event)

        try:
            monitored_users = self.config_manager.get_monitored_users()
            if username in monitored_users:
                return event.plain_result(f"❌ 用户 {username} 已经在视奸列表中了哦~").stop_event()

            # 验证用户是否存在
            events = await self.github_api.get_user_events(username)
            if not events:
                return event.plain_result(f"❌ 无法获取用户 {username} 的动态，请检查用户名是否正确").stop_event()

            monitored_users.append(username)
            self.config_manager.update_config("monitored_users", monitored_users)
            self.config_manager.config.save_config()  # 保存配置
            return event.plain_result(f"✅ 已将用户 {username} 加入视奸列表~").stop_event()
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 添加用户失败: {e}")
            return event.plain_result(f"❌ 添加用户失败: {e}").stop_event()

    @yandere_group.command("remove")
    async def remove_user(self, event: AstrMessageEvent, username: str):
        """从视奸列表中移除一个GitHub用户"""
        self._prepare_command(event)

        try:
            monitored_users = self.config_manager.get_monitored_users()
            if username not in monitored_users:
                return event.plain_result(f"❌ 用户 {username} 不在视奸列表中哦~").stop_event()

            monitored_users.remove(username)
            self.config_manager.update_config("monitored_users", monitored_users)
            self.config_manager.config.save_config()  # 保存配置
            return event.plain_result(f"✅ 已将用户 {username} 从视奸列表中移除~").stop_event()
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 移除用户失败: {e}")
            return event.plain_result(f"❌ 移除用户失败: {e}").stop_event()

    @yandere_group.command("enable")
    @filter.permission_type(PermissionType.ADMIN)
    async def enable_session(self, event: AstrMessageEvent):
        """启用当前会话的通知"""
        self._prepare_command(event)

        try:
            target_sessions = self.config_manager.get_target_sessions()
            session_id = event.unified_msg_origin

            if session_id in target_sessions:
                return event.plain_result("当前会话已启用通知").stop_event()

            target_sessions.append(session_id)
            self.config_manager.update_config("target_sessions", target_sessions)
            self.config_manager.config.save_config()  # 保存配置
            return event.plain_result("已启用当前会话的通知").stop_event()
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 启用会话失败: {e}")
            return event.plain_result(f"启用失败: {e}").stop_event()

    @yandere_group.command("disable")
    @filter.permission_type(PermissionType.ADMIN)
    async def disable_session(self, event: AstrMessageEvent):
        """禁用当前会话的通知"""
        self._prepare_command(event)

        try:
            target_sessions = self.config_manager.get_target_sessions()
            session_id = event.unified_msg_origin

            if session_id not in target_sessions:
                return event.plain_result("当前会话未启用通知").stop_event()

            target_sessions.remove(session_id)
            self.config_manager.update_config("target_sessions", target_sessions)
            self.config_manager.config.save_config()  # 保存配置
            return event.plain_result("已禁用当前会话的通知").stop_event()
        except Exception as e:
            logger.error(f"Yandere Github Stalker: 禁用会话失败: {e}")
            return event.plain_result(f"禁用失败: {e}").stop_event()

    async def _monitoring_loop(self):
        """监控循环"""
        logger.debug("Yandere Github Stalker: 开始监控循环")
        self.is_monitoring = True

        while self.is_monitoring:
            try:
                # 检查是否需要清理数据库（每24小时清理一次）
                now = datetime.now()
                if (now - self.last_cleanup_time).total_seconds() >= 24 * 3600:  # 24小时
                    logger.debug("Yandere Github Stalker: 开始清理过期事件ID")
                    retention_days = self.config_manager.get_event_retention_days()
                    success = await self.pushed_event_ids_manager.cleanup_old_events(retention_days)
                    if success:
                        self.last_cleanup_time = now
                        logger.debug("Yandere Github Stalker: 清理完成")
                    else:
                        logger.warning("Yandere Github Stalker: 清理失败，将在下次检查时重试")

                # 获取配置
                monitored_users = self.config_manager.get_monitored_users()
                target_sessions = self.config_manager.get_target_sessions()
                check_interval = self.config_manager.get_check_interval()

                if not monitored_users:
                    logger.debug("Yandere Github Stalker: 没有要监控的用户")
                    await asyncio.sleep(check_interval)
                    continue

                if not target_sessions:
                    logger.debug("Yandere Github Stalker: 没有推送目标会话")
                    await asyncio.sleep(check_interval)
                    continue

                # 获取并处理每个用户的事件
                for username in monitored_users:
                    try:
                        # 获取用户事件
                        events = await self.github_api.get_user_events(username)
                        if not events:
                            continue

                        # 处理事件
                        new_events = await self.event_processor.process_events(events, username)
                        if not new_events:
                            continue

                        # 推送新事件通知
                        for event in new_events:
                            try:
                                # 根据配置选择通知方式
                                if self.config_manager.is_image_notification_enabled():
                                    success = await self.notification_sender.send_image_notification(
                                        username, event, target_sessions)
                                else:
                                    success = await self.notification_sender.send_text_notification(
                                        username, event, target_sessions)

                                # 标记事件状态
                                if success:
                                    if not await self.event_processor.mark_event_as_pushed(event.id, username, event.created_at):
                                        logger.warning(
                                            f"Yandere Github Stalker: 事件 {event.id} 标记失败，可能会在下次重复推送")
                                else:
                                    # 如果发送失败，也标记为已处理，避免重复推送
                                    await self.event_processor.mark_event_as_ignored(event.id, username, event.created_at)
                            except Exception as e:
                                logger.error(
                                    f"Yandere Github Stalker: 处理事件 {event.id} 时出错: {str(e)}")
                                continue
                    except Exception as e:
                        logger.error(
                            f"Yandere Github Stalker: 处理用户 {username} 的事件时出错: {str(e)}")
                        continue

                # 等待下一次检查
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Yandere Github Stalker: 监控循环出错: {str(e)}")
                await asyncio.sleep(check_interval)  # 出错后也要等待，避免频繁重试

    async def start(self) -> None:
        """启动插件"""
        if not self.is_monitoring:
            # 启动时先清理一次数据库
            logger.debug("Yandere Github Stalker: 插件启动，执行初始数据库清理")
            retention_days = self.config_manager.get_event_retention_days()
            success = await self.pushed_event_ids_manager.cleanup_old_events(retention_days)
            if not success:
                logger.warning("Yandere Github Stalker: 初始数据库清理失败，将在下次定时任务重试")
            
            # 启动监控任务
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.debug("Yandere Github Stalker: 监控任务已启动")

    async def stop_monitoring(self):
        """停止监控"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None
            logger.info("Yandere Github Stalker: 监控任务已停止")

    async def terminate(self):
        """插件卸载时调用"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
        if hasattr(self, "pushed_event_ids_manager") and self.pushed_event_ids_manager is not None:
            logger.info("Closing pushed event ids manager...")
            try:
                self.pushed_event_ids_manager.close()
                logger.info("Pushed event ids manager closed successfully")
            except Exception as e:
                logger.error(f"Error closing pushed event ids manager: {e}")
            # 移除pushed_event_ids_manager引用
            self.pushed_event_ids_manager = None

        logger.info("Yandere Github Stalker: 插件已停止...有缘再见呢 ♥")
