import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from ..libraries.config import Root, SHANGGUMONO, BOTNAME, log
from ..libraries.image import image_to_base64, music_picture, text_to_image, tricolor_gradient, rounded_corners
from ..libraries.maimaidx_api_data import maiApi
from ..libraries.maimaidx_error import *
from ..libraries.maimaidx_music import mai
from ..libraries.maimaidx_music_info import draw_music_info
from ..libraries.maimaidx_player_score import rating_ranking_data
from ..libraries.tool import qqhash
import PIL.Image

# CLI 版全局变量
BOTNAME = "AbyssSeeker"
log = print

# 美观大图渲染

def draw_today_fortune_image(user_id, rp, wm_list, wm_value, music, ds):
    # 画布参数
    width, height = 1000, 500
    bg = tricolor_gradient(width, height)
    # 叠加aurora和pattern
    try:
        aurora = Image.open(Root / 'src/static/mai/pic/aurora.png').resize((width, 220)).convert('RGBA')
        bg.alpha_composite(aurora, (0, 0))
    except Exception:
        pass
    try:
        pattern = Image.open(Root / 'src/static/mai/pic/pattern.png').resize((width, 120)).convert('RGBA')
        bg.alpha_composite(pattern, (0, height-120))
    except Exception:
        pass
    # logo
    try:
        logo = Image.open(Root / 'src/static/mai/pic/logo.png').resize((120, 60)).convert('RGBA')
        bg.alpha_composite(logo, (30, 20))
    except Exception:
        pass
    # 推荐曲绘
    try:
        cover = Image.open(music_picture(music.id)).resize((340, 340))
        cover = rounded_corners(cover, 36, (True, True, True, True))
        bg.paste(cover, (60, 100), cover)
    except Exception:
        pass
    # 卡通小人
    try:
        chara = Image.open(Root / 'src/static/mai/pic/chara-right.png').resize((180, 180)).convert('RGBA')
        bg.alpha_composite(chara, (width-200, height-200))
    except Exception:
        pass
    
    draw = ImageDraw.Draw(bg)
    
    # 字体
    font_title = ImageFont.truetype(str(SHANGGUMONO), 48)
    font_sub = ImageFont.truetype(str(SHANGGUMONO), 32)
    font_text = ImageFont.truetype(str(SHANGGUMONO), 26)
    font_small = ImageFont.truetype(str(SHANGGUMONO), 24)
    
    # 辅助函数：自动换行
    def draw_wrapped_text(text, x, y, font, fill, max_width, line_height=None):
        """绘制自动换行的文字"""
        if line_height is None:
            line_height = font.size + 4
        
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
                    # 单个字符就超长了，强制添加
                    lines.append(char)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        # 绘制每一行
        for i, line in enumerate(lines):
            draw.text((x, y + i * line_height), line, font=font, fill=fill)
        
        return len(lines) * line_height
    
    # 主标题阴影
    title_x, title_y = 440, 40
    draw.text((title_x+2, title_y+2), "今日舞萌运势", font=font_title, fill=(180,180,180))
    draw.text((title_x, title_y), "今日舞萌运势", font=font_title, fill=(124,129,255))
    
    # 人品值
    draw.text((440, 110), f"今日人品值：{rp}", font=font_sub, fill=(60,60,60))
    
    # 宜忌（自动换行）
    y, n = [], []
    for i in range(11):
        if wm_value[i] == 3:
            y.append(wm_list[i])
        elif wm_value[i] == 0:
            n.append(wm_list[i])
    
    current_y = 160
    max_text_width = 520  # 右侧文字区域最大宽度
    
    # 宜
    yi_text = f"宜：{'、'.join(y) if y else '无'}"
    yi_height = draw_wrapped_text(yi_text, 440, current_y, font_text, (34,139,34), max_text_width)
    current_y += yi_height + 10
    
    # 忌
    ji_text = f"忌：{'、'.join(n) if n else '无'}"
    ji_height = draw_wrapped_text(ji_text, 440, current_y, font_text, (220,20,60), max_text_width)
    current_y += ji_height + 15
    
    # 推荐曲目（自动换行）
    draw.text((440, current_y), "今日推荐：", font=font_sub, fill=(124,129,255))
    current_y += 40
    
    # 曲目标题（自动换行）
    song_text = f"ID.{music.id} - {music.title}"
    song_height = draw_wrapped_text(song_text, 440, current_y, font_text, (60,60,60), max_text_width)
    current_y += song_height + 10
    
    # 难度
    draw.text((440, current_y), f"难度：{ds}", font=font_text, fill=(60,60,60))
    current_y += 40
    
    # 提醒（自动换行）- 固定底部居中
    remind = f"{BOTNAME} Bot提醒：打机时不要大力拍打或滑动哦"
    remind_y = height - 60  # 距离底部60像素
    def draw_centered_wrapped_text(text, y, font, fill, max_width):
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
        for i, line in enumerate(lines):
            x = width // 2 - draw.textlength(line, font=font) // 2
            draw.text((x, y + i * (font.size + 4)), line, font=font, fill=fill)
        return len(lines) * (font.size + 4)
    draw_centered_wrapped_text(remind, remind_y, font_small, (120,120,120), width-100)
    
    # 签名（确保不超出右边界）
    signature = "Adapted by AbyssSeeker"
    sig_width = draw.textlength(signature, font=font_small)
    sig_x = min(width - sig_width - 20, width - 320)  # 确保不超出右边界，最小距离右边界20像素
    draw.text((sig_x, height-32), signature, font=font_small, fill=(180,180,180))
    
    return bg

