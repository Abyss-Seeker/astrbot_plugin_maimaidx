import asyncio
import json
import re
import traceback
from textwrap import dedent
from typing import List, Optional
from pathlib import Path
import PIL.Image

from libraries.config import SONGS_PER_PAGE, UUID, public_addr
from libraries.image import image_to_base64, text_to_image
from libraries.maimaidx_api_data import maiApi
from libraries.maimaidx_error import ServerError
from libraries.maimaidx_model import Alias, PushAliasStatus
from libraries.maimaidx_music import alias, mai, update_local_alias
from libraries.maimaidx_music_info import draw_music_info

# CLI 版全局变量
def log(*args, **kwargs):
    print(*args, **kwargs)

async def update_alias_cli():
    try:
        await mai.get_music_alias()
        log('手动更新别名库成功')
    except Exception as e:
        log('手动更新别名库失败:', e)

async def alias_switch_cli(on: bool):
    if on:
        await alias.alias_global_change(True)
        print('已全局开启maimai别名推送')
    else:
        await alias.alias_global_change(False)
        print('已全局关闭maimai别名推送')

async def alias_local_apply_cli(song_id: str, alias_name: str):
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
        log(traceback.format_exc())
        msg = str(e)
    print(msg)

async def alias_agree_cli(tag: str, user_id: int):
    try:
        status = await maiApi.post_agree_user(tag.upper(), user_id)
        print(status)
    except ValueError as e:
        print(str(e))

async def alias_status_cli(page: int = 1):
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
        if isinstance(img, PIL.Image.Image):
            img.save(img_path)
            print(f"别名投票状态图片已保存到: {img_path}")
        else:
            print(img)
    except (ServerError, ValueError) as e:
        log(traceback.format_exc())
        print(str(e))

async def alias_song_cli(song_id_or_alias: str):
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