import asyncio
from textwrap import dedent
from pathlib import Path
from PIL import Image
import io

from ..libraries.maimaidx_music import guess
from ..libraries.maimaidx_music_info import draw_music_info

from ..output_manager import OutputManager
from ..error_handler import ErrorHandler

# 初始化输出管理器和错误处理器
output_manager = OutputManager()
error_handler = ErrorHandler()

# AstrBot 命令处理器实现
async def guess_music_handler(event):
    """
    开始猜歌命令处理器
    
    Args:
        event: AstrBot 事件对象
    """
    try:
        group_id = event.group.id if hasattr(event, 'group') and hasattr(event.group, 'id') else None
        if group_id is None:
            return output_manager.send_text(event, '无法获取群组信息')
        
        gid = str(group_id)
        if gid not in guess.switch.enable:
            return output_manager.send_text(event, '该群已关闭猜歌功能，开启请输入 开启mai猜歌')
        
        if gid in guess.Group:
            return output_manager.send_text(event, '该群已有正在进行的猜歌或猜曲绘')
        
        guess.start(gid)
        start_msg = dedent(''' \
            我将从热门乐曲中选择一首歌，每隔8秒描述它的特征，
            请输入歌曲的 id 标题 或 别名 进行猜歌（DX乐谱和标准乐谱视为两首歌）。
            猜歌时查歌等其他命令依然可用。
        ''')
        
        # 发送开始消息
        await output_manager.send_text(event, start_msg)
        
        # 等待4秒后开始提示
        await asyncio.sleep(4)
        
        for cycle in range(7):
            if gid not in guess.switch.enable or gid not in guess.Group or guess.Group[gid].end:
                break
            if cycle < 6:
                # 使用getattr安全地获取options属性
                try:
                    options = getattr(guess.Group[gid], 'options', [])
                    if cycle < len(options):
                        hint_msg = f'{cycle + 1}/7 这首歌{options[cycle]}'
                    else:
                        hint_msg = f'{cycle + 1}/7 这首歌的提示信息'
                except (AttributeError, IndexError):
                    hint_msg = f'{cycle + 1}/7 这首歌的提示信息'
                await output_manager.send_text(event, hint_msg)
                await asyncio.sleep(8)
            else:
                # 显示封面图片
                img_data = guess.Group[gid].img
                if isinstance(img_data, bytes):
                    # 保存图片到临时文件
                    img_path = output_manager.save_image(Image.open(io.BytesIO(img_data)), f"guess_music_{gid}.png")
                    await output_manager.send_text(event, f'7/7 这首歌封面的一部分\n答案将在30秒后揭晓')
                else:
                    await output_manager.send_text(event, f'7/7 这首歌封面的一部分: {img_data}\n答案将在30秒后揭晓')
                
                # 等待30秒
                for _ in range(30):
                    await asyncio.sleep(1)
                    if gid in guess.Group:
                        if gid not in guess.switch.enable or guess.Group[gid].end:
                            return
                    else:
                        return
                
                guess.Group[gid].end = True
                answer_img = await draw_music_info(guess.Group[gid].music)
                if isinstance(answer_img, Image.Image):
                    return await output_manager.send_image(event, answer_img, f"guess_answer_{gid}.png", "猜歌答案")
                else:
                    return await output_manager.send_text(event, f"答案是：\n{answer_img}")
                
                guess.end(gid)
    except Exception as e:
        return error_handler.handle_error(event, e, "猜歌功能启动失败")

async def guess_pic_handler(event):
    """
    开始猜曲绘命令处理器
    
    Args:
        event: AstrBot 事件对象
    """
    try:
        group_id = event.group.id if hasattr(event, 'group') and hasattr(event.group, 'id') else None
        if group_id is None:
            return output_manager.send_text(event, '无法获取群组信息')
        
        gid = str(group_id)
        if gid not in guess.switch.enable:
            return output_manager.send_text(event, '该群已关闭猜歌功能，开启请输入 开启mai猜歌')
        
        if gid in guess.Group:
            return output_manager.send_text(event, '该群已有正在进行的猜歌或猜曲绘')
        
        guess.startpic(gid)
        img_data = guess.Group[gid].img
        if isinstance(img_data, bytes):
            # 保存图片到临时文件
            img_path = output_manager.save_image(Image.open(io.BytesIO(img_data)), f"guess_pic_{gid}.png")
            await output_manager.send_text(event, f'以下裁切图片是哪首谱面的曲绘\n请在30s内输入答案')
        else:
            await output_manager.send_text(event, f'以下裁切图片是哪首谱面的曲绘：{img_data}\n请在30s内输入答案')
        
        # 等待30秒
        for _ in range(30):
            await asyncio.sleep(1)
            if gid in guess.Group:
                if gid not in guess.switch.enable or guess.Group[gid].end:
                    return
            else:
                return
        
        guess.Group[gid].end = True
        answer_img = await draw_music_info(guess.Group[gid].music)
        if isinstance(answer_img, Image.Image):
            return await output_manager.send_image(event, answer_img, f"guess_pic_answer_{gid}.png", "猜曲绘答案")
        else:
            return await output_manager.send_text(event, f"答案是：\n{answer_img}")
        
        guess.end(gid)
    except Exception as e:
        return error_handler.handle_error(event, e, "猜曲绘功能启动失败")

