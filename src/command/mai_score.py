import re
from textwrap import dedent
from typing import List, Optional, Union, Tuple, cast
from PIL import Image

from ..libraries.config import score_Rank_l, fcl, fsl, category
from ..libraries.image import image_to_base64, text_to_image
from ..libraries.maimai_best_50 import generate, computeRa, dxScore, coloumWidth, changeColumnWidth
from ..libraries.maimaidx_music import mai
from ..libraries.maimaidx_music_info import draw_music_play_data, draw_music_info
from ..libraries.maimaidx_player_score import music_global_data
from ..libraries.maimaidx_model import Notes1, Notes2

from ..output_manager import OutputManager
from ..error_handler import ErrorHandler

# 初始化输出管理器和错误处理器
output_manager = OutputManager()
error_handler = ErrorHandler()

# AstrBot 命令处理器实现
async def b50_handler(event, username=None):
    """
    B50 查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        username: 用户名，如果为None则从事件中获取
    """
    try:
        if username is None:
            username = event.sender.name if hasattr(event, 'sender') else ""
        
        img = await generate(username or "")
        if isinstance(img, Image.Image):
            # 使用输出管理器保存和发送图片
            result = await output_manager.send_image(event, img, f"b50_{username}.png", f"{username}的B50数据")
            return result
        else:
            result = await output_manager.send_text(event, str(img))
            return result
    except Exception as e:
        result = await error_handler.handle_error(event, e, "B50查询失败")
        return result

async def minfo_handler(event, args: str):
    """
    查询玩家游玩记录命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串，包含曲目ID或曲名
    """
    try:
        args = args.strip()
        if not args:
            result = await output_manager.send_text(event, '请输入曲目id或曲名')
            return result

        # 获取用户名
        username = event.sender.name if hasattr(event, 'sender') else ""

        # 查找曲目
        song_id = None
        if mai.total_list.by_id(args):
            song_id = args
        elif by_t := mai.total_list.by_title(args):
            song_id = by_t.id
        else:
            alias = mai.total_alias_list.by_alias(args)
            if not alias:
                result = await output_manager.send_text(event, '未找到曲目')
                return result
            elif len(alias) != 1:
                msg = f'找到相同别名的曲目，请使用以下ID查询：\n'
                for song in alias:
                    msg += f'{song.SongID}：{song.Name}\n'
                result = await output_manager.send_text(event, msg.strip())
                return result
            else:
                song_id = str(alias[0].SongID)

        if song_id is None:
            result = await output_manager.send_text(event, '未找到曲目')
            return result

        result = await draw_music_play_data(username, song_id)
        if isinstance(result, Image.Image):
            result = await output_manager.send_image(event, result, f"minfo_{username}_{song_id}.png", f"{username}的游玩记录")
            return result
        else:
            result = await output_manager.send_text(event, str(result))
            return result
    except Exception as e:
        result = await error_handler.handle_error(event, e, "游玩记录查询失败")
        return result

async def ginfo_handler(event, args: str):
    """
    查询曲目信息命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串，格式为 "难度 曲目ID/曲名"
    """
    try:
        args = args.strip()
        if not args:
            result = await output_manager.send_text(event, '请输入难度+曲目id或曲名')
            return result

        # 解析难度和曲目
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            result = await output_manager.send_text(event, '格式错误，请输入难度+曲目id或曲名')
            return result
        
        difficulty, song = parts
        if difficulty[0] not in '绿黄红紫白':
            result = await output_manager.send_text(event, '难度必须是绿/黄/红/紫/白之一')
            return result
        
        level_index = '绿黄红紫白'.index(difficulty[0])
        song = song.strip()

        # 查找曲目
        music = None
        if mai.total_list.by_id(song):
            music = mai.total_list.by_id(song)
        elif by_t := mai.total_list.by_title(song):
            music = by_t
        else:
            alias = mai.total_alias_list.by_alias(song)
            if not alias:
                result = await output_manager.send_text(event, '未找到曲目')
                return result
            elif len(alias) != 1:
                msg = f'找到相同别名的曲目，请使用以下ID查询：\n'
                for song in alias:
                    msg += f'{song.SongID}：{song.Name}\n'
                result = await output_manager.send_text(event, msg.strip())
                return result
            else:
                music = mai.total_list.by_id(str(alias[0].SongID))
                if not music:
                    result = await output_manager.send_text(event, '未找到曲目')
                    return result

        if music is None:
            result = await output_manager.send_text(event, '未找到曲目')
            return result

        result = await draw_music_info(music, level_index)
        if isinstance(result, Image.Image):
            result = await output_manager.send_image(event, result, f"ginfo_{music.id}_{level_index}.png", f"{music.title}的曲目信息")
            return result
        else:
            result = await output_manager.send_text(event, str(result))
            return result
    except Exception as e:
        result = await error_handler.handle_error(event, e, "曲目信息查询失败")
        return result

