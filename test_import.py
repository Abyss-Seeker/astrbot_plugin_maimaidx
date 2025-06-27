#!/usr/bin/env python3
"""
测试脚本 - 验证插件导入是否正常
"""
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def test_imports():
    """测试所有关键模块的导入"""
    try:
        print("测试导入...")
        
        # 测试基础模块导入
        print("1. 测试 src/__init__.py...")
        from src import BOTNAME, scoreRank, levelList
        print(f"   ✅ BOTNAME: {BOTNAME}")
        print(f"   ✅ scoreRank: {len(scoreRank)} 项")
        print(f"   ✅ levelList: {len(levelList)} 项")
        
        # 测试路径管理器
        print("2. 测试 path_manager...")
        from src.path_manager import PLUGIN_ROOT, STATIC_DIR
        print(f"   ✅ PLUGIN_ROOT: {PLUGIN_ROOT}")
        print(f"   ✅ STATIC_DIR: {STATIC_DIR}")
        
        # 测试库模块
        print("3. 测试库模块...")
        from src.libraries import config, maimaidx_music, maimaidx_music_info
        print("   ✅ 核心库模块导入成功")
        
        # 测试命令模块
        print("4. 测试命令模块...")
        from src.command import mai_base, mai_score, mai_search, mai_table, mai_alias, mai_guess
        print("   ✅ 所有命令模块导入成功")
        
        # 测试基础管理器（不依赖AstrBot）
        print("5. 测试基础管理器...")
        from src.output_manager import OutputManager
        from src.error_handler import ErrorHandler
        print("   ✅ 基础管理器导入成功")
        
        print("\n🎉 所有基础导入测试通过！")
        print("注意：ConfigManager 和 DataManager 需要 AstrBot 环境才能测试。")
        return True
        
    except Exception as e:
        print(f"\n❌ 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 