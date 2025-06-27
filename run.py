#!/usr/bin/env python3
"""
maimaiDX 本地版启动脚本
"""
import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 导入并运行主程序
from main import main
import asyncio

if __name__ == "__main__":
    print("🎵 maimaiDX 本地版启动中...")
    print("=" * 50)
    
    # 检查配置文件
    config_file = current_dir / "static" / "config.json"
    if not config_file.exists():
        print("⚠️  首次运行，正在创建配置文件...")
        os.makedirs(config_file.parent, exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('''{
    "maimaidxtoken": "请在此处填入您的水鱼账号token",
    "maimaidxproberproxy": false,
    "maimaidxaliasproxy": false
}''')
        print("✅ 配置文件已创建，请编辑 static/config.json 配置您的token")
        print("配置完成后重新运行此程序")
        input("按回车键退出...")
        sys.exit(0)
    
    # 运行主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        input("按回车键退出...") 