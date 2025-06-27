import re
from re import Match
from pathlib import Path
from PIL import Image

from ..libraries.config import ratingdir, levelList, platecn, combo_rank, scoreRank, syncRank, Root
from ..libraries.maimaidx_music_info import (
    draw_plate_table,
    draw_rating,
    draw_rating_table,
)
from ..libraries.maimaidx_player_score import (
    level_achievement_list_data,
    level_process_data,
    player_plate_data,
    rise_score_data,
)
from ..libraries.maimaidx_update_table import update_plate_table, update_rating_table

from ..output_manager import OutputManager
from ..error_handler import ErrorHandler

# 初始化输出管理器和错误处理器
output_manager = OutputManager()
error_handler = ErrorHandler()

# AstrBot 命令处理器实现
async def update_rating_table_handler(event):
    """
    更新定数表命令处理器
    
    Args:
        event: AstrBot 事件对象
    """
    try:
        result = await update_rating_table()
        return output_manager.send_text(event, result)
    except Exception as e:
        return error_handler.handle_error(event, e, "定数表更新失败")

async def update_plate_table_handler(event):
    """
    更新段位表命令处理器
    
    Args:
        event: AstrBot 事件对象
    """
    try:
        result = await update_plate_table()
        return output_manager.send_text(event, result)
    except Exception as e:
        return error_handler.handle_error(event, e, "段位表更新失败")

async def rating_table_handler(event, args: str):
    """
    定数表查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串，支持"定数表 14+"或"14+定数表"两种格式
    """
    try:
        args = args.strip()
        
        # 支持"定数表 14+"或"14+定数表"两种格式
        m = re.match(r'^(\d+\+?)定数表$', args)
        if m:
            rating = m.group(1)
            path = ratingdir / f'{rating}.png'
            if path.exists():
                pic = draw_rating(rating, path)
                if isinstance(pic, Image.Image):
                    return output_manager.send_image(event, pic, f"rating_table_{rating}.png", f"{rating}定数表")
                else:
                    return output_manager.send_text(event, str(pic))
            else:
                return output_manager.send_text(event, f'未找到定数表图片: {path}')
        
        m = re.match(r'^定数表\s*(\d+\+?)$', args)
        if m:
            rating = m.group(1)
            path = ratingdir / f'{rating}.png'
            if path.exists():
                pic = draw_rating(rating, path)
                if isinstance(pic, Image.Image):
                    return output_manager.send_image(event, pic, f"rating_table_{rating}.png", f"{rating}定数表")
                else:
                    return output_manager.send_text(event, str(pic))
            else:
                return output_manager.send_text(event, f'未找到定数表图片: {path}')
        
        # 兼容原有参数
        if args in levelList[:6]:
            return output_manager.send_text(event, '只支持查询lv7-15的定数表')
        elif args in levelList[6:]:
            path = ratingdir / f'{args}.png'
            if path.exists():
                pic = draw_rating(args, path)
                if isinstance(pic, Image.Image):
                    return output_manager.send_image(event, pic, f"rating_table_{args}.png", f"{args}定数表")
                else:
                    return output_manager.send_text(event, str(pic))
            else:
                return output_manager.send_text(event, f'未找到定数表图片: {path}')
        else:
            return output_manager.send_text(event, '无法识别的定数')
    except Exception as e:
        return error_handler.handle_error(event, e, "定数表查询失败")

