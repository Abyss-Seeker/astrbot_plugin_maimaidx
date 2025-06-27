import re
from re import Match
from typing import List, Tuple
from libraries.config import Root, SIYUAN, SHANGGUMONO, diffs, SONGS_PER_PAGE
from libraries.image import image_to_base64, text_to_image, tricolor_gradient, rounded_corners
from libraries.maimaidx_api_data import maiApi
from libraries.maimaidx_error import *
from libraries.maimaidx_model import AliasStatus
from libraries.maimaidx_music import guess, mai
from libraries.maimaidx_music_info import draw_music_info
import PIL.Image
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

OUTPUT_DIR = Path(__file__).parent.parent / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

def log(*args, **kwargs):
    print(*args, **kwargs)

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

async def search_music_cli(name: str, page=1, user_id=None):
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
        if isinstance(img, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"search_music_{safe_filename(name)}.png"
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
    result.sort(key=lambda i: int(i.id))
    for i, music in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{music.id}」":<7} {music.title}\n'
    search_result += (
        f'第「{page}」页，'
        f'共「{total_pages}」页。'
        '请使用「id xxxxx」查询指定曲目。'
    )
    
    # 使用美观渲染
    title = f"关键词搜索：{name}"
    img = create_beautiful_search_image(title, search_result, "search")
    img_path = OUTPUT_DIR / f"search_music_list_{safe_filename(name)}_{page}.png"
    img.save(img_path)
    print(f"查歌列表图片已保存到: {img_path}")

async def search_base_cli(args: List[str]):
    if len(args) > 3 or len(args) == 0:
        print('命令格式：\n定数查歌 「定数」「页数」\n定数查歌 「定数下限」「定数上限」「页数」')
        return
    page = 1
    if len(args) == 1:
        ds1, ds2 = args[0], args[0]
    elif len(args) == 2:
        if '.' in args[1]:
            ds1, ds2 = args
        elif args[1].isdigit():
            ds1, ds2 = args[0], args[0]
            page = int(args[1])
        else:
            ds1, ds2 = args[0], args[0]
    else:
        ds1, ds2, page = args
        page = int(page) if str(page).isdigit() else 1
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = song_level(float(ds1), float(ds2))
    if not result:
        print('没有找到这样的乐曲。')
        return
    if result is None or len(result) == 0:
        return
    search_result = ''
    total_pages = len(result) // SONGS_PER_PAGE + 1
    page = int(page) if isinstance(page, int) or (isinstance(page, str) and str(page).isdigit()) else 1
    if page < 1 or page > total_pages:
        page = 1
    for i, _result in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            id, title, ds, diff = _result
            search_result += f'{f"「{id}」":<7}{f"「{diff}」":<11}{f"「{ds}」"} {title}\n'
    search_result += (
        f'第「{page}」页，'
        f'共「{total_pages}」页。'
        '请使用「id xxxxx」查询指定曲目。'
    )
    
    # 使用美观渲染
    title = f"定数搜索：{ds1} - {ds2}"
    img = create_beautiful_search_image(title, search_result, "base")
    img_path = OUTPUT_DIR / f"search_base_{safe_filename(str(ds1))}_{safe_filename(str(ds2))}_{page}.png"
    img.save(img_path)
    print(f"定数查歌图片已保存到: {img_path}")

async def search_bpm_cli(args: List[str]):
    if len(args) == 1:
        bpm = int(args[0])
        page = 1
        result = mai.total_list.filter(bpm=bpm)
    elif len(args) == 2:
        if '.' in args[1]:
            bpm = int(args[0])
            result = mai.total_list.filter(bpm=bpm)
            page = 1
        elif args[1].isdigit():
            bpm = int(args[0])
            page = int(args[1])
            result = mai.total_list.filter(bpm=bpm)
        else:
            bpm = int(args[0])
            result = mai.total_list.filter(bpm=bpm)
            page = 1
    elif len(args) == 3:
        bpm = int(args[0])
        bpm2 = int(args[1])
        page = int(args[2]) if args[2].isdigit() else 1
        result = mai.total_list.filter(bpm=(bpm, bpm2))
    else:
        print('命令格式：\nbpm查歌 「bpm」\nbpm查歌 「bpm下限」「bpm上限」「页数」')
        return
    if not result:
        print('没有找到这样的乐曲。')
        return
    if result is None or len(result) == 0:
        return
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    search_result = ''
    total_pages = len(result) // SONGS_PER_PAGE + 1
    page = int(page) if isinstance(page, int) or (isinstance(page, str) and page.isdigit()) else 1
    if page < 1 or page > total_pages:
        page = 1
    result.sort(key=lambda x: int(x.basic_info.bpm))
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{m.id}」":<7}{f"「BPM {m.basic_info.bpm}」":<9} {m.title} \n'
    search_result += (
        f'第「{page}」页，'
        f'共「{total_pages}」页。'
        '请使用「id xxxxx」查询指定曲目。'
    )
    
    # 使用美观渲染
    title = f"BPM搜索：{bpm}"
    if len(args) == 3:
        title = f"BPM搜索：{bpm} - {bpm2}"
    img = create_beautiful_search_image(title, search_result, "bpm")
    img_path = OUTPUT_DIR / f"search_bpm_{safe_filename(str(page))}.png"
    img.save(img_path)
    print(f"bpm查歌图片已保存到: {img_path}")

def safe_filename(s: str) -> str:
    return re.sub(r'[\\/*?<>|:"\n\r]', '_', s)

async def search_artist_cli(args: List[str]):
    if len(args) == 1:
        artist_name = args[0]
        page = 1
    elif len(args) == 2:
        artist_name = args[0]
        page = int(args[1]) if args[1].isdigit() else 1
    else:
        print('命令格式：\n曲师查歌「曲师名称」「页数」')
        return
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = mai.total_list.filter(artist_search=artist_name)
    if not result:
        print('没有找到这样的乐曲。')
        return
    if result is None or len(result) == 0:
        return
    search_result = ''
    total_pages = len(result) // SONGS_PER_PAGE + 1
    page = int(page) if isinstance(page, int) or (isinstance(page, str) and str(page).isdigit()) else 1
    if page < 1 or page > total_pages:
        page = 1
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{m.id}」":<7}{f"「{m.basic_info.artist}」"} - {m.title}\n'
    search_result += (
        f'第「{page}」页，'
        f'共「{total_pages}」页。'
        '请使用「id xxxxx」查询指定曲目。'
    )
    
    # 使用美观渲染
    title = f"曲师搜索：{artist_name}"
    img = create_beautiful_search_image(title, search_result, "artist")
    safe_artist = safe_filename(artist_name)
    img_path = OUTPUT_DIR / f"search_artist_{safe_artist}_{page}.png"
    img.save(img_path)
    print(f"曲师查歌图片已保存到: {img_path}")

async def search_charter_cli(args: List[str]):
    if len(args) == 1:
        charter_name = args[0]
        page = 1
    elif len(args) == 2:
        charter_name = args[0]
        page = int(args[1]) if args[1].isdigit() else 1
    else:
        print('命令格式：\n谱师查歌「谱师名称」「页数」')
        return
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    result = mai.total_list.filter(charter_search=charter_name)
    if not result:
        print('没有找到这样的乐曲。')
        return
    if result is None or len(result) == 0:
        return
    search_result = ''
    total_pages = len(result) // SONGS_PER_PAGE + 1
    page = int(page) if isinstance(page, int) or (isinstance(page, str) and str(page).isdigit()) else 1
    if page < 1 or page > total_pages:
        page = 1
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip([SONGS_PER_PAGE.diffs[d] for d in m.diff], [m.charts[d].charter for d in m.diff])
            diff_parts = [
                f"{f'「{d}」':<9}{f'「{c}」'}"
                for d, c in diff_charter
            ]
            diff_str = " ".join(diff_parts)
            line = f"{f'「{m.id}」':<7}{diff_str} {m.title}\n"
            search_result += line
    search_result += (
        f'第「{page}」页，'
        f'共「{total_pages}」页。'
        '请使用「id xxxxx」查询指定曲目。'
    )
    
    # 使用美观渲染
    title = f"谱师搜索：{charter_name}"
    img = create_beautiful_search_image(title, search_result, "charter")
    safe_charter = safe_filename(charter_name)
    img_path = OUTPUT_DIR / f"search_charter_{safe_charter}_{page}.png"
    img.save(img_path)
    print(f"谱师查歌图片已保存到: {img_path}")

async def search_alias_song_cli(name: str, user_id=None):
    name = name.strip().lower()
    error_msg = (
        f'未找到别名为「{name}」的歌曲\n'
        '※ 可以使用「添加别名」指令给该乐曲添加别名\n'
        '※ 如果是歌名的一部分，请使用「查歌」指令查询哦。'
    )
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        try:
            obj = await maiApi.get_songs(name)
            if obj:
                if obj and isinstance(obj[0], AliasStatus):
                    msg = f'未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n'
                    for _s in obj:
                        if hasattr(_s, 'Tag') and hasattr(_s, 'SongID'):
                            msg += f'- {_s.Tag}\n    ID {_s.SongID}: {name}\n'
                    msg += f'※ 可以使用指令「同意别名 {_s.Tag}」进行投票'
                    print(msg.strip())
                    return
                else:
                    alias_data = obj
        except AliasesNotFoundError:
            pass
    if alias_data:
        if len(alias_data) != 1:
            msg = f'找到{len(alias_data)}个相同别名的曲目：\n'
            for songs in alias_data:
                msg += f'{songs.SongID}：{songs.Name}\n'
            msg += '※ 请使用「id xxxxx」查询指定曲目'
            
            # 使用美观渲染
            title = f"别名搜索：{name}"
            img = create_beautiful_search_image(title, msg, "alias")
            img_path = OUTPUT_DIR / f"alias_song_list_{safe_filename(name)}.png"
            img.save(img_path)
            print(f"别名查歌列表图片已保存到: {img_path}")
            return
        else:
            music = mai.total_list.by_id(str(alias_data[0].SongID))
            if music:
                img = await draw_music_info(music, user_id)
                if isinstance(img, PIL.Image.Image):
                    img_path = OUTPUT_DIR / f"alias_song_{name}.png"
                    img.save(img_path)
                    print(f"别名查歌图片已保存到: {img_path}")
                else:
                    print(img)
                return
            else:
                print(error_msg)
                return
    if name.isdigit() and (music := mai.total_list.by_id(name)):
        img = await draw_music_info(music, user_id)
        if isinstance(img, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"alias_song_id_{name}.png"
            img.save(img_path)
            print(f"ID查歌图片已保存到: {img_path}")
        else:
            print(img)
        return
    if search_id := re.search(r'^id([0-9]*)$', name, re.IGNORECASE):
        music = mai.total_list.by_id(search_id.group(1))
        img = await draw_music_info(music, user_id)
        if isinstance(img, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"alias_song_id_{search_id.group(1)}.png"
            img.save(img_path)
            print(f"ID查歌图片已保存到: {img_path}")
        else:
            print(img)
        return
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        print(error_msg)
    elif len(result) == 1:
        img = await draw_music_info(result.random(), user_id)
        if isinstance(img, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"alias_song_title_{name}.png"
            img.save(img_path)
            print(f"标题查歌图片已保存到: {img_path}")
        else:
            print(img)
    elif len(result) < 50:
        msg = f'未找到别名为「{name}」的歌曲，但找到「{len(result)}」个相似标题的曲目：\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            msg += f'{f"「{music.id}」":<7} {music.title}\n'
        msg += '请使用「id xxxxx」查询指定曲目。'
        
        # 使用美观渲染
        title = f"别名搜索：{name} (相似标题)"
        img = create_beautiful_search_image(title, msg, "alias")
        img_path = OUTPUT_DIR / f"alias_song_similar_{safe_filename(name)}.png"
        img.save(img_path)
        print(f"别名查歌相似标题图片已保存到: {img_path}")
    else:
        print(f'结果过多「{len(result)}」条，请缩小查询范围。')

async def query_chart_cli(id: str, user_id=None):
    if not hasattr(mai, 'total_list'):
        print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
        return
    music = mai.total_list.by_id(id)
    if music:
        img = await draw_music_info(music, user_id)
        if isinstance(img, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"query_chart_{id}.png"
            img.save(img_path)
            print(f"id查歌图片已保存到: {img_path}")
        else:
            print(img)
    else:
        print(f'未找到ID为「{id}」的乐曲')