import copy
import time
from pathlib import Path

import aiofiles

from .image import tricolor_gradient
from .maimai_best_50 import *
from .maimaidx_music import Music, mai
from .config import levelList, plate_to_dx_version, maimaidir, ratingdir, platedir, BOTNAME, platecn, version_map
from .maimai_best_50 import ScoreBaseImage
from .image import DrawText
from typing import Dict


async def update_rating_table() -> str:
    """更新定数表"""
    try:
        dx_img = Image.open(maimaidir / 'DX.png') if (maimaidir / 'DX.png').exists() else None
        dx = dx_img.convert('RGBA').resize((44, 16)) if dx_img else Image.new('RGBA', (44, 16))
        diff = [Image.new('RGBA', (75, 16), color) for color in ScoreBaseImage.bg_color]
        atime = 0
        for lv in levelList[6:]:
            _otime = time.time()
            picname = ratingdir / f'{lv}.png'
            lvlist = mai.total_level_data[lv]
            lines = 0
            for _lv in lvlist:
                musicnum = len(lvlist[_lv])
                if musicnum == 0:
                    r = 1
                else:
                    remainder = musicnum % 14
                    r = (musicnum // 14) + (1 if remainder else 0)
                lines += r

            if '+' in lv:
                f = 4
            elif lv == '6':
                f = 10
            else:
                f = 8

            linesheight = 85 * lines
            """
            `85` 为曲绘高度 `80` + 间隔 `5`
            `lines` 为行数
            """
            
            width, height = 1400, 325 + f * 20 + linesheight
            """
            `325` 为顶部文字和底部图片高度 + 上下间隔高度
            `f * 20` 为等级数量 `f` * 等级间隔 `20`
            `linesheight` 为各等级曲绘和间隔总和高度
            """
            
            im = tricolor_gradient(width, height)
            
            aurora_bg = ScoreBaseImage.aurora_bg if ScoreBaseImage.aurora_bg else Image.new('RGBA', (1400, 220))
            shines_bg = ScoreBaseImage.shines_bg if ScoreBaseImage.shines_bg else Image.new('RGBA', (1400, 220))
            rainbow_bg = ScoreBaseImage.rainbow_bg if ScoreBaseImage.rainbow_bg else Image.new('RGBA', (1400, 220))
            rainbow_bottom_bg = ScoreBaseImage.rainbow_bottom_bg if ScoreBaseImage.rainbow_bottom_bg else Image.new('RGBA', (1200, 200))
            im.alpha_composite(aurora_bg)
            im.alpha_composite(shines_bg, (34, 0))
            im.alpha_composite(rainbow_bg, (319, height - 643))
            im.alpha_composite(rainbow_bottom_bg, (100, height - 343))
            for h in range((height // 358) + 1):
                pattern = ScoreBaseImage.pattern_bg
                if pattern is None:
                    pattern = Image.new('RGBA', (1400, 365), (0,0,0,0))
                im.alpha_composite(pattern, (0, (358 + 7) * h))

            dr = ImageDraw.Draw(im)
            sy = DrawText(dr, SIYUAN)
            ts = DrawText(dr, TBFONT)
            design_img = Image.open(maimaidir / 'design.png') if (maimaidir / 'design.png').exists() else None
            if design_img:
                im.alpha_composite(design_img, (200, height - 113))
            sy.draw(
                700, 
                height - 70, 
                22, 
                f'Designed by Yuri-YuzuChaN & BlueDeer233. Adapted by AbyssSeeker', 
                ScoreBaseImage.text_color, 
                'mm'
            )
            y = 100
            for _lv in lvlist: 
                x = 160
                y += 20
                chara_img = Image.open(maimaidir / 'UI_CMN_Chara_Level_S_01.png') if (maimaidir / 'UI_CMN_Chara_Level_S_01.png').exists() else None
                if chara_img:
                    im.alpha_composite(chara_img.resize((80, 80)), (50, y + 80))
                ts.draw(88, y + 120, 35, _lv, anchor='mm')
                for num, music in enumerate(lvlist[_lv]):
                    if num % 14 == 0:
                        x = 160
                        y += 85
                    else:
                        x += 85
                    cover_img = Image.open(music_picture(music.id)) if Path(music_picture(music.id)).exists() else None
                    if cover_img:
                        im.alpha_composite(cover_img.resize((75, 75)), (x, y))
                    if music.type == 'DX':
                        im.alpha_composite(dx, (x + 31, y))
                    im.alpha_composite(diff[int(music.lv)], (x, y + 59))
                    ts.draw(x + 37, y + 67, 13, music.id, ScoreBaseImage.t_color[int(music.lv)], 'mm')
                if not lvlist[_lv]:
                    y += 85

            by = BytesIO()
            im.save(by, 'PNG')
            async with aiofiles.open(picname, 'wb') as f:
                await f.write(by.getbuffer())
            _ntime = int(time.time() - _otime)
            atime += _ntime
            print(f'lv.{lv} 定数表更新完成，耗时：{_ntime}s')
        print(f'定数表更新完成，共耗时{atime}s')
        return f'定数表更新完成，共耗时{atime}s'
    except Exception as e:
        print(traceback.format_exc())
        return f'定数表更新失败，Error: {e}'


async def update_plate_table() -> str:
    """更新完成表"""
    try:
        version = list(_ for _ in plate_to_dx_version.keys())[1:]
        # version.append('霸')
        # version.append('舞')
        id_bg = Image.new('RGBA', (100, 20), (124, 129, 255, 255))
        rlv: Dict[str, List[Music]] = {}
        for _ in list(reversed(levelList)):
            rlv[_] = []
        for _v in version:
            if _v in platecn:
                _v = platecn[_v]
            ver, _ver = version_map.get(_v, ([plate_to_dx_version.get(_v)], _v))
            
            music_id_list = mai.total_plate_id_list[_ver]
            music = mai.total_list.by_id_list(music_id_list)
            ralv = copy.deepcopy(rlv)

            for m in music:
                ralv[m.level[3]].append(m)

            lines = 0
            interval = 0
            for _ in ralv:
                musicnum = len(ralv[_])
                if musicnum == 0:
                    continue
                interval += 1
                remainder = musicnum % 10
                lines += (musicnum // 10) + (1 if remainder else 0)
            
            linesheight = 115 * lines + (interval - 1) * 15
            """
            `linesheight`: 各等级曲绘和间隔总和高度
            
                - `115` 为曲绘高度 `100` + 间隔 `15`
                - `lines` 为行数
                - `interval` 为各等级间隔行数
                - `(interval - 1) * 15` 为各等级间隔高度，各等级之间间隔为 `30`，所以只加 `15`
            """
            width, height = 1400, 150 + linesheight + 360
            """
            `150` 为底部图片 `design` 高度 + 上下间隔高度
            `linesheight` 为各等级曲绘和间隔总和高度
            `360` 为顶部图片 `` 高度 + 上下间隔高度
            """

            im = tricolor_gradient(width, height)
            
            aurora_bg = ScoreBaseImage.aurora_bg if ScoreBaseImage.aurora_bg else Image.new('RGBA', (1400, 220))
            shines_bg = ScoreBaseImage.shines_bg if ScoreBaseImage.shines_bg else Image.new('RGBA', (1400, 220))
            rainbow_bg = ScoreBaseImage.rainbow_bg if ScoreBaseImage.rainbow_bg else Image.new('RGBA', (1400, 220))
            rainbow_bottom_bg = ScoreBaseImage.rainbow_bottom_bg if ScoreBaseImage.rainbow_bottom_bg else Image.new('RGBA', (1200, 200))
            im.alpha_composite(aurora_bg)
            im.alpha_composite(shines_bg, (34, 0))
            im.alpha_composite(rainbow_bg, (319, height - 643))
            im.alpha_composite(rainbow_bottom_bg, (100, height - 343))
            for h in range((height // 358) + 1):
                pattern = ScoreBaseImage.pattern_bg
                if pattern is None:
                    pattern = Image.new('RGBA', (1400, 365), (0,0,0,0))
                im.alpha_composite(pattern, (0, (358 + 7) * h))
            
            dr = ImageDraw.Draw(im)
            ts = DrawText(dr, TBFONT)
            sy = DrawText(dr, SIYUAN)
            design_img = Image.open(maimaidir / 'design.png') if (maimaidir / 'design.png').exists() else None
            if design_img:
                im.alpha_composite(design_img, (200, height - 113))
            sy.draw(
                700, 
                height - 70, 
                22, 
                f'Designed by Yuri-YuzuChaN & BlueDeer233. Adapted by AbyssSeeker', 
                ScoreBaseImage.text_color, 
                'mm'
            )
            y = 245
            for r in ralv:
                if _v in ['霸', '舞']:
                    ralv[r].sort(key=lambda x: x.ds[-1], reverse=True)
                else:
                    ralv[r].sort(key=lambda x: x.ds[3], reverse=True)
                if ralv[r]:
                    y += 15
                    chara_img = Image.open(maimaidir / 'UI_CMN_Chara_Level_S_01.png') if (maimaidir / 'UI_CMN_Chara_Level_S_01.png').exists() else None
                    if chara_img:
                        im.alpha_composite(chara_img, (65, y + 115))
                    ts.draw(113, y + 164, 35, r, anchor='mm')
                x = 200
                for num, music in enumerate(ralv[r]):
                    if num % 10 == 0:
                        x = 200
                        y += 115
                    else:
                        x += 115
                    cover_path = music_picture(music.id)
                    cover_img = Image.open(cover_path) if Path(cover_path).exists() else None
                    if cover_img:
                        im.alpha_composite(cover_img.resize((100, 100)), (x, y))
                    im.alpha_composite(id_bg, (x, y + 80))
                    ts.draw(x + 50, y + 88, 20, music.id, anchor='mm')

            by = BytesIO()
            im.save(by, 'PNG')
            async with aiofiles.open(platedir / f'{_v}.png', 'wb') as f:
                await f.write(by.getbuffer())
            print(f'{_v}代牌子更新完成')
        return f'完成表更新完成'
    except Exception as e:
        print(traceback.format_exc())
        return f'完成表更新失败，Error: {e}'