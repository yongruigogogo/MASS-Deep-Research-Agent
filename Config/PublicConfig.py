import configparser
import os


class PublicConfig:
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    config_path = os.path.join(current_dir, "../Config/config.ini")
    config_path = os.path.normpath(config_path)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    simulateIdConfig = config.get("agentId","simulateIdConfig")
    taskIdConfig = config.get("agentId","taskIdConfig")