# CLI 版指令实现

def maimaidxhelp_cli():
    help_img = Image.open((Root / 'maimaidxhelp.png'))
    out_path = Path("help_image.png")
    help_img.save(out_path)
    print(f"帮助图片已保存到: {out_path}")

def maimaidxrepo_cli():
    print('项目地址：https://github.com/Yuri-YuzuChaN/maimaiDX\n求star，求宣传~')

async def mai_today_cli(user_id=None):
    # 如果没有提供user_id，随机生成一个
    if user_id is None:
        user_id = random.randint(100000000, 999999999)
    
    wm_list = [
        '拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌'
    ]
    h = qqhash(user_id)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    music = mai.total_list[h % len(mai.total_list)]
    ds = '/'.join([str(_) for _ in music.ds])
    # 渲染大图
    img = draw_today_fortune_image(user_id, rp, wm_list, wm_value, music, ds)
    img_path = Path(f"today_fortune_{user_id}.png")
    img.save(img_path)
    print(f"今日舞萌大图已保存到: {img_path}")
    return img_path

async def mai_what_cli(user_id, point=None):
    music = mai.total_list.random()
    user = None
    if point and ('推分' in point or '上分' in point or '加分' in point):
        try:
            user = await maiApi.query_user_b50(qqid=user_id)
            r = random.randint(0, 1)
            _ra = 0
            ignore = []
            if r == 0:
                charts_sd = getattr(user.charts, 'sd', None)
                if charts_sd:
                    ignore = [m.song_id for m in charts_sd if m.achievements < 100.5]
                    _ra = charts_sd[-1].ra
            else:
                charts_dx = getattr(user.charts, 'dx', None)
                if charts_dx:
                    ignore = [m.song_id for m in charts_dx if m.achievements < 100.5]
                    _ra = charts_dx[-1].ra
            if _ra != 0:
                ds = round(_ra / 22.4, 1)
                musiclist = mai.total_list.filter(ds=(ds, ds + 1))
                for _m in musiclist:
                    if int(_m.id) in ignore:
                        musiclist.remove(_m)
                music = musiclist.random()
        except (UserNotFoundError, UserDisabledQueryError):
            pass
    # 绘制并保存图片
    img = await draw_music_info(music, user_id, user)
    img_path = Path(f"what_song_{music.id}.png")
    if isinstance(img, PIL.Image.Image):
        img.save(img_path)
        print(f"推荐曲目信息图片已保存到: {img_path}")
    else:
        print(img)

async def random_song_cli(user_id, diff, color, level):
    try:
        if diff == 'dx':
            tp = ['DX']
        elif diff == 'sd' or diff == '标准':
            tp = ['SD']
        else:
            tp = ['SD', 'DX']
        if color == '':
            music_data = mai.total_list.filter(level=level, type=tp)
        else:
            music_data = mai.total_list.filter(level=level, diff=['绿黄红紫白'.index(color)], type=tp)
        if len(music_data) == 0:
            msg = '没有这样的乐曲哦。'
            print(msg)
        else:
            img = await draw_music_info(music_data.random(), user_id)
            img_path = Path(f"random_song_{level}_{diff or 'all'}.png")
            if isinstance(img, PIL.Image.Image):
                img.save(img_path)
                print(f"随机曲目信息图片已保存到: {img_path}")
            else:
                print(img)
    except Exception as e:
        print(f'随机命令错误，请检查语法: {e}')

async def rating_ranking_cli(user_id, args):
    page = 1
    name = ''
    if args.isdigit():
        page = int(args)
    else:
        name = args.lower()
    pic = await rating_ranking_data(name, page)
    img_path = Path(f"rating_ranking_{name or page}.png")
    if isinstance(pic, PIL.Image.Image):
        pic.save(img_path)
        print(f"排名图片已保存到: {img_path}")
    else:
        print(pic)

async def my_rating_ranking_cli(user_id):
    try:
        user = await maiApi.query_user_b50(qqid=user_id)
        rank_data = await maiApi.rating_ranking()
        for num, rank in enumerate(rank_data):
            if rank.username == user.username:
                result = f'您的Rating为「{rank.ra}」，排名第「{num + 1}」名'
                print(result)
                return
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        print(str(e))
