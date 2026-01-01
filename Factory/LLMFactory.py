import configparser
import os
from langchain_community.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI

"""
返回大模型实体类的工厂类
"""
class ModelFactory:
    def __init__(self,purpose):
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        config_path = os.path.join(current_dir, "../Config/config.ini")
        config_path = os.path.normpath(config_path)
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        if(purpose == "deepResearch"):
            self.__LLMApiKey = os.getenv("API_KEY_EXTERNAL")
            self.__BaseURL = config.get("deepResearchApi","base_url")
            self.__ModelName = config.get("deepResearchApi","model_name")
        elif(purpose == "socialSimulate"):
            self.__LLMApiKey = os.getenv("API_KEY_TJUNLP")
            self.__BaseURL = config.get("socialSimulateApi", "base_url")
            self.__ModelName = config.get("socialSimulateApi", "model_name")
        elif(purpose == "dataSet"):
            self.__LLMApiKey = os.getenv("API_KEY_TJUNLP")
            self.__BaseURL = config.get("dataSetAssistAPI", "base_url")
            self.__ModelName = config.get("dataSetAssistAPI", "model_name")
        elif (purpose == "codeGeneration"):
            self.__LLMApiKey = os.getenv("API_KEY_EXTERNAL")
            self.__BaseURL = config.get("codeGenerationApi", "base_url")
            self.__ModelName = config.get("codeGenerationApi", "model_name")
        elif (purpose == "evaluation"):
            self.__LLMApiKey = os.getenv("API_KEY_EXTERNAL")
            self.__BaseURL = config.get("evaluationAPI", "base_url")
            self.__ModelName = config.get("evaluationAPI", "model_name")
        elif (purpose == "writingPaper"):
            self.__LLMApiKey = os.getenv("API_KEY_EXTERNAL")
            self.__BaseURL = config.get("writingPaperApi", "base_url")
            self.__ModelName = config.get("writingPaperApi", "model_name")
        elif (purpose == "controlTest"):
            self.__LLMApiKey = os.getenv("API_KEY_EXTERNAL")
            self.__BaseURL = config.get("controlTestApi", "base_url")
            self.__ModelName = config.get("controlTestApi", "model_name")
    def GetModel(self):
        return ChatOpenAI(model_name=self.__ModelName,
                          openai_api_key=self.__LLMApiKey,
                          openai_api_base=self.__BaseURL)


