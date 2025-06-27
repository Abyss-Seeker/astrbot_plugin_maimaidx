"""
MaimaiDX Plugin for AstrBot
舞萌DX查询工具插件
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 导入 AstrBot 相关模块
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.star.filter.permission import PermissionType

# 导入插件内部模块
from src.config_manager import ConfigManager
from src.data_manager import DataManager
from src.output_manager import OutputManager
from src.error_handler import ErrorHandler

# 导入命令模块
from src.command import mai_base, mai_alias, mai_guess, mai_score, mai_search, mai_table


@register("astrbot_plugin_maimaidx", "AbyssSeeker", "MaimaiDX 插件 - 舞萌DX查询工具", "1.0.0", "https://github.com/AbyssSeeker/astrbot_plugin_maimaidx")
class MaimaiDXPlugin(Star):
    """MaimaiDX 插件主类"""
    
    def __init__(self, context: Context):
        """初始化插件"""
        super().__init__(context)
        
        # 获取插件根目录
        self.plugin_root = Path(__file__).parent.resolve()
        
        # 初始化组件
        self.config_manager = ConfigManager(context)
        self.data_manager = DataManager(self.plugin_root)
        self.output_manager = OutputManager(self.plugin_root)
        self.error_handler = ErrorHandler()
        
        # 启动数据初始化任务
        asyncio.create_task(self._initialize_plugin())
        
        logger.info("MaimaiDX 插件初始化完成")
    
    async def _initialize_plugin(self):
        """初始化插件数据"""
        try:
            # 确保数据准备就绪
            success = await self.data_manager.ensure_data_ready()
            if success:
                logger.info("MaimaiDX 插件数据初始化成功")
            else:
                logger.error("MaimaiDX 插件数据初始化失败")
        except Exception as e:
            logger.error(f"MaimaiDX 插件初始化异常: {e}")
    
    def _prepare_command(self, event: AstrMessageEvent):
        """准备命令执行环境"""
        event.stop_event()
        event.should_call_llm(False)
    
    # ==================== 基础命令 ====================
    
    @filter.command_group("maimai")
    def maimai_group(self):
        """MaimaiDX 命令组"""
        pass
    
    @maimai_group.command("help")
    async def maimai_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        self._prepare_command(event)
        
        help_text = """
🎵 MaimaiDX 插件帮助

📋 基础命令：
  /maimai b50 [用户名]         - 查询B50
  /maimai minfo [用户名] [曲名/ID] - 查询游玩数据
  /maimai ginfo [难度] [曲名/ID]   - 查询曲目统计
  /maimai score [难度] [ID] [分数]   - 分数线计算
  /maimai today [用户ID]          - 今日舞萌运势

🔍 搜索命令：
  /maimai search [关键词] [页数]       - 查歌
  /maimai search_base [定数下限] [定数上限] [页数] - 定数查歌
  /maimai search_bpm [bpm下限] [bpm上限] [页数] - bpm查歌
  /maimai search_artist [曲师] [页数]     - 曲师查歌
  /maimai search_charter [谱师] [页数]     - 谱师查歌
  /maimai search_alias [别名]         - 别名查歌
  /maimai search_id [ID]                - ID查歌

📊 表格命令：
  /maimai table_pfm [用户名] [难度/plate] - 完成表
  /maimai rating_table [难度] [用户名] - 定数表

🛠️ 管理命令：
  /maimai update_alias            - 更新别名库
  /maimai update_rating_table     - 更新定数表
  /maimai update_plate_table      - 更新完成表
  /maimai init                    - 重新初始化曲库数据