async def score_handler(event, args: str):
    """
    计算分数线命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串，格式为 "难度+歌曲id 分数线"
    """
    try:
        args = args.strip()
        if not args:
            result = await output_manager.send_text(event, '请输入难度+歌曲id和分数线')
            return result

        # 显示帮助信息
        if args == '帮助':
            help_text = dedent('''\
                此功能为查找某首歌分数线设计。
                命令格式：分数线「难度+歌曲id」「分数线」
                例如：分数线 紫799 100
                命令将返回分数线允许的「TAP」「GREAT」容错，
                以及「BREAK」50落等价的「TAP」「GREAT」数。
                以下为「TAP」「GREAT」的对应表：
                        GREAT / GOOD / MISS
                TAP         1 / 2.5  / 5
                HOLD        2 / 5    / 10
                SLIDE       3 / 7.5  / 15
                TOUCH       1 / 2.5  / 5
                BREAK       5 / 12.5 / 25 (外加200落)
            ''').strip()
            result = await output_manager.send_text(event, help_text)
            return result

        # 解析参数
        try:
            parts = args.split()
            if len(parts) < 2:
                result = await output_manager.send_text(event, '格式错误，请输入难度+歌曲id和分数线')
                return result
            
            # 处理难度和歌曲ID
            if len(parts) == 2:
                # 格式：紫799 100
                if not any(diff in parts[0] for diff in '绿黄红紫白'):
                    result = await output_manager.send_text(event, '格式错误，难度必须是绿/黄/红/紫/白之一')
                    return result
                difficulty = parts[0][0]  # 取第一个字符作为难度
                song_id = parts[0][1:]    # 剩余部分作为歌曲ID
                try:
                    score_line = float(parts[1])
                except ValueError:
                    result = await output_manager.send_text(event, '分数线必须是数字')
                    return result
            elif len(parts) == 3:
                # 格式：紫 799 100
                if parts[0] not in '绿黄红紫白':
                    result = await output_manager.send_text(event, '格式错误，难度必须是绿/黄/红/紫/白之一')
                    return result
                difficulty = parts[0]
                song_id = parts[1]
                try:
                    score_line = float(parts[2])
                except ValueError:
                    result = await output_manager.send_text(event, '分数线必须是数字')
                    return result
            else:
                result = await output_manager.send_text(event, '格式错误，请输入难度+歌曲id和分数线')
                return result

            # 查找歌曲
            music = mai.total_list.by_id(song_id)
            if not music:
                result = await output_manager.send_text(event, '未找到歌曲')
                return result

            # 计算分数线
            level_index = '绿黄红紫白'.index(difficulty)
            if music.ds is None or level_index >= len(music.ds):
                result = await output_manager.send_text(event, '该歌曲没有此难度')
                return result

            # 获取谱面数据
            chart = music.charts[level_index]
            if not chart:
                result = await output_manager.send_text(event, '未找到谱面数据')
                return result

            # 计算容错 - 使用正确的参数调用computeRa
            result_text = computeRa(score_line, chart)
            result = await output_manager.send_text(event, result_text)
            return result

        except Exception as e:
            result = await output_manager.send_text(event, f'计算失败：{str(e)}')
            return result

    except Exception as e:
        result = await error_handler.handle_error(event, e, "分数线计算失败")
        return result

# 保留原有的CLI函数以保持向后兼容性
async def b50_cli(username=None):
    """CLI版本的B50查询（已弃用，请使用b50_handler）"""
    img = await generate(username or "")
    if isinstance(img, Image.Image):
        img_path = f"b50_{username}.png"
        img.save(img_path)
        print(f"B50图片已保存到: {img_path}")
    else:
        print(img)

async def minfo_cli(username: str, args: str) -> Union[str, Image.Image]:
    """CLI版本的游玩记录查询（已弃用，请使用minfo_handler）"""
    args = args.strip()
    if not args:
        return '请输入曲目id或曲名'

    # 查找曲目
    if mai.total_list.by_id(args):
        song_id = args
    elif by_t := mai.total_list.by_title(args):
        song_id = by_t.id
    else:
        alias = mai.total_alias_list.by_alias(args)
        if not alias:
            return '未找到曲目'
        elif len(alias) != 1:
            msg = f'找到相同别名的曲目，请使用以下ID查询：\n'
            for song in alias:
                msg += f'{song.SongID}：{song.Name}\n'
            return msg.strip()
        else:
            song_id = str(alias[0].SongID)

    return await draw_music_play_data(username, song_id)