async def table_pfm_handler(event, args: str):
    """
    完成表查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        args: 参数字符串
    """
    try:
        args = args.strip()
        username = event.sender.name if hasattr(event, 'sender') else 'default'
        
        # 1. 数字完成表（定数完成表）
        m = re.match(r'^(\d+\+?)完成表(?:\s+(\S+))?$', args)
        if m:
            ra = m.group(1)
            user = m.group(2) if m.group(2) else username
            # 数字完成表（定数表+成绩）
            result = await draw_rating_table(user, ra, False)
            if isinstance(result, Image.Image):
                return output_manager.send_image(event, result, f"table_pfm_{user}_{ra}.png", f"{user}的{ra}完成表")
            else:
                return output_manager.send_text(event, str(result))
        
        # 2. 文字完成表：段位+完成表
        m = re.match(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜])([極极将舞神者]舞?)完成表(?:\s+(\S+))?$', args)
        if m:
            ver = m.group(1)
            plan = m.group(2)
            user = m.group(3) if m.group(3) else username
            if ver in platecn:
                ver = platecn[ver]
            if ver in ['舞', '霸']:
                return output_manager.send_text(event, '暂不支持查询「舞」系和「霸者」的牌子')
            if f'{ver}{plan}' == '真将':
                return output_manager.send_text(event, '真系没有真将哦')
            # 文字完成表（段位）
            result = await draw_plate_table(user, ver, plan)
            if isinstance(result, Image.Image):
                return output_manager.send_image(event, result, f"table_pfm_{user}_{ver}{plan}.png", f"{user}的{ver}{plan}完成表")
            else:
                return output_manager.send_text(event, str(result))
        
        # 3. 图片完成表
        plate = re.match(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜])([極极将舞神者]舞?)$', args)
        if plate:
            ver = plate.group(1)
            plan = plate.group(2)
            user = username
            if ver in platecn:
                ver = platecn[ver]
            if ver in ['舞', '霸']:
                return output_manager.send_text(event, '暂不支持查询「舞」系和「霸者」的牌子')
            if f'{ver}{plan}' == '真将':
                return output_manager.send_text(event, '真系没有真将哦')
            pic = await draw_plate_table(user, ver, plan)
            if isinstance(pic, Image.Image):
                return output_manager.send_image(event, pic, f"table_plate_{user}_{ver}{plan}.png", f"{user}的{ver}{plan}完成表")
            else:
                return output_manager.send_text(event, str(pic))
        
        # 4. 定数图片完成表
        rating = re.match(r'^([0-9]+\+?)(app|fcp|ap|fc)?$', args, re.IGNORECASE)
        if rating:
            ra = rating.group(1)
            plan = rating.group(2)
            user = username
            if ra in levelList[5:]:
                pic = await draw_rating_table(user, ra, True if plan and plan.lower() in combo_rank else False)
                if isinstance(pic, Image.Image):
                    return output_manager.send_image(event, pic, f"table_pfm_{user}_{ra}.png", f"{user}的{ra}完成表")
                else:
                    return output_manager.send_text(event, str(pic))
            else:
                return output_manager.send_text(event, '只支持查询lv6-15的完成表')
        
        return output_manager.send_text(event, '无法识别的表格')
    except Exception as e:
        return error_handler.handle_error(event, e, "完成表查询失败")

async def rise_score_handler(event, rating=None, score=None):
    """
    分数提升查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        rating: 定数
        score: 分数
    """
    try:
        user_id = event.sender.id if hasattr(event, 'sender') else None
        username = event.sender.name if hasattr(event, 'sender') else None
        # 确保user_id是整数类型
        if user_id is not None:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                user_id = 0  # 使用默认值而不是None
        else:
            user_id = 0  # 使用默认值而不是None
        data = await rise_score_data(user_id, username, rating, score)
        return output_manager.send_text(event, str(data))
    except Exception as e:
        return error_handler.handle_error(event, e, "分数提升查询失败")

async def plate_process_handler(event, ver, plan):
    """
    段位进度查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        ver: 段位版本
        plan: 段位计划
    """
    try:
        if f'{ver}{plan}' == '真将':
            return output_manager.send_text(event, '真系没有真将哦')
        
        user_id = event.sender.id if hasattr(event, 'sender') else None
        username = event.sender.name if hasattr(event, 'sender') else ''
        data = await player_plate_data(username, ver, plan)
        return output_manager.send_text(event, str(data))
    except Exception as e:
        return error_handler.handle_error(event, e, "段位进度查询失败")

async def level_process_handler(event, level, plan, category=None, page=1):
    """
    等级进度查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        level: 等级
        plan: 计划
        category: 分类
        page: 页码
    """
    try:
        if level not in levelList:
            return output_manager.send_text(event, '无此等级')
        if plan.lower() not in scoreRank + combo_rank + syncRank:
            return output_manager.send_text(event, '无此评价等级')
        if levelList.index(level) < 11 or (plan.lower() in scoreRank and scoreRank.index(plan.lower()) < 8):
            return output_manager.send_text(event, '兄啊，有点志向好不好')
        
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
                return output_manager.send_text(event, f'无法指定查询「{category}」')
        else:
            category = 'default'
        
        user_id = event.sender.id if hasattr(event, 'sender') else None
        username = event.sender.name if hasattr(event, 'sender') else None
        data = await level_process_data(user_id, username, level, plan, category, page)
        return output_manager.send_text(event, str(data))
    except Exception as e:
        return error_handler.handle_error(event, e, "等级进度查询失败")