💡 提示：基于Yuri-YuzuChaN的maimaiDX，由AbyssSeeker移植
        """.strip()
        
        yield event.plain_result(help_text)
    
    @maimai_group.command("today")
    async def maimai_today(self, event: AstrMessageEvent, user_id: Optional[str] = None):
        """今日舞萌运势"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 如果没有提供user_id，使用发送者ID
            if user_id is None:
                user_id = event.get_sender_name() or "default"
            
            # 调用原始函数
            result = await mai_base.mai_today_cli(user_id)
            
            # 发送结果
            if isinstance(result, str):
                yield event.plain_result(result)
            else:
                # 假设返回的是图片路径
                yield event.image_result(str(result))
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "获取今日运势失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("repo")
    async def maimai_repo(self, event: AstrMessageEvent):
        """显示项目地址"""
        self._prepare_command(event)
        
        repo_text = "项目地址：https://github.com/Yuri-YuzuChaN/maimaiDX\n求star，求宣传~"
        yield event.plain_result(repo_text)
    
    # ==================== 分数相关命令 ====================
    
    @maimai_group.command("b50")
    async def maimai_b50(self, event: AstrMessageEvent, username: Optional[str] = None):
        """查询B50"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 如果没有提供用户名，使用默认用户名
            if username is None:
                username = self.config_manager.get_default_username()
            
            # 验证用户名
            is_valid, username_or_error = self.error_handler.validate_username(username)
            if not is_valid:
                yield event.plain_result(f"❌ {username_or_error}")
                return
            
            # 调用原始函数
            result = await mai_score.b50_cli(username_or_error)
            
            # 发送结果
            if isinstance(result, str):
                yield event.plain_result(result)
            else:
                # 假设返回的是图片
                await self.output_manager.send_image_result(event, result, f"b50_{username_or_error}.png")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "查询B50失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("minfo")
    async def maimai_minfo(self, event: AstrMessageEvent, username: str, song: str):
        """查询玩家游玩记录"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 验证用户名
            is_valid, username_or_error = self.error_handler.validate_username(username)
            if not is_valid:
                yield event.plain_result(f"❌ {username_or_error}")
                return
            
            # 调用原始函数
            result = await mai_score.minfo_cli(username_or_error, song)
            
            # 发送结果
            if isinstance(result, str):
                yield event.plain_result(result)
            else:
                # 假设返回的是图片
                await self.output_manager.send_image_result(event, result, f"minfo_{username_or_error}_{song}.png")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "查询游玩记录失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("ginfo")
    async def maimai_ginfo(self, event: AstrMessageEvent, difficulty: str, song: str):
        """查询曲目信息"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 验证难度
            is_valid, difficulty_or_error = self.error_handler.validate_difficulty(difficulty)
            if not is_valid:
                yield event.plain_result(f"❌ {difficulty_or_error}")
                return
            
            # 调用原始函数
            result = await mai_score.ginfo_cli(f"{difficulty_or_error} {song}")
            
            # 发送结果
            if isinstance(result, str):
                yield event.plain_result(result)
            else:
                # 假设返回的是图片
                await self.output_manager.send_image_result(event, result, f"ginfo_{difficulty_or_error}_{song}.png")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "查询曲目信息失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("score")
    async def maimai_score(self, event: AstrMessageEvent, args: str):
        """计算分数线"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            result = await mai_score.score_cli(args)
            
            # 发送结果
            yield event.plain_result(result)
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "计算分数线失败")
            yield event.plain_result(error_msg)
    
    # ==================== 搜索相关命令 ====================
    
    @maimai_group.command("search")
    async def maimai_search(self, event: AstrMessageEvent, name: str = "", page: int = 1):
        """查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_search.search_music_cli(name, page=page)
            
            # 注意：search_music_cli 可能直接输出到控制台，需要修改为返回结果
            yield event.plain_result("搜索完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "搜索歌曲失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("search_base")
    async def maimai_search_base(self, event: AstrMessageEvent, *args):
        """定数查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_search.search_base_cli(list(args))
            
            yield event.plain_result("定数查歌完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "定数查歌失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("search_bpm")
    async def maimai_search_bpm(self, event: AstrMessageEvent, *args):
        """bpm查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_search.search_bpm_cli(list(args))
            
            yield event.plain_result("BPM查歌完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "BPM查歌失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("search_artist")
    async def maimai_search_artist(self, event: AstrMessageEvent, *args):
        """曲师查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_search.search_artist_cli(list(args))
            
            yield event.plain_result("曲师查歌完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "曲师查歌失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("search_charter")
    async def maimai_search_charter(self, event: AstrMessageEvent, *args):
        """谱师查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_search.search_charter_cli(list(args))
            
            yield event.plain_result("谱师查歌完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "谱师查歌失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("search_alias")
    async def maimai_search_alias(self, event: AstrMessageEvent, alias: str):
        """别名查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_search.search_alias_song_cli(alias)
            
            yield event.plain_result("别名查歌完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "别名查歌失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("search_id")
    async def maimai_search_id(self, event: AstrMessageEvent, song_id: str):
        """ID查歌"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 验证歌曲ID
            is_valid, song_id_or_error = self.error_handler.validate_song_id(song_id)
            if not is_valid:
                yield event.plain_result(f"❌ {song_id_or_error}")
                return
            
            # 调用原始函数
            await mai_search.query_chart_cli(song_id_or_error)
            
            yield event.plain_result("ID查歌完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "ID查歌失败")
            yield event.plain_result(error_msg)
    
    # ==================== 表格相关命令 ====================
    
    @maimai_group.command("table_pfm")
    async def maimai_table_pfm(self, event: AstrMessageEvent, username: str = "default", *args):
        """完成表"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 验证用户名
            is_valid, username_or_error = self.error_handler.validate_username(username)
            if not is_valid:
                yield event.plain_result(f"❌ {username_or_error}")
                return
            
            # 调用原始函数
            await mai_table.table_pfm_cli(username_or_error, ' '.join(args))
            
            yield event.plain_result("完成表生成完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "生成完成表失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("rating_table")
    async def maimai_rating_table(self, event: AstrMessageEvent, *args, username: str = "default"):
        """定数表"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 验证用户名
            is_valid, username_or_error = self.error_handler.validate_username(username)
            if not is_valid:
                yield event.plain_result(f"❌ {username_or_error}")
                return
            
            # 调用原始函数
            await mai_table.rating_table_cli(' '.join(args), username_or_error)
            
            yield event.plain_result("定数表生成完成，请查看输出")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "生成定数表失败")
            yield event.plain_result(error_msg)
    
    # ==================== 管理命令 ====================
    
    @maimai_group.command("update_rating_table")
    @filter.permission_type(PermissionType.ADMIN)
    async def maimai_update_rating_table(self, event: AstrMessageEvent):
        """更新定数表"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_table.update_rating_table_cli()
            
            yield event.plain_result("✅ 定数表更新完成")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "更新定数表失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("update_plate_table")
    @filter.permission_type(PermissionType.ADMIN)
    async def maimai_update_plate_table(self, event: AstrMessageEvent):
        """更新完成表"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_table.update_plate_table_cli()
            
            yield event.plain_result("✅ 完成表更新完成")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "更新完成表失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("update_alias")
    @filter.permission_type(PermissionType.ADMIN)
    async def maimai_update_alias(self, event: AstrMessageEvent):
        """更新别名库"""
        self._prepare_command(event)
        
        try:
            # 确保数据准备就绪
            if not await self.data_manager.ensure_data_ready():
                yield event.plain_result("❌ 数据未准备就绪，请稍后重试")
                return
            
            # 调用原始函数
            await mai_alias.update_alias_cli()
            
            yield event.plain_result("✅ 别名库更新完成")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "更新别名库失败")
            yield event.plain_result(error_msg)
    
    @maimai_group.command("init")
    @filter.permission_type(PermissionType.ADMIN)
    async def maimai_init(self, event: AstrMessageEvent):
        """重新初始化曲库数据"""
        self._prepare_command(event)
        
        try:
            yield event.plain_result("🔄 正在初始化曲库数据，请稍候...")
            
            # 强制重新初始化
            success = await self.data_manager.initialize_data(force=True)
            
            if success:
                yield event.plain_result("✅ 曲库初始化完成！")
            else:
                yield event.plain_result("❌ 曲库初始化失败，请查看日志")
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(event, e, "初始化曲库失败")
            yield event.plain_result(error_msg)
    
    async def terminate(self):
        """插件卸载时的清理工作"""
        try:
            # 清理临时文件
            self.output_manager.cleanup_temp_files()
            logger.info("MaimaiDX 插件已卸载")
        except Exception as e:
            logger.error(f"MaimaiDX 插件卸载时出错: {e}") 