async def guess_music_solve_handler(event, answer: str):
    """
    猜歌答案提交命令处理器
    
    Args:
        event: AstrBot 事件对象
        answer: 用户提交的答案
    """
    try:
        group_id = event.group.id if hasattr(event, 'group') and hasattr(event.group, 'id') else None
        if group_id is None:
            return output_manager.send_text(event, '无法获取群组信息')
        
        gid = str(group_id)
        if gid not in guess.Group:
            return output_manager.send_text(event, '当前没有正在进行的猜歌')
        
        ans = answer.strip().lower()
        if ans in guess.Group[gid].answer:
            guess.Group[gid].end = True
            answer_img = await draw_music_info(guess.Group[gid].music)
            if isinstance(answer_img, Image.Image):
                return await output_manager.send_image(event, answer_img, f"guess_solve_answer_{gid}.png", "猜对了！答案")
            else:
                return await output_manager.send_text(event, f"猜对了，答案是：\n{answer_img}")
            guess.end(gid)
        else:
            return output_manager.send_text(event, '答案不正确，请继续尝试。')
    except Exception as e:
        return error_handler.handle_error(event, e, "答案提交失败")

async def reset_guess_handler(event):
    """
    重置猜歌命令处理器（仅管理员）
    
    Args:
        event: AstrBot 事件对象
    """
    try:
        # 检查管理员权限
        is_admin = event.sender.role == 'admin' if hasattr(event, 'sender') and hasattr(event.sender, 'role') else False
        if not is_admin:
            return output_manager.send_text(event, '仅允许管理员重置')
        
        group_id = event.group.id if hasattr(event, 'group') and hasattr(event.group, 'id') else None
        if group_id is None:
            return output_manager.send_text(event, '无法获取群组信息')
        
        gid = str(group_id)
        if gid in guess.Group:
            guess.end(gid)
            return output_manager.send_text(event, '已重置该群猜歌')
        else:
            return output_manager.send_text(event, '该群未处在猜歌状态')
    except Exception as e:
        return error_handler.handle_error(event, e, "重置猜歌失败")

async def guess_on_off_handler(event, on: bool):
    """
    猜歌功能开关命令处理器（仅管理员）
    
    Args:
        event: AstrBot 事件对象
        on: 是否开启
    """
    try:
        # 检查管理员权限
        is_admin = event.sender.role == 'admin' if hasattr(event, 'sender') and hasattr(event.sender, 'role') else False
        if not is_admin:
            return output_manager.send_text(event, '仅允许管理员开关')
        
        group_id = event.group.id if hasattr(event, 'group') and hasattr(event.group, 'id') else None
        if group_id is None:
            return output_manager.send_text(event, '无法获取群组信息')
        
        gid = str(group_id)
        if on:
            msg = await guess.on(gid)
        else:
            msg = await guess.off(gid)
        return output_manager.send_text(event, msg)
    except Exception as e:
        return error_handler.handle_error(event, e, "猜歌功能开关设置失败")

