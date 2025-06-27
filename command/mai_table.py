import re
from re import Match
from libraries.config import ratingdir, levelList, platecn, combo_rank, scoreRank, syncRank, Root
from libraries.maimaidx_music_info import (
    draw_plate_table,
    draw_rating,
    draw_rating_table,
)
from libraries.maimaidx_player_score import (
    level_achievement_list_data,
    level_process_data,
    player_plate_data,
    rise_score_data,
)
from libraries.maimaidx_update_table import update_plate_table, update_rating_table
import PIL.Image
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

def log(*args, **kwargs):
    print(*args, **kwargs)

async def update_rating_table_cli():
    result = await update_rating_table()
    print(result)

async def update_plate_table_cli():
    result = await update_plate_table()
    print(result)

async def rating_table_cli(args: str, username: str = 'default'):
    # 支持"定数表 14+"或"14+定数表"两种格式
    args = args.strip()
    m = re.match(r'^(\d+\+?)定数表$', args)
    if m:
        rating = m.group(1)
        path = ratingdir / f'{rating}.png'
        if path.exists():
            pic = draw_rating(rating, path)
            if isinstance(pic, PIL.Image.Image):
                img_path = OUTPUT_DIR / f"rating_table_{rating}.png"
                pic.save(img_path)
                print(f"定数表图片已保存到: {img_path}")
            else:
                print(pic)
        else:
            print(f'未找到定数表图片: {path}')
        return
    m = re.match(r'^定数表\s*(\d+\+?)$', args)
    if m:
        rating = m.group(1)
        path = ratingdir / f'{rating}.png'
        if path.exists():
            pic = draw_rating(rating, path)
            if isinstance(pic, PIL.Image.Image):
                img_path = OUTPUT_DIR / f"rating_table_{rating}.png"
                pic.save(img_path)
                print(f"定数表图片已保存到: {img_path}")
            else:
                print(pic)
        else:
            print(f'未找到定数表图片: {path}')
        return
    # 兼容原有参数
    if args in levelList[:6]:
        print('只支持查询lv7-15的定数表')
    elif args in levelList[6:]:
        path = ratingdir / f'{args}.png'
        if path.exists():
            pic = draw_rating(args, path)
            if isinstance(pic, PIL.Image.Image):
                img_path = OUTPUT_DIR / f"rating_table_{args}.png"
                pic.save(img_path)
                print(f"定数表图片已保存到: {img_path}")
            else:
                print(pic)
        else:
            print(f'未找到定数表图片: {path}')
    else:
        print('无法识别的定数')

async def table_pfm_cli(username, args: str):
    # 支持"华将完成表 jerri-"或"华将完成表"
    args = args.strip()
    # 1. 数字完成表（定数完成表）
    m = re.match(r'^(\d+\+?)完成表(?:\s+(\S+))?$', args)
    if m:
        ra = m.group(1)
        user = m.group(2) if m.group(2) else username or 'default'
        # 数字完成表（定数表+成绩）
        result = await draw_rating_table(user, ra, False)
        if isinstance(result, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"table_pfm_{user}_{ra}.png"
            result.save(img_path)
            print(f"完成表图片已保存到: {img_path}")
        else:
            print(result)
        return
    # 2. 文字完成表：段位+完成表
    m = re.match(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜])([極极将舞神者]舞?)完成表(?:\s+(\S+))?$', args)
    if m:
        ver = m.group(1)
        plan = m.group(2)
        user = m.group(3) if m.group(3) else username or 'default'
        if ver in platecn:
            ver = platecn[ver]
        if ver in ['舞', '霸']:
            print('暂不支持查询「舞」系和「霸者」的牌子')
            return
        if f'{ver}{plan}' == '真将':
            print('真系没有真将哦')
            return
        # 文字完成表（段位）
        result = await draw_plate_table(user, ver, plan)
        if isinstance(result, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"table_pfm_{user}_{ver}{plan}.png"
            result.save(img_path)
            print(f"完成表图片已保存到: {img_path}")
        else:
            print(result)
        return
    # 3. 图片完成表
    plate = re.match(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜])([極极将舞神者]舞?)$', args)
    if plate:
        ver = plate.group(1)
        plan = plate.group(2)
        user = username or 'default'
        if ver in platecn:
            ver = platecn[ver]
        if ver in ['舞', '霸']:
            print('暂不支持查询「舞」系和「霸者」的牌子')
            return
        if f'{ver}{plan}' == '真将':
            print('真系没有真将哦')
            return
        pic = await draw_plate_table(user, ver, plan)
        if isinstance(pic, PIL.Image.Image):
            img_path = OUTPUT_DIR / f"table_plate_{user}_{ver}{plan}.png"
            pic.save(img_path)
            print(f"完成表图片已保存到: {img_path}")
        else:
            print(pic)
        return
    # 4. 定数图片完成表
    rating = re.match(r'^([0-9]+\+?)(app|fcp|ap|fc)?$', args, re.IGNORECASE)
    if rating:
        ra = rating.group(1)
        plan = rating.group(2)
        user = username or 'default'
        if ra in levelList[5:]:
            pic = await draw_rating_table(user, ra, True if plan and plan.lower() in combo_rank else False)
            if isinstance(pic, PIL.Image.Image):
                img_path = OUTPUT_DIR / f"table_pfm_{user}_{ra}.png"
                pic.save(img_path)
                print(f"完成表图片已保存到: {img_path}")
            else:
                print(pic)
        else:
            print('只支持查询lv6-15的完成表')
        return
    print('无法识别的表格')

async def rise_score_cli(user_id, rating=None, score=None, username=None):
    data = await rise_score_data(user_id, username, rating, score)
    print(data)

async def plate_process_cli(user_id, ver, plan, username=None):
    if f'{ver}{plan}' == '真将':
        print('真系没有真将哦')
        return
    username = username if username is not None else ''
    data = await player_plate_data(user_id, username, ver, plan)
    print(data)

async def level_process_cli(user_id, level, plan, category=None, page=1, username=None):
    if level not in levelList:
        print('无此等级')
        return
    if plan.lower() not in scoreRank + combo_rank + syncRank:
        print('无此评价等级')
        return
    if levelList.index(level) < 11 or (plan.lower() in scoreRank and scoreRank.index(plan.lower()) < 8):
        print('兄啊，有点志向好不好')
        return
    if category:
        if category in ['已完成', '未完成', '未开始', '未游玩']:
            _c = {
                '已完成': 'completed',
                '未完成': 'unfinished',
                '未开始': 'notstarted',
                '未游玩': 'notstarted'
            }
            category = _c[category]
        else:
            print(f'无法指定查询「{category}」')
            return
    else:
        category = 'default'
    data = await level_process_data(user_id, username, level, plan, category, int(page) if page else 1)
    print(data)

async def level_achievement_list_cli(user_id, rating, page=1, username=None):
    try:
        if '.' in str(rating):
            rating = round(float(rating), 1)
        elif rating not in levelList:
            print('无此等级')
            return
    except ValueError:
        if rating not in levelList:
            print('无此等级')
            return
    data = await level_achievement_list_data(user_id, username, rating, int(page) if page else 1)
    print(data)