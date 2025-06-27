import asyncio
import json
import re
import traceback
from textwrap import dedent
from typing import List, Optional
from pathlib import Path
from PIL import Image

from ..libraries.config import SONGS_PER_PAGE, UUID, public_addr
from ..libraries.image import image_to_base64, text_to_image
from ..libraries.maimaidx_api_data import maiApi
from ..libraries.maimaidx_error import ServerError
from ..libraries.maimaidx_model import Alias, PushAliasStatus
from ..libraries.maimaidx_music import alias, mai, update_local_alias
from ..libraries.maimaidx_music_info import draw_music_info

from ..output_manager import OutputManager
from ..error_handler import ErrorHandler

# 初始化输出管理器和错误处理器
output_manager = OutputManager()
error_handler = ErrorHandler()

# AstrBot 命令处理器实现
async def update_alias_handler(event):
    """
    更新别名库命令处理器
    
    Args:
        event: AstrBot 事件对象
    """
    try:
        await mai.get_music_alias()
        return output_manager.send_text(event, '手动更新别名库成功')
    except Exception as e:
        return error_handler.handle_error(event, e, "手动更新别名库失败")

async def alias_switch_handler(event, on: bool):
    """
    别名推送开关命令处理器
    
    Args:
        event: AstrBot 事件对象
        on: 是否开启
    """
    try:
        if on:
            await alias.alias_global_change(True)
            return output_manager.send_text(event, '已全局开启maimai别名推送')
        else:
            await alias.alias_global_change(False)
            return output_manager.send_text(event, '已全局关闭maimai别名推送')
    except Exception as e:
        return error_handler.handle_error(event, e, "别名推送开关设置失败")

async def alias_local_apply_handler(event, song_id: str, alias_name: str):
    """
    添加本地别名命令处理器
    
    Args:
        event: AstrBot 事件对象
        song_id: 歌曲ID
        alias_name: 别名名称
    """
    try:
        if not mai.total_list.by_id(song_id):
            return output_manager.send_text(event, f'未找到ID为「{song_id}」的曲目')
        
        server_exist = await maiApi.get_songs_alias(int(song_id))
        if isinstance(server_exist, Alias) and alias_name.lower() in server_exist.Alias:
            return output_manager.send_text(event, f'该曲目的别名「{alias_name}」已存在别名服务器')
        
        local_exist = mai.total_alias_list.by_id(song_id)
        if local_exist and alias_name.lower() in local_exist[0].Alias:
            return output_manager.send_text(event, '本地别名库已存在该别名')
        
        issave = await update_local_alias(song_id, alias_name)
        if not issave:
            msg = '添加本地别名失败'
        else:
            msg = f'已成功为ID「{song_id}」添加别名「{alias_name}」到本地别名库'
        return output_manager.send_text(event, msg)
    except Exception as e:
        return error_handler.handle_error(event, e, "添加本地别名失败")

async def alias_apply_handler(event, song_id: str, alias_name: str, group_id: Optional[int] = None):
    """
    申请别名命令处理器
    
    Args:
        event: AstrBot 事件对象
        song_id: 歌曲ID
        alias_name: 别名名称
        group_id: 群组ID（可选）
    """
    try:
        user_id = event.sender.id if hasattr(event, 'sender') else 0
        
        if not (music := mai.total_list.by_id(song_id)):
            return output_manager.send_text(event, f'未找到ID为「{song_id}」的曲目')
        
        isexist = await maiApi.get_songs_alias(int(song_id))
        if isinstance(isexist, Alias) and alias_name.lower() in isexist.Alias:
            return output_manager.send_text(event, f'该曲目的别名「{alias_name}」已存在别名服务器')
        
        msg = await maiApi.post_alias(int(song_id), alias_name, int(user_id), int(group_id) if group_id is not None else 0)
        return output_manager.send_text(event, msg)
    except (ServerError, ValueError) as e:
        return error_handler.handle_error(event, e, "申请别名失败")

