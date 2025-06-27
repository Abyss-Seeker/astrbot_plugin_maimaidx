"""
中央路径管理文件
解决相对路径问题，提供统一的路径管理
"""
import os
import sys
from pathlib import Path

# 获取项目根目录
def get_project_root():
    """获取项目根目录"""
    current_file = Path(__file__).resolve()
    return current_file.parent

# 项目根目录
PROJECT_ROOT = get_project_root()

# 添加项目根目录到Python路径
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 主要目录路径
STATIC_DIR = PROJECT_ROOT / 'static'
OUTPUT_DIR = PROJECT_ROOT / 'output'
COMMAND_DIR = PROJECT_ROOT / 'command'
LIBRARIES_DIR = PROJECT_ROOT / 'libraries'

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
HELP_IMAGE = PROJECT_ROOT / 'maimaidxhelp.png'

def get_relative_path(target_path: Path) -> Path:
    """获取相对于项目根目录的路径"""
    try:
        return target_path.relative_to(PROJECT_ROOT)
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