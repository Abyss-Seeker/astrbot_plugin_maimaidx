"""
配置管理文件
处理用户配置，特别是maimaidxtoken
"""
import json
import os
from pathlib import Path

# 添加项目根目录到路径
import sys
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from path_manager import CONFIG_JSON

class ConfigManager:
    def __init__(self):
        self.config_file = CONFIG_JSON
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if not self.config_file.exists():
            # 创建默认配置
            default_config = {
                "maimaidxtoken": "请在此处填入您的水鱼账号token",
                "maimaidxproberproxy": False,
                "maimaidxaliasproxy": False
            }
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_token(self):
        """获取maimaidxtoken"""
        token = self.config.get("maimaidxtoken", "")
        if not token or token == "请在此处填入您的水鱼账号token":
            print("⚠️  警告：未配置maimaidxtoken！")
            print("请在 static/config.json 文件中配置您的水鱼账号token")
            print("配置格式：")
            print('{"maimaidxtoken": "您的token"}')
            return None
        return token
    
    def set_token(self, token):
        """设置maimaidxtoken"""
        self.config["maimaidxtoken"] = token
        self.save_config(self.config)
        print(f"✅ Token已更新")
    
    def check_config(self):
        """检查配置是否完整"""
        token = self.get_token()
        if not token:
            return False
        return True

# 全局配置管理器实例
config_manager = ConfigManager() 