async def ginfo_cli(args: str) -> Union[str, Image.Image]:
    """CLI版本的曲目信息查询（已弃用，请使用ginfo_handler）"""
    args = args.strip()
    if not args:
        return '请输入难度+曲目id或曲名'

    # 解析难度和曲目
    parts = args.split(maxsplit=1)
    if len(parts) != 2:
        return '格式错误，请输入难度+曲目id或曲名'
    
    difficulty, song = parts
    if difficulty[0] not in '绿黄红紫白':
        return '难度必须是绿/黄/红/紫/白之一'
    
    level_index = '绿黄红紫白'.index(difficulty[0])
    song = song.strip()

    # 查找曲目
    if mai.total_list.by_id(song):
        music = mai.total_list.by_id(song)
    elif by_t := mai.total_list.by_title(song):
        music = by_t
    else:
        alias = mai.total_alias_list.by_alias(song)
        if not alias:
            return '未找到曲目'
        elif len(alias) != 1:
            msg = f'找到相同别名的曲目，请使用以下ID查询：\n'
            for song in alias:
                msg += f'{song.SongID}：{song.Name}\n'
            return msg.strip()
        else:
            music = mai.total_list.by_id(str(alias[0].SongID))
            if not music:
                return '未找到曲目'

    return await draw_music_info(music, level_index)

async def score_cli(args: str) -> str:
    """CLI版本的分数线计算（已弃用，请使用score_handler）"""
    args = args.strip()
    if not args:
        return '请输入难度+歌曲id和分数线'

    # 显示帮助信息
    if args == '帮助':
        return dedent('''\
            此功能为查找某首歌分数线设计。
            命令格式：分数线「难度+歌曲id」「分数线」
            例如：分数线 紫799 100
            命令将返回分数线允许的「TAP」「GREAT」容错，
            以及「BREAK」50落等价的「TAP」「GREAT」数。
            以下为「TAP」「GREAT」的对应表：
                    GREAT / GOOD / MISS
            TAP         1 / 2.5  / 5
            HOLD        2 / 5    / 10
            SLIDE       3 / 7.5  / 15
            TOUCH       1 / 2.5  / 5
            BREAK       5 / 12.5 / 25 (外加200落)
        ''').strip()

    # 解析参数
    try:
        parts = args.split()
        if len(parts) < 2:
            return '格式错误，请输入难度+歌曲id和分数线'
        
        # 处理难度和歌曲ID
        if len(parts) == 2:
            # 格式：紫799 100
            if not any(diff in parts[0] for diff in '绿黄红紫白'):
                return '格式错误，难度必须是绿/黄/红/紫/白之一'
            difficulty = parts[0][0]  # 取第一个字符作为难度
            song_id = parts[0][1:]    # 剩余部分作为歌曲ID
            try:
                score_line = float(parts[1])
            except ValueError:
                return '分数线必须是数字'
        elif len(parts) == 3:
            # 格式：紫 799 100
            if parts[0] not in '绿黄红紫白':
                return '格式错误，难度必须是绿/黄/红/紫/白之一'
            difficulty = parts[0]
            song_id = parts[1]
            try:
                score_line = float(parts[2])
            except ValueError:
                return '分数线必须是数字'
        else:
            return '格式错误，请输入难度+歌曲id和分数线'

        if not song_id.isdigit():
            return '歌曲ID必须是数字'
        
        level_labels = ['绿', '黄', '红', '紫', '白']
        level_labels2 = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
        level_index = level_labels.index(difficulty)
        
        music = mai.total_list.by_id(song_id)
        if not music:
            return '未找到曲目'

        # 获取谱面信息
        chart = music.charts[level_index]
        notes = chart.notes or []
        tap = int(notes[0]) if len(notes) > 0 else 0
        hold = int(notes[1]) if len(notes) > 1 else 0
        slide = int(notes[2]) if len(notes) > 2 else 0
        if len(notes) == 5:
            touch = int(notes[3])
            brk = int(notes[4])
        else:
            touch = 0
            brk = int(notes[3]) if len(notes) > 3 else 0

        # 计算总分和分数线
        total_score = tap * 500 + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
        break_bonus = 0.01 / brk if brk > 0 else 0
        break_50_reduce = total_score * break_bonus / 4
        reduce = 101 - score_line

        if reduce <= 0 or reduce >= 101:
            return '分数线必须在0-101之间'

        msg = f'''\
            {music.title}「{level_labels2[level_index]}」
            分数线「{score_line}%」
            允许的最多「TAP」「GREAT」数量为 
            「{(total_score * reduce / 10000):.2f}」(每个-{10000 / total_score:.4f}%),
            「BREAK」50落(一共「{brk}」个)
            等价于「{(break_50_reduce / 100):.3f}」个「TAP」「GREAT」(-{break_50_reduce / total_score * 100:.4f}%)
        '''
        return dedent(msg).strip()
    except Exception as e:
        return f'计算时出错：{str(e)}'