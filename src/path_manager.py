"""
中央路径管理文件 - 适配 AstrBot 插件结构
解决相对路径问题，提供统一的路径管理
"""
import os
import sys
from pathlib import Path

# 获取插件根目录
def get_plugin_root():
    """获取插件根目录"""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

# 插件根目录
PLUGIN_ROOT = get_plugin_root()

# 添加插件根目录到Python路径
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

# 主要目录路径
STATIC_DIR = PLUGIN_ROOT / 'src' / 'static'
OUTPUT_DIR = PLUGIN_ROOT / 'output'
COMMAND_DIR = PLUGIN_ROOT / 'src' / 'command'
LIBRARIES_DIR = PLUGIN_ROOT / 'src' / 'libraries'

# 确保输出目录存在
OUTPUT_DIR.mkdir(exist_ok=True)

# 静态资源路径
MAIMAI_DIR = STATIC_DIR / 'mai' / 'pic'
COVER_DIR = STATIC_DIR / 'mai' / 'cover'
RATING_DIR = STATIC_DIR / 'mai' / 'rating'
PLATE_DIR = STATIC_DIR / 'mai' / 'plate'

# 字体路径
SIYUAN_FONT = STATIC_DIR / 'ResourceHanRoundedCN-Bold.ttf'
SHANGGUMONO_FONT = STATIC_DIR / 'ShangguMonoSC-Regular.otf'
TB_FONT = STATIC_DIR / 'Torus SemiBold.otf'

# 数据文件路径
ARCADES_JSON = STATIC_DIR / 'arcades.json'
CONFIG_JSON = STATIC_DIR / 'config.json'
ALIAS_FILE = STATIC_DIR / 'music_alias.json'
LOCAL_ALIAS_FILE = STATIC_DIR / 'local_music_alias.json'
MUSIC_FILE = STATIC_DIR / 'music_data.json'
CHART_FILE = STATIC_DIR / 'music_chart.json'
GUESS_FILE = STATIC_DIR / 'group_guess_switch.json'
GROUP_ALIAS_FILE = STATIC_DIR / 'group_alias_switch.json'
PIE_HTML_FILE = STATIC_DIR / 'temp_pie.html'

# 帮助图片
HELP_IMAGE = PLUGIN_ROOT / 'maimaidxhelp.png'

def get_relative_path(target_path: Path) -> Path:
    """获取相对于插件根目录的路径"""
    try:
        return target_path.relative_to(PLUGIN_ROOT)
    except ValueError:
        return target_path

def ensure_path_exists(path: Path):
    """确保路径存在"""
    if path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path.mkdir(parents=True, exist_ok=True)

# 确保所有必要目录存在
ensure_path_exists(OUTPUT_DIR)
ensure_path_exists(STATIC_DIR)
ensure_path_exists(MAIMAI_DIR)
ensure_path_exists(COVER_DIR)
ensure_path_exists(RATING_DIR)
ensure_path_exists(PLATE_DIR) 