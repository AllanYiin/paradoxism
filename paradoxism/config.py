import os
import yaml
import copy

class ConfigManager:
    def __init__(self):

        self.default_config = {
            "llm_provider": "openai",
            "llm_model": "gpt-4o"
        }
        self.config =copy.deepcopy(self.default_config)
        if  not  os.path.exists(os.path.join(os.path.expanduser('~'), ".paradoxism")):
            os.mkdir(os.path.join(os.path.expanduser('~'), ".paradoxism"))
        self.config_path = os.path.expanduser("~/.paradoxism/config.yaml")
        self.load_config()

    def load_config(self):
        # 從檔案讀取設定，並優先使用環境變數覆寫
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:

            # 環境變數優先
            self.config["llm_provider"] = os.getenv("LLM_PROVIDER", self.config.get("llm_provider", self.default_config["llm_provider"]))
            self.config["llm_model"] = os.getenv("LLM_MODEL", self.config.get("llm_model", self.default_config["llm_model"]))
            self.save_config()


    def save_config(self):
        # 儲存設定到檔案
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f)

    def update_config(self, key, value):
        # 動態更新設定
        self.config[key] = value
        self.save_config()

    def get_config(self):
        return self.config