async def alias_agree_handler(event, tag: str):
    """
    同意别名申请命令处理器
    
    Args:
        event: AstrBot 事件对象
        tag: 申请标签
    """
    try:
        user_id = event.sender.id if hasattr(event, 'sender') else 0
        status = await maiApi.post_agree_user(tag.upper(), user_id)
        return output_manager.send_text(event, str(status))
    except ValueError as e:
        return output_manager.send_text(event, str(e))

async def alias_status_handler(event, page: int = 1):
    """
    别名投票状态查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        page: 页码
    """
    try:
        status = await maiApi.get_alias_status()
        if not status:
            return output_manager.send_text(event, '未查询到正在进行的别名投票')
        
        page = max(min(page, len(status) // SONGS_PER_PAGE + 1), 1)
        result = []
        for num, _s in enumerate(status):
            if (page - 1) * SONGS_PER_PAGE <= num < page * SONGS_PER_PAGE:
                apply_alias = _s.ApplyAlias
                if len(_s.ApplyAlias) > 15:
                    apply_alias = _s.ApplyAlias[:15] + '...'
                result.append(
                    dedent(f'''\
                        - {_s.Tag}：
                        - ID：{_s.SongID}
                        - 别名：{apply_alias}
                        - 票数：{_s.AgreeVotes}/{_s.Votes}
                    ''')
                )
        result.append(f'第「{page}」页，共「{len(status) // SONGS_PER_PAGE + 1}」页')
        img = text_to_image('\n'.join(result))
        if isinstance(img, Image.Image):
            return output_manager.send_image(event, img, f"alias_status_{page}.png", f"别名投票状态第{page}页")
        else:
            return output_manager.send_text(event, str(img))
    except (ServerError, ValueError) as e:
        return error_handler.handle_error(event, e, "查询别名投票状态失败")

async def alias_song_handler(event, song_id_or_alias: str):
    """
    查询歌曲别名命令处理器
    
    Args:
        event: AstrBot 事件对象
        song_id_or_alias: 歌曲ID或别名
    """
    try:
        # 支持ID或别名查询
        name = song_id_or_alias
        aliases = None
        if name.isdigit():
            alias_id = mai.total_alias_list.by_id(name)
            if not alias_id:
                return output_manager.send_text(event, '未找到此歌曲\n可以使用"添加别名"指令给该乐曲添加别名')
            else:
                aliases = alias_id
        else:
            aliases = mai.total_alias_list.by_alias(name)
            if not aliases:
                return output_manager.send_text(event, '未找到此歌曲\n可以使用"添加别名"指令给该乐曲添加别名')
        
        if len(aliases) != 1:
            msg = []
            for songs in aliases:
                alias_list = '\n'.join(songs.Alias)
                msg.append(f'ID：{songs.SongID}\n{alias_list}')
            return output_manager.send_text(event, f'找到{len(aliases)}个相同别名的曲目：\n' + '\n======\n'.join(msg))
        
        if len(aliases[0].Alias) == 1:
            return output_manager.send_text(event, '该曲目没有别名')
        
        msg = f'该曲目有以下别名：\nID：{aliases[0].SongID}\n'
        msg += '\n'.join(aliases[0].Alias)
        return output_manager.send_text(event, msg)
    except Exception as e:
        return error_handler.handle_error(event, e, "查询歌曲别名失败")

# 保留原有的CLI函数以保持向后兼容性
async def update_alias_cli():
    """CLI版本的别名库更新（已弃用，请使用update_alias_handler）"""
    try:
        await mai.get_music_alias()
        print('手动更新别名库成功')
    except Exception as e:
        print('手动更新别名库失败:', e)

async def alias_switch_cli(on: bool):
    """CLI版本的别名推送开关（已弃用，请使用alias_switch_handler）"""
    if on:
        await alias.alias_global_change(True)
        print('已全局开启maimai别名推送')
    else:
        await alias.alias_global_change(False)
        print('已全局关闭maimai别名推送')

async def alias_local_apply_cli(song_id: str, alias_name: str):
    """CLI版本的添加本地别名（已弃用，请使用alias_local_apply_handler）"""
    if not mai.total_list.by_id(song_id):
        print(f'未找到ID为「{song_id}」的曲目')
        return
    server_exist = await maiApi.get_songs_alias(int(song_id))
    if isinstance(server_exist, Alias) and alias_name.lower() in server_exist.Alias:
        print(f'该曲目的别名「{alias_name}」已存在别名服务器')
        return
    local_exist = mai.total_alias_list.by_id(song_id)
    if local_exist and alias_name.lower() in local_exist[0].Alias:
        print('本地别名库已存在该别名')
        return
    issave = await update_local_alias(song_id, alias_name)
    if not issave:
        msg = '添加本地别名失败'
    else:
        msg = f'已成功为ID「{song_id}」添加别名「{alias_name}」到本地别名库'
    print(msg)

async def alias_apply_cli(song_id: str, alias_name: str, user_id: int, group_id: Optional[int] = None):
    """CLI版本的申请别名（已弃用，请使用alias_apply_handler）"""
    try:
        if not (music := mai.total_list.by_id(song_id)):
            print(f'未找到ID为「{song_id}」的曲目')
            return
        isexist = await maiApi.get_songs_alias(int(song_id))
        if isinstance(isexist, Alias) and alias_name.lower() in isexist.Alias:
            print(f'该曲目的别名「{alias_name}」已存在别名服务器')
            return
        msg = await maiApi.post_alias(int(song_id), alias_name, int(user_id), int(group_id) if group_id is not None else 0)
    except (ServerError, ValueError) as e:
        print(traceback.format_exc())
        msg = str(e)
    print(msg)

async def alias_agree_cli(tag: str, user_id: int):
    """CLI版本的同意别名申请（已弃用，请使用alias_agree_handler）"""
    try:
        status = await maiApi.post_agree_user(tag.upper(), user_id)
        print(status)
    except ValueError as e:
        print(str(e))

async def alias_status_cli(page: int = 1):
    """CLI版本的别名投票状态查询（已弃用，请使用alias_status_handler）"""
    try:
        status = await maiApi.get_alias_status()
        if not status:
            print('未查询到正在进行的别名投票')
            return
        page = max(min(page, len(status) // SONGS_PER_PAGE + 1), 1)
        result = []
        for num, _s in enumerate(status):
            if (page - 1) * SONGS_PER_PAGE <= num < page * SONGS_PER_PAGE:
                apply_alias = _s.ApplyAlias
                if len(_s.ApplyAlias) > 15:
                    apply_alias = _s.ApplyAlias[:15] + '...'
                result.append(
                    dedent(f'''\
                        - {_s.Tag}：
                        - ID：{_s.SongID}
                        - 别名：{apply_alias}
                        - 票数：{_s.AgreeVotes}/{_s.Votes}
                    ''')
                )
        result.append(f'第「{page}」页，共「{len(status) // SONGS_PER_PAGE + 1}」页')
        img = text_to_image('\n'.join(result))
        img_path = Path(f"alias_status_{page}.png")
        if isinstance(img, Image.Image):
            img.save(img_path)
            print(f"别名投票状态图片已保存到: {img_path}")
        else:
            print(img)
    except (ServerError, ValueError) as e:
        print(traceback.format_exc())
        print(str(e))

async def alias_song_cli(song_id_or_alias: str):
    """CLI版本的查询歌曲别名（已弃用，请使用alias_song_handler）"""
    # 支持ID或别名查询
    name = song_id_or_alias
    aliases = None
    if name.isdigit():
        alias_id = mai.total_alias_list.by_id(name)
        if not alias_id:
            print('未找到此歌曲\n可以使用"添加别名"指令给该乐曲添加别名')
            return
        else:
            aliases = alias_id
    else:
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            print('未找到此歌曲\n可以使用"添加别名"指令给该乐曲添加别名')
            return
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = '\n'.join(songs.Alias)
            msg.append(f'ID：{songs.SongID}\n{alias_list}')
        print(f'找到{len(aliases)}个相同别名的曲目：\n' + '\n======\n'.join(msg))
        return
    if len(aliases[0].Alias) == 1:
        print('该曲目没有别名')
        return
    msg = f'该曲目有以下别名：\nID：{aliases[0].SongID}\n'
    msg += '\n'.join(aliases[0].Alias)
    print(msg)

# 推送/定时任务相关函数可选实现（如需本地CLI推送可用）
# async def ws_alias_server_cli():
#     ...