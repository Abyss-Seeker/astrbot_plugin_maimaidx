import asyncio
from textwrap import dedent
from pathlib import Path
import PIL.Image

from libraries.maimaidx_music import guess
from libraries.maimaidx_music_info import draw_music_info

def log(*args, **kwargs):
    print(*args, **kwargs)

async def guess_music_cli(group_id: int):
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
            if isinstance(answer_img, PIL.Image.Image):
                answer_img.save(answer_path)
                print(f"答案图片已保存到: {answer_path}")
            else:
                print(f"答案是：\n{answer_img}")
            guess.end(gid)

async def guess_pic_cli(group_id: int):
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
    if isinstance(answer_img, PIL.Image.Image):
        answer_img.save(answer_path)
        print(f"答案图片已保存到: {answer_path}")
    else:
        print(f"答案是：\n{answer_img}")
    guess.end(gid)

async def guess_music_solve_cli(group_id: int, answer: str):
    gid = str(group_id)
    if gid not in guess.Group:
        print('当前没有正在进行的猜歌')
        return
    ans = answer.strip().lower()
    if ans in guess.Group[gid].answer:
        guess.Group[gid].end = True
        answer_img = await draw_music_info(guess.Group[gid].music)
        answer_path = Path(f"guess_solve_answer_{gid}.png")
        if isinstance(answer_img, PIL.Image.Image):
            answer_img.save(answer_path)
            print(f"猜对了，答案图片已保存到: {answer_path}")
        else:
            print(f"猜对了，答案是：\n{answer_img}")
        guess.end(gid)
    else:
        print('答案不正确，请继续尝试。')

async def reset_guess_cli(group_id: int, is_admin: bool = False):
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
    gid = str(group_id)
    if not is_admin:
        print('仅允许管理员开关')
        return
    if on:
        msg = await guess.on(gid)
    else:
        msg = await guess.off(gid)
    print(msg)