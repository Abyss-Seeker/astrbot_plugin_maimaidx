import re
from re import Match
from typing import List, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

from ..libraries.config import Root, SIYUAN, SHANGGUMONO, diffs, SONGS_PER_PAGE
from ..libraries.image import image_to_base64, text_to_image, tricolor_gradient, rounded_corners
from ..libraries.maimaidx_api_data import maiApi
from ..libraries.maimaidx_error import *
from ..libraries.maimaidx_model import AliasStatus
from ..libraries.maimaidx_music import guess, mai
from ..libraries.maimaidx_music_info import draw_music_info

from ..output_manager import OutputManager
from ..error_handler import ErrorHandler

# 初始化输出管理器和错误处理器
output_manager = OutputManager()
error_handler = ErrorHandler()

def create_beautiful_search_image(title: str, content: str, search_type: str = "search") -> Image.Image:
    """
    创建美观的查歌结果图片
    
    Args:
        title: 标题
        content: 内容文本
        search_type: 搜索类型 (search, base, bpm, artist, charter, alias, id)
    """
    # 计算内容行数和图片尺寸
    lines = content.strip().split('\n')
    line_count = len(lines)
    
    # 基础尺寸
    base_width = 1200
    base_height = 200  # 标题和装饰区域
    line_height = 35
    content_height = max(line_count * line_height + 40, 400)  # 最小内容高度
    total_height = base_height + content_height
    
    # 创建渐变背景
    bg = tricolor_gradient(base_width, total_height)
    
    # 添加装饰元素
    try:
        # 顶部装饰条
        decor_top = Image.open(Root / 'static/mai/pic/pattern.png').resize((base_width, 60)).convert('RGBA')
        bg.alpha_composite(decor_top, (0, 0))
    except:
        pass
    
    try:
        # 底部装饰条
        decor_bottom = Image.open(Root / 'static/mai/pic/pattern.png').resize((base_width, 60)).convert('RGBA')
        bg.alpha_composite(decor_bottom, (0, total_height - 60))
    except:
        pass
    
    # 添加动漫元素
    try:
        # 左上角装饰
        chara_left = Image.open(Root / 'static/mai/pic/chara-left.png').resize((120, 120)).convert('RGBA')
        bg.alpha_composite(chara_left, (30, 40))
    except:
        pass
    
    try:
        # 右上角装饰
        chara_right = Image.open(Root / 'static/mai/pic/chara-right.png').resize((120, 120)).convert('RGBA')
        bg.alpha_composite(chara_right, (base_width - 150, 40))
    except:
        pass
    
    # 绘制文字
    draw = ImageDraw.Draw(bg)
    
    # 字体设置
    title_font = ImageFont.truetype(str(SIYUAN), 36)
    content_font = ImageFont.truetype(str(SHANGGUMONO), 24)
    small_font = ImageFont.truetype(str(SHANGGUMONO), 20)
    
    # 绘制标题阴影
    title_x, title_y = base_width // 2, 80
    draw.text((title_x + 2, title_y + 2), title, font=title_font, fill=(180, 180, 180))
    draw.text((title_x, title_y), title, font=title_font, fill=(124, 129, 255))
    
    # 绘制搜索类型标签
    type_labels = {
        "search": "关键词搜索",
        "base": "定数搜索", 
        "bpm": "BPM搜索",
        "artist": "曲师搜索",
        "charter": "谱师搜索",
        "alias": "别名搜索",
        "id": "ID搜索"
    }
    type_label = type_labels.get(search_type, "搜索")
    label_x = base_width - 200
    label_y = 30
    draw.text((label_x + 1, label_y + 1), type_label, font=small_font, fill=(180, 180, 180))
    draw.text((label_x, label_y), type_label, font=small_font, fill=(255, 255, 255))
    
    # 绘制内容
    content_x = 50
    content_y = base_height + 20
    
    # 自动换行处理
    max_line_width = base_width - 100  # 左右各留50像素边距
    
    def draw_wrapped_text(text, x, y, font, fill, max_width):
        """绘制自动换行的文字"""
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            if draw.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    lines.append(char)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        # 绘制每一行
        for i, line in enumerate(lines):
            draw.text((x, y + i * (font.size + 4)), line, font=font, fill=fill)
        
        return len(lines) * (font.size + 4)
    
    # 绘制内容文本
    for i, line in enumerate(lines):
        if i == len(lines) - 1:  # 最后一行（页码信息）用不同颜色
            draw_wrapped_text(line, content_x, content_y + i * line_height, content_font, (100, 100, 100), max_line_width)
        else:
            draw_wrapped_text(line, content_x, content_y + i * line_height, content_font, (60, 60, 60), max_line_width)
    
    # 添加底部签名
    signature = "Adapted by AbyssSeeker"
    sig_width = draw.textlength(signature, font=small_font)
    sig_x = base_width - sig_width - 30
    sig_y = total_height - 30
    draw.text((sig_x + 1, sig_y + 1), signature, font=small_font, fill=(180, 180, 180))
    draw.text((sig_x, sig_y), signature, font=small_font, fill=(120, 120, 120))
    
    return bg