# 保留原有的CLI函数以保持向后兼容性
async def guess_music_cli(group_id: int):
    """CLI版本的开始猜歌（已弃用，请使用guess_music_handler）"""
    gid = str(group_id)
    if gid not in guess.switch.enable:
        print('该群已关闭猜歌功能，开启请输入 开启mai猜歌')
        return
    if gid in guess.Group:
        print('该群已有正在进行的猜歌或猜曲绘')
        return
    guess.start(gid)
    print(dedent(''' \
        我将从热门乐曲中选择一首歌，每隔8秒描述它的特征，
        请输入歌曲的 id 标题 或 别名 进行猜歌（DX乐谱和标准乐谱视为两首歌）。
        猜歌时查歌等其他命令依然可用。
    '''))
    await asyncio.sleep(4)
    for cycle in range(7):
        if gid not in guess.switch.enable or gid not in guess.Group or guess.Group[gid].end:
            break
        if cycle < 6:
            print(f'{cycle + 1}/7 这首歌{guess.Group[gid].options[cycle]}')
            await asyncio.sleep(8)
        else:
            img_path = Path(f"guess_music_{gid}.png")
            img_data = guess.Group[gid].img
            if isinstance(img_data, bytes):
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                print(f'7/7 这首歌封面的一部分已保存到: {img_path}\n答案将在30秒后揭晓')
            else:
                print(f'7/7 这首歌封面的一部分: {img_data}\n答案将在30秒后揭晓')
            for _ in range(30):
                await asyncio.sleep(1)
                if gid in guess.Group:
                    if gid not in guess.switch.enable or guess.Group[gid].end:
                        return
                else:
                    return
            guess.Group[gid].end = True
            answer_img = await draw_music_info(guess.Group[gid].music)
            answer_path = Path(f"guess_answer_{gid}.png")
            if isinstance(answer_img, Image.Image):
                answer_img.save(answer_path)
                print(f"答案图片已保存到: {answer_path}")
            else:
                print(f"答案是：\n{answer_img}")
            guess.end(gid)

async def guess_pic_cli(group_id: int):
    """CLI版本的开始猜曲绘（已弃用，请使用guess_pic_handler）"""
    gid = str(group_id)
    if gid not in guess.switch.enable:
        print('该群已关闭猜歌功能，开启请输入 开启mai猜歌')
        return
    if gid in guess.Group:
        print('该群已有正在进行的猜歌或猜曲绘')
        return
    guess.startpic(gid)
    img_path = Path(f"guess_pic_{gid}.png")
    img_data = guess.Group[gid].img
    if isinstance(img_data, bytes):
        with open(img_path, 'wb') as f:
            f.write(img_data)
        print(f'以下裁切图片是哪首谱面的曲绘，图片已保存到: {img_path}\n请在30s内输入答案')
    else:
        print(f'以下裁切图片是哪首谱面的曲绘：{img_data}\n请在30s内输入答案')
    for _ in range(30):
        await asyncio.sleep(1)
        if gid in guess.Group:
            if gid not in guess.switch.enable or guess.Group[gid].end:
                return
        else:
            return
    guess.Group[gid].end = True
    answer_img = await draw_music_info(guess.Group[gid].music)
    answer_path = Path(f"guess_pic_answer_{gid}.png")
    if isinstance(answer_img, Image.Image):
        answer_img.save(answer_path)
        print(f"答案图片已保存到: {answer_path}")
    else:
        print(f"答案是：\n{answer_img}")
    guess.end(gid)

async def guess_music_solve_cli(group_id: int, answer: str):
    """CLI版本的猜歌答案提交（已弃用，请使用guess_music_solve_handler）"""
    gid = str(group_id)
    if gid not in guess.Group:
        print('当前没有正在进行的猜歌')
        return
    ans = answer.strip().lower()
    if ans in guess.Group[gid].answer:
        guess.Group[gid].end = True
        answer_img = await draw_music_info(guess.Group[gid].music)
        answer_path = Path(f"guess_solve_answer_{gid}.png")
        if isinstance(answer_img, Image.Image):
            answer_img.save(answer_path)
            print(f"猜对了，答案图片已保存到: {answer_path}")
        else:
            print(f"猜对了，答案是：\n{answer_img}")
        guess.end(gid)
    else:
        print('答案不正确，请继续尝试。')

async def reset_guess_cli(group_id: int, is_admin: bool = False):
    """CLI版本的重置猜歌（已弃用，请使用reset_guess_handler）"""
    gid = str(group_id)
    if not is_admin:
        print('仅允许管理员重置')
        return
    if gid in guess.Group:
        print('已重置该群猜歌')
        guess.end(gid)
    else:
        print('该群未处在猜歌状态')

async def guess_on_off_cli(group_id: int, on: bool, is_admin: bool = False):
    """CLI版本的猜歌功能开关（已弃用，请使用guess_on_off_handler）"""
    gid = str(group_id)
    if not is_admin:
        print('仅允许管理员开关')
        return
    if on:
        msg = await guess.on(gid)
    else:
        msg = await guess.off(gid)
    print(msg)