import asyncio
import os
import sys
from pathlib import Path
from libraries.config import music_file, alias_file, chart_file

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 导入路径管理器
from path_manager import *

# 导入命令模块
from command import mai_base, mai_alias, mai_guess, mai_score, mai_search, mai_table
from libraries.maimaidx_music import mai

OUTPUT_DIR = Path(__file__).parent / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

def move_output_file(file_path):
    file_path = Path(file_path)
    if file_path.exists() and file_path.is_file():
        new_path = OUTPUT_DIR / file_path.name
        file_path.replace(new_path)
        print(f"[图片/文件] 已保存到: {new_path}")

async def main():
    # 自动检查数据完整性
    if not music_file.exists() or not alias_file.exists() or not chart_file.exists():
        print("检测到数据文件不存在，正在自动初始化...")
        try:
            await mai.get_music()
            await mai.get_music_alias()
            await mai.get_plate_json()
            mai.guess()
            print("数据自动初始化完成！")
        except Exception as e:
            print(f"自动初始化失败: {e}")
            print("请手动执行 'init' 命令进行初始化")
    else:
        print("检测到本地缓存文件，正在加载数据...")
        try:
            await mai.get_music()
            await mai.get_music_alias()
            await mai.get_plate_json()
            mai.guess()
            print("数据加载完成！")
        except Exception as e:
            print(f"数据加载失败: {e}")
            print("请手动执行 'init' 命令重新初始化")
    
    print("欢迎使用 MaimaiDX-Local 终端！输入 help 查看所有指令，输入 exit 退出。")
    while True:
        cmd = input("\n>>> ").strip()
        if cmd.lower() in ("exit", "quit", "q"):
            print("再见！")
            break
        if cmd.lower() in ("help", "h"):
            print("""
可用指令示例：
  b50 [用户名]         —— 查询B50
  minfo [用户名] [曲名/ID] —— 查询游玩数据
  ginfo [难度] [曲名/ID]   —— 查询曲目统计
  score [难度] [ID] [分数]   —— 分数线计算
  今日<舞萌/mai/运势>          —— 今日舞萌运势
  查歌 [关键词] [页数]       —— 查歌
  定数查歌 [定数下限] [定数上限] [页数] —— 定数查歌
  bpm查歌 [bpm下限] [bpm上限] [页数] —— bpm查歌
  曲师查歌 [曲师] [页数]     —— 曲师查歌
  谱师查歌 [谱师] [页数]     —— 谱师查歌
  [别名]是什么歌         —— 别名查歌
  id[数字]                —— ID查歌
  <难度/plate>完成表           —— 完成表
  [难度]定数表           —— 定数表
  update_alias            —— 更新别名库
  update_rating_table     —— 更新定数表
  update_plate_table      —— 更新完成表
  init/load               —— 手动重新初始化曲库数据
  exit                   —— 退出

注意：程序会自动检查并加载本地缓存数据，通常无需手动执行init命令
基于Yuri-YuzuChaN的maimaiDX，由AbyssSeeker移植。需要水鱼账号。
""")
            continue
        try:
            # 指令分发
            args = cmd.split()
            if not args:
                continue
            c = args[0].lower()
            # 今日舞萌
            if c in ("今日舞萌", "今日mai", "今日运势"):
                await mai_base.mai_today_cli()  # 不传参数，让函数内部随机生成QQ号
                # 移动生成的图片文件
                for file_path in Path(".").glob("today_recommend_*.png"):
                    move_output_file(file_path)
                for file_path in Path(".").glob("today_fortune_*.png"):
                    move_output_file(file_path)
                continue
            # B50
            elif c in ("b50",):
                username = args[1] if len(args) > 1 else None
                result = await mai_score.b50_cli(username)
                if isinstance(result, str):
                    print(result)
                else:
                    move_output_file(f"b50_{username}.png")
            # minfo
            elif c in ("minfo", "info"):
                if len(args) < 3:
                    print("格式：minfo [用户名] [曲名/ID]")
                    continue
                username = args[1]
                song = ' '.join(args[2:])  # 支持带空格的曲名
                result = await mai_score.minfo_cli(username, song)
                if isinstance(result, str):
                    print(result)
                else:
                    result.save(f"minfo_{username}_{song}.png")
                    move_output_file(f"minfo_{username}_{song}.png")
            # ginfo
            elif c in ("ginfo",):
                if len(args) < 3:
                    print("格式：ginfo [难度(绿/黄/红/紫/白)] [曲名/ID]")
                    continue
                difficulty = args[1]
                song = ' '.join(args[2:])  # 支持带空格的曲名
                result = await mai_score.ginfo_cli(f"{difficulty} {song}")
                if isinstance(result, str):
                    print(result)
                else:
                    result.save(f"ginfo_{difficulty}_{song}.png")
                    move_output_file(f"ginfo_{difficulty}_{song}.png")
            # score
            elif c in ("score", "分数线"):
                if len(args) < 2:
                    print("格式：score [难度+ID] [分数]")
                    continue
                result = await mai_score.score_cli(' '.join(args[1:]))
                print(result)  # score命令返回文本结果
            # 查歌
            elif c in ("查歌", "search"):
                # 查歌 [关键词] [页码]
                name = args[1] if len(args) > 1 else ''
                page = int(args[2]) if len(args) > 2 and args[2].isdigit() else 1
                await mai_search.search_music_cli(name, page=page)
                # 文件名不唯一，需手动查看output
            # 定数查歌
            elif c in ("定数查歌", "search base"):
                # 定数查歌 [定数] [定数上限] [页码]
                base_args = args[1:]
                await mai_search.search_base_cli(base_args)
            # bpm查歌
            elif c in ("bpm查歌", "search bpm"):
                if not hasattr(mai, 'total_list'):
                    print('曲库未初始化，请先执行一次主菜单或相关数据加载指令！')
                    return
                # bpm查歌 [bpm] [bpm上限] [页码]
                bpm_args = args[1:]
                await mai_search.search_bpm_cli(bpm_args)
            # 曲师查歌
            elif c in ("曲师查歌", "search artist"):
                # 曲师查歌 [曲师] [页码]
                artist_args = args[1:]
                await mai_search.search_artist_cli(artist_args)
            # 谱师查歌
            elif c in ("谱师查歌", "search charter"):
                # 谱师查歌 [谱师] [页码]
                charter_args = args[1:]
                await mai_search.search_charter_cli(charter_args)
            # 别名查歌
            elif c.endswith("是什么歌") or c.endswith("是啥歌"):
                await mai_search.search_alias_song_cli(c[:-4])
            # id查歌
            elif c.startswith("id") and c[2:].isdigit():
                await mai_search.query_chart_cli(c[2:])
            # 完成表/定数表
            elif c.endswith("完成表"):
                username = args[1] if len(args) > 1 else "default"
                await mai_table.table_pfm_cli(username, ' '.join(args))
            elif c.endswith("定数表"):
                username = args[1] if len(args) > 1 else "default"
                await mai_table.rating_table_cli(' '.join(args), username)
            # update_rating_table
            elif c in ("update_rating_table", "更新定数表"):
                await mai_table.update_rating_table_cli()
                continue
            # update_plate_table
            elif c in ("update_plate_table", "更新完成表"):
                await mai_table.update_plate_table_cli()
                continue
            # update_alias
            elif c in ("update_alias", "更新别名库"):
                await mai_alias.update_alias_cli()
                continue
            # init 指令
            elif c in ("init", "load"):
                print("正在初始化曲库数据，请稍候...")
                await mai.get_music()
                await mai.get_music_alias()
                await mai.get_plate_json()
                mai.guess()
                print("曲库初始化完成！")
                continue
            # 其它指令可继续补充...
            else:
                print(f"未知指令: {c}")
                print("输入 help 查看所有可用指令")
        except Exception as e:
            print(f"执行指令时出错: {e}")
            print("请检查输入格式是否正确")

if __name__ == "__main__":
    asyncio.run(main()) 