#!/usr/bin/env python3
"""
maimaiDX 本地版设置测试脚本
"""
import sys
import os
from pathlib import Path

def test_imports():
    """测试导入是否正常"""
    print("🔍 测试模块导入...")
    
    try:
        # 添加当前目录到Python路径
        current_dir = Path(__file__).parent.resolve()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        # 测试路径管理器
        from path_manager import *
        print("✅ path_manager 导入成功")
        
        # 测试配置管理器
        from config_manager import config_manager
        print("✅ config_manager 导入成功")
        
        # 测试项目初始化
        from libraries.config import *
        print("✅ config 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_paths():
    """测试路径是否正确"""
    print("\n🔍 测试路径设置...")
    
    try:
        from path_manager import *
        
        # 检查关键目录
        dirs_to_check = [
            (PROJECT_ROOT, "项目根目录"),
            (STATIC_DIR, "静态资源目录"),
            (OUTPUT_DIR, "输出目录"),
            (COMMAND_DIR, "命令目录"),
            (LIBRARIES_DIR, "库目录")
        ]
        
        for path, name in dirs_to_check:
            if path.exists():
                print(f"✅ {name}: {path}")
            else:
                print(f"⚠️  {name}不存在: {path}")
        
        return True
    except Exception as e:
        print(f"❌ 路径测试失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n🔍 测试配置文件...")
    
    try:
        from config_manager import config_manager
        
        # 检查配置文件是否存在
        config_file = config_manager.config_file
        if config_file.exists():
            print(f"✅ 配置文件存在: {config_file}")
            
            # 检查token配置
            token = config_manager.get_token()
            if token and token != "请在此处填入您的水鱼账号token":
                print("✅ Token已配置")
            else:
                print("⚠️  Token未配置，请在 static/config.json 中设置")
        else:
            print(f"⚠️  配置文件不存在: {config_file}")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_resources():
    """测试资源文件"""
    print("\n🔍 测试资源文件...")
    
    try:
        from path_manager import *
        
        # 检查字体文件
        fonts = [
            (SIYUAN_FONT, "思源黑体"),
            (SHANGGUMONO_FONT, "上谷等宽"),
            (TB_FONT, "Torus字体")
        ]
        
        for font_path, name in fonts:
            if font_path.exists():
                print(f"✅ {name}: {font_path}")
            else:
                print(f"⚠️  {name}缺失: {font_path}")
        
        # 检查数据文件
        data_files = [
            (MUSIC_FILE, "音乐数据"),
            (ALIAS_FILE, "别名数据"),
            (CHART_FILE, "谱面数据")
        ]
        
        for file_path, name in data_files:
            if file_path.exists():
                print(f"✅ {name}: {file_path}")
            else:
                print(f"⚠️  {name}缺失: {file_path}")
        
        return True
    except Exception as e:
        print(f"❌ 资源测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎵 maimaiDX 本地版设置测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_paths,
        test_config,
        test_resources
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    if all(results):
        print("🎉 所有测试通过！项目设置正确。")
        print("💡 现在可以运行 'python main.py' 启动程序")
    else:
        print("⚠️  部分测试失败，请检查上述问题")
        print("💡 确保所有文件都已正确复制")
    
    print("\n按回车键退出...")
    input()

if __name__ == "__main__":
    main() 