async def level_achievement_list_handler(event, rating, page=1):
    """
    等级成就列表查询命令处理器
    
    Args:
        event: AstrBot 事件对象
        rating: 定数
        page: 页码
    """
    try:
        user_id = event.sender.id if hasattr(event, 'sender') else None
        username = event.sender.name if hasattr(event, 'sender') else None
        # 确保user_id是整数类型
        if user_id is not None:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                user_id = 0  # 使用默认值而不是None
        else:
            user_id = 0  # 使用默认值而不是None
        data = await level_achievement_list_data(user_id, username, rating, page)
        return output_manager.send_text(event, str(data))
    except Exception as e:
        return error_handler.handle_error(event, e, "等级成就列表查询失败")

# 保留原有的CLI函数以保持向后兼容性
async def update_rating_table_cli():
    """CLI版本的定数表更新（已弃用，请使用update_rating_table_handler）"""
    result = await update_rating_table()
    print(result)

async def update_plate_table_cli():
    """CLI版本的段位表更新（已弃用，请使用update_plate_table_handler）"""
    result = await update_plate_table()
    print(result)

async def rating_table_cli(args: str, username: str = 'default'):
    """CLI版本的定数表查询（已弃用，请使用rating_table_handler）"""
    # 支持"定数表 14+"或"14+定数表"两种格式
    args = args.strip()
    m = re.match(r'^(\d+\+?)定数表$', args)
    if m:
        rating = m.group(1)
        path = ratingdir / f'{rating}.png'
        if path.exists():
            pic = draw_rating(rating, path)
            if isinstance(pic, Image.Image):
                img_path = Path("output") / f"rating_table_{rating}.png"
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
            if isinstance(pic, Image.Image):
                img_path = Path("output") / f"rating_table_{rating}.png"
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
            if isinstance(pic, Image.Image):
                img_path = Path("output") / f"rating_table_{args}.png"
                pic.save(img_path)
                print(f"定数表图片已保存到: {img_path}")
            else:
                print(pic)
        else:
            print(f'未找到定数表图片: {path}')
    else:
        print('无法识别的定数')

async def table_pfm_cli(username, args: str):
    """CLI版本的完成表查询（已弃用，请使用table_pfm_handler）"""
    # 支持"华将完成表 jerri-"或"华将完成表"
    args = args.strip()
    # 1. 数字完成表（定数完成表）
    m = re.match(r'^(\d+\+?)完成表(?:\s+(\S+))?$', args)
    if m:
        ra = m.group(1)
        user = m.group(2) if m.group(2) else username or 'default'
        # 数字完成表（定数表+成绩）
        result = await draw_rating_table(user, ra, False)
        if isinstance(result, Image.Image):
            img_path = Path("output") / f"table_pfm_{user}_{ra}.png"
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
        if isinstance(result, Image.Image):
            img_path = Path("output") / f"table_pfm_{user}_{ver}{plan}.png"
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
        if isinstance(pic, Image.Image):
            img_path = Path("output") / f"table_plate_{user}_{ver}{plan}.png"
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
            if isinstance(pic, Image.Image):
                img_path = Path("output") / f"table_pfm_{user}_{ra}.png"
                pic.save(img_path)
                print(f"完成表图片已保存到: {img_path}")
            else:
                print(pic)
        else:
            print('只支持查询lv6-15的完成表')
        return
    print('无法识别的表格')

async def rise_score_cli(user_id, rating=None, score=None, username=None):
    """CLI版本的分数提升查询（已弃用，请使用rise_score_handler）"""
    data = await rise_score_data(user_id, username, rating, score)
    print(data)

async def plate_process_cli(user_id, ver, plan, username=None):
    """CLI版本的段位进度查询（已弃用，请使用plate_process_handler）"""
    if f'{ver}{plan}' == '真将':
        print('真系没有真将哦')
        return
    username = username if username is not None else ''
    data = await player_plate_data(user_id, username, ver, plan)
    print(data)

async def level_process_cli(user_id, level, plan, category=None, page=1, username=None):
    """CLI版本的等级进度查询（已弃用，请使用level_process_handler）"""
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
    data = await level_process_data(user_id, username, level, plan, category, page)
    print(data)

async def level_achievement_list_cli(user_id, rating, page=1, username=None):
    """CLI版本的等级成就列表查询（已弃用，请使用level_achievement_list_handler）"""
    data = await level_achievement_list_data(user_id, username, rating, page)
    print(data)