def song_level(ds1: float, ds2: float) -> List[Tuple[str, str, float, str]]:
    """
    查询定数范围内的乐曲
    
    Params:
        `ds1`: 定数下限
        `ds2`: 定数上限
    Return:
        `result`: 查询结果
    """
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return []
    result: List[Tuple[str, str, float, str]] = []
    music_data = mai.total_list.filter(ds=(ds1, ds2))
    for music in sorted(music_data, key=lambda x: int(x.id)) if music_data else []:
        if int(music.id) >= 100000:
            continue
        for i in music.diff:
            result.append((music.id, music.title, music.ds[i], diffs[i]))
    return result

def safe_filename(s: str) -> str:
    """生成安全的文件名"""
    return re.sub(r'[<>:"/\\|?*]', '_', s)

# AstrBot 命令处理器实现
async def search_music_handler(event, name: str, page=1):
    """
    关键词搜索命令处理器
    
    Args:
        event: AstrBot 事件对象
        name: 搜索关键词
        page: 页码
    """
    try:
        name = name.strip()
        if not name:
            return await output_manager.send_text(event, '请输入关键词')
        
        if not hasattr(mai, 'total_list'):
            return await output_manager.send_text(event, '曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        
        result = mai.total_list.filter(title_search=name)
        if len(result) == 0:
            return await output_manager.send_text(event, '没有找到这样的乐曲。\n※ 如果是别名请使用「xxx是什么歌」指令来查询哦。')
        
        if len(result) == 1:
            img = await draw_music_info(result.random(), None)
            if isinstance(img, Image.Image):
                return await output_manager.send_image(event, img, f"search_music_{safe_filename(name)}.png", f"搜索结果: {name}")
            else:
                return await output_manager.send_text(event, str(img))
        
        search_result = ''
        total_pages = len(result) // SONGS_PER_PAGE + 1
        page = int(page) if isinstance(page, int) or (isinstance(page, str) and page.isdigit()) else 1
        if page < 1 or page > total_pages:
            page = 1
        
        start_idx = (page - 1) * SONGS_PER_PAGE
        end_idx = min(start_idx + SONGS_PER_PAGE, len(result))
        
        for i in range(start_idx, end_idx):
            music = result[i]
            search_result += f'{music.id}. {music.title}\n'
        
        search_result += f'\n第 {page}/{total_pages} 页，共 {len(result)} 首歌曲'
        
        # 创建图片
        img = create_beautiful_search_image(f"关键词搜索: {name}", search_result, "search")
        return await output_manager.send_image(event, img, f"search_music_{safe_filename(name)}_p{page}.png", f"关键词搜索: {name}")
    except Exception as e:
        return await error_handler.handle_error(event, e, "关键词搜索失败")

async def search_base_handler(event, args: str):
    """
    定数搜索命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串，格式为 "定数下限 定数上限"
    """
    try:
        args = args.strip()
        if not args:
            return await output_manager.send_text(event, '请输入定数范围，例如: 12 13')
        
        parts = args.split()
        if len(parts) != 2:
            return await output_manager.send_text(event, '格式错误，请输入两个数字，例如: 12 13')
        
        try:
            ds1 = float(parts[0])
            ds2 = float(parts[1])
        except ValueError:
            return await output_manager.send_text(event, '定数必须是数字')
        
        if ds1 > ds2:
            ds1, ds2 = ds2, ds1
        
        result = song_level(ds1, ds2)
        if not result:
            return await output_manager.send_text(event, f'没有找到定数在 {ds1}~{ds2} 之间的乐曲')
        
        search_result = f'定数范围: {ds1}~{ds2}\n\n'
        for music_id, title, ds, diff in result:
            search_result += f'{music_id}. {title} ({diff} {ds})\n'
        
        search_result += f'\n共找到 {len(result)} 首歌曲'
        
        # 创建图片
        img = create_beautiful_search_image(f"定数搜索: {ds1}~{ds2}", search_result, "base")
        return await output_manager.send_image(event, img, f"search_base_{ds1}_{ds2}.png", f"定数搜索: {ds1}~{ds2}")
    except Exception as e:
        return await error_handler.handle_error(event, e, "定数搜索失败")

async def search_bpm_handler(event, args: str):
    """
    BPM搜索命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串，格式为 "BPM下限 BPM上限"
    """
    try:
        args = args.strip()
        if not args:
            return await output_manager.send_text(event, '请输入BPM范围，例如: 120 140')
        
        parts = args.split()
        if len(parts) != 2:
            return await output_manager.send_text(event, '格式错误，请输入两个数字，例如: 120 140')
        
        try:
            bpm1 = float(parts[0])
            bpm2 = float(parts[1])
        except ValueError:
            return await output_manager.send_text(event, 'BPM必须是数字')
        
        if bpm1 > bpm2:
            bpm1, bpm2 = bpm2, bpm1
        
        if not hasattr(mai, 'total_list'):
            return await output_manager.send_text(event, '曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        
        result = mai.total_list.filter(bpm=(bpm1, bpm2))
        if not result:
            return await output_manager.send_text(event, f'没有找到BPM在 {bpm1}~{bpm2} 之间的乐曲')
        
        search_result = f'BPM范围: {bpm1}~{bpm2}\n\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            search_result += f'{music.id}. {music.title} (BPM: {music.bpm})\n'
        
        search_result += f'\n共找到 {len(result)} 首歌曲'
        
        # 创建图片
        img = create_beautiful_search_image(f"BPM搜索: {bpm1}~{bpm2}", search_result, "bpm")
        return await output_manager.send_image(event, img, f"search_bpm_{bpm1}_{bpm2}.png", f"BPM搜索: {bpm1}~{bpm2}")
    except Exception as e:
        return await error_handler.handle_error(event, e, "BPM搜索失败")

async def search_artist_handler(event, args: str):
    """
    曲师搜索命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 曲师名称
    """
    try:
        args = args.strip()
        if not args:
            return await output_manager.send_text(event, '请输入曲师名称')
        
        if not hasattr(mai, 'total_list'):
            return await output_manager.send_text(event, '曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        
        result = mai.total_list.filter(artist_search=args)
        if not result:
            return await output_manager.send_text(event, f'没有找到曲师为 "{args}" 的乐曲')
        
        search_result = f'曲师: {args}\n\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            search_result += f'{music.id}. {music.title}\n'
        
        search_result += f'\n共找到 {len(result)} 首歌曲'
        
        # 创建图片
        img = create_beautiful_search_image(f"曲师搜索: {args}", search_result, "artist")
        return await output_manager.send_image(event, img, f"search_artist_{safe_filename(args)}.png", f"曲师搜索: {args}")
    except Exception as e:
        return await error_handler.handle_error(event, e, "曲师搜索失败")

async def search_charter_handler(event, args: str):
    """
    谱师搜索命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 谱师名称
    """
    try:
        args = args.strip()
        if not args:
            return await output_manager.send_text(event, '请输入谱师名称')
        
        if not hasattr(mai, 'total_list'):
            return await output_manager.send_text(event, '曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        
        result = mai.total_list.filter(charter_search=args)
        if not result:
            return await output_manager.send_text(event, f'没有找到谱师为 "{args}" 的乐曲')
        
        search_result = f'谱师: {args}\n\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            search_result += f'{music.id}. {music.title}\n'
        
        search_result += f'\n共找到 {len(result)} 首歌曲'
        
        # 创建图片
        img = create_beautiful_search_image(f"谱师搜索: {args}", search_result, "charter")
        return await output_manager.send_image(event, img, f"search_charter_{safe_filename(args)}.png", f"谱师搜索: {args}")
    except Exception as e:
        return await error_handler.handle_error(event, e, "谱师搜索失败")

async def search_alias_song_handler(event, name: str):
    """
    别名搜索命令处理器
    
    Args:
        event: AstrBot 事件对象
        name: 别名
    """
    try:
        name = name.strip()
        if not name:
            return await output_manager.send_text(event, '请输入别名')
        
        if not hasattr(mai, 'total_alias_list'):
            return await output_manager.send_text(event, '别名库未初始化，请先执行一次主菜单或相关数据加载指令！')
        
        alias_result = mai.total_alias_list.by_alias(name)
        if not alias_result:
            return await output_manager.send_text(event, f'没有找到别名为 "{name}" 的乐曲')
        
        if len(alias_result) == 1:
            # 只有一个结果，直接显示详细信息
            music = mai.total_list.by_id(str(alias_result[0].SongID))
            if music:
                img = await draw_music_info(music, None)
                if isinstance(img, Image.Image):
                    return await output_manager.send_image(event, img, f"alias_{safe_filename(name)}.png", f"别名查询: {name}")
                else:
                    return await output_manager.send_text(event, str(img))
            else:
                return await output_manager.send_text(event, '未找到对应曲目')
        
        # 多个结果，显示列表
        search_result = f'别名: {name}\n\n'
        for alias in alias_result:
            music = mai.total_list.by_id(str(alias.SongID))
            if music:
                search_result += f'{music.id}. {music.title}\n'
        
        search_result += f'\n共找到 {len(alias_result)} 首歌曲'
        
        # 创建图片
        img = create_beautiful_search_image(f"别名搜索: {name}", search_result, "alias")
        return await output_manager.send_image(event, img, f"search_alias_{safe_filename(name)}.png", f"别名搜索: {name}")
    except Exception as e:
        return await error_handler.handle_error(event, e, "别名搜索失败")

async def query_chart_handler(event, id: str):
    """
    谱面查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        id: 曲目ID
    """
    try:
        id = id.strip()
        if not id:
            return await output_manager.send_text(event, '请输入曲目ID')
        
        if not id.isdigit():
            return await output_manager.send_text(event, '曲目ID必须是数字')
        
        if not hasattr(mai, 'total_list'):
            return await output_manager.send_text(event, '曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        
        music = mai.total_list.by_id(id)
        if not music:
            return await output_manager.send_text(event, f'未找到ID为 {id} 的曲目')
        
        img = await draw_music_info(music, None)
        if isinstance(img, Image.Image):
            return await output_manager.send_image(event, img, f"chart_{id}.png", f"谱面查询: {music.title}")
        else:
            return await output_manager.send_text(event, str(img))
    except Exception as e:
        return await error_handler.handle_error(event, e, "谱面查询失败")

# 保留原有的CLI函数以保持向后兼容性
async def search_music_cli(name: str, page=1, user_id=None):
    """CLI版本的关键词搜索（已弃用，请使用search_music_handler）"""
    name = name.strip()
    if not name:
        print('请输入关键词')
        return
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        print('没有找到这样的乐曲。\n※ 如果是别名请使用「xxx是什么歌」指令来查询哦。')
        return
    if len(result) == 1:
        img = await draw_music_info(result.random(), user_id)
        if isinstance(img, Image.Image):
            img_path = Path("output") / f"search_music_{safe_filename(name)}.png"
            img.save(img_path)
            print(f"查歌图片已保存到: {img_path}")
        else:
            print(img)
        return
    search_result = ''
    total_pages = len(result) // SONGS_PER_PAGE + 1
    page = int(page) if isinstance(page, int) or (isinstance(page, str) and page.isdigit()) else 1
    if page < 1 or page > total_pages:
        page = 1
    start_idx = (page - 1) * SONGS_PER_PAGE
    end_idx = min(start_idx + SONGS_PER_PAGE, len(result))
    for i in range(start_idx, end_idx):
        music = result[i]
        search_result += f'{music.id}. {music.title}\n'
    search_result += f'\n第 {page}/{total_pages} 页，共 {len(result)} 首歌曲'
    print(search_result)

async def search_base_cli(args: List[str]):
    """CLI版本的定数搜索（已弃用，请使用search_base_handler）"""
    if len(args) != 2:
        print('格式错误，请输入两个数字，例如: 12 13')
        return
    try:
        ds1 = float(args[0])
        ds2 = float(args[1])
    except ValueError:
        print('定数必须是数字')
        return
    if ds1 > ds2:
        ds1, ds2 = ds2, ds1
    result = song_level(ds1, ds2)
    if not result:
        print(f'没有找到定数在 {ds1}~{ds2} 之间的乐曲')
        return
    search_result = f'定数范围: {ds1}~{ds2}\n\n'
    for music_id, title, ds, diff in result:
        search_result += f'{music_id}. {title} ({diff} {ds})\n'
    search_result += f'\n共找到 {len(result)} 首歌曲'
    print(search_result)

async def search_bpm_cli(args: List[str]):
    """CLI版本的BPM搜索（已弃用，请使用search_bpm_handler）"""
    if len(args) != 2:
        print('格式错误，请输入两个数字，例如: 120 140')
        return
    try:
        bpm1 = float(args[0])
        bpm2 = float(args[1])
    except ValueError:
        print('BPM必须是数字')
        return
    if bpm1 > bpm2:
        bpm1, bpm2 = bpm2, bpm1
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = mai.total_list.filter(bpm=(bpm1, bpm2))
    if not result:
        print(f'没有找到BPM在 {bpm1}~{bpm2} 之间的乐曲')
        return
    search_result = f'BPM范围: {bpm1}~{bpm2}\n\n'
    for music in sorted(result, key=lambda x: int(x.id)):
        search_result += f'{music.id}. {music.title} (BPM: {music.bpm})\n'
    search_result += f'\n共找到 {len(result)} 首歌曲'
    print(search_result)

async def search_artist_cli(args: List[str]):
    """CLI版本的曲师搜索（已弃用，请使用search_artist_handler）"""
    if len(args) != 1:
        print('请输入曲师名称')
        return
    artist = args[0]
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = mai.total_list.filter(artist_search=artist)
    if not result:
        print(f'没有找到曲师为 "{artist}" 的乐曲')
        return
    search_result = f'曲师: {artist}\n\n'
    for music in sorted(result, key=lambda x: int(x.id)):
        search_result += f'{music.id}. {music.title}\n'
    search_result += f'\n共找到 {len(result)} 首歌曲'
    print(search_result)

async def search_charter_cli(args: List[str]):
    """CLI版本的谱师搜索（已弃用，请使用search_charter_handler）"""
    if len(args) != 1:
        print('请输入谱师名称')
        return
    charter = args[0]
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = mai.total_list.filter(charter_search=charter)
    if not result:
        print(f'没有找到谱师为 "{charter}" 的乐曲')
        return
    search_result = f'谱师: {charter}\n\n'
    for music in sorted(result, key=lambda x: int(x.id)):
        search_result += f'{music.id}. {music.title}\n'
    search_result += f'\n共找到 {len(result)} 首歌曲'
    print(search_result)

async def search_alias_song_cli(name: str, user_id=None):
    """CLI版本的别名搜索（已弃用，请使用search_alias_song_handler）"""
    name = name.strip()
    if not name:
        print('请输入别名')
        return
    if not hasattr(mai, 'total_alias_list'):
        print('别名库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    alias_result = mai.total_alias_list.by_alias(name)
    if not alias_result:
        print(f'没有找到别名为 "{name}" 的乐曲')
        return
    if len(alias_result) == 1:
        music = mai.total_list.by_id(str(alias_result[0].SongID))
        if music:
            img = await draw_music_info(music, user_id)
            if isinstance(img, Image.Image):
                img_path = Path("output") / f"alias_{safe_filename(name)}.png"
                img.save(img_path)
                print(f"别名查询图片已保存到: {img_path}")
            else:
                print(img)
        else:
            print('未找到对应曲目')
        return
    search_result = f'别名: {name}\n\n'
    for alias in alias_result:
        music = mai.total_list.by_id(str(alias.SongID))
        if music:
            search_result += f'{music.id}. {music.title}\n'
    search_result += f'\n共找到 {len(alias_result)} 首歌曲'
    print(search_result)

async def query_chart_cli(id: str, user_id=None):
    """CLI版本的谱面查询（已弃用，请使用query_chart_handler）"""
    id = id.strip()
    if not id:
        print('请输入曲目ID')
        return
    if not id.isdigit():
        print('曲目ID必须是数字')
        return
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    music = mai.total_list.by_id(id)
    if not music:
        print(f'未找到ID为 {id} 的曲目')
        return
    img = await draw_music_info(music, user_id)
    if isinstance(img, Image.Image):
        img_path = Path("output") / f"chart_{id}.png"
        img.save(img_path)
        print(f"谱面查询图片已保存到: {img_path}")
    else:
        print(img)