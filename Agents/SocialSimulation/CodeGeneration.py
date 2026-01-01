import configparser
import json
import os
import textwrap
import time
from typing import List, Any
from langchain_core.messages import SystemMessage, HumanMessage

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import codeGenerateInstruction, Code_generation_prompt
from Utils.Tools import evaluateOutput, _connectMySQL, _closeMySQL, getFormatOutput

"""
社会实体代码生成
"""
def codeGeneration(SocialSimulateContent):
    model = ModelFactory("codeGeneration").GetModel()
    ChatHistory: List[Any] = []
    connection, cursor = _connectMySQL()
    OddSql = f"SELECT overView,designConcept FROM `odd` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(OddSql)
    record = cursor.fetchall()[0]
    overview_content = record[0]
    design_content = record[1]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    OddSql = f"SELECT detail FROM `odd2` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(OddSql)
    record = cursor.fetchall()[0]
    detail_content = record[0]
    detailDict = json.loads(detail_content)
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    envSql = f"SELECT pathPlanning FROM `env_restraint` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(envSql)
    pathPlanning = cursor.fetchall()[0][0]

    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    config_path = os.path.join(current_dir, "../../Config/config.ini")
    config_path = os.path.normpath(config_path)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    entityNum = config.get("simulateConfig","simulationEntityNum")
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            ChatHistory.append(SystemMessage(codeGenerateInstruction.format(overview=overview_content,
                                                            design=design_content,details=detail_content)))
            ChatHistory.append(HumanMessage(Code_generation_prompt.format(entityNum = str(entityNum),DetailAttribute = detailDict['attribute'],topic = SocialSimulateContent,
                                                                          mainPath = pathPlanning)))
            codeGenerationAns = model.invoke(ChatHistory)
            codeGenerationDict = json.loads(getFormatOutput(codeGenerationAns.content))
            code_current_file_path = os.path.abspath(__file__)
            code_current_dir = os.path.dirname(code_current_file_path)
            code_config_path = os.path.join(code_current_dir,
                                            "../../Data/Coding/Example" + str(PublicConfig.simulateIdConfig) + ".py")
            code_config_path = os.path.normpath(code_config_path)
            with open(code_config_path, 'w', encoding='utf-8') as f:
                f.write(codeGenerationDict["codeGeneration"])
            # 增加获取反射
            reflectionCode = textwrap.dedent("""
            def get_entity(typename):
                global_var = globals()  # 这里缩进4个空格
                return global_var[typename]
            """)
            with open(code_config_path, 'a', encoding='utf-8') as f:
                f.write(reflectionCode)
            print("需要将python有问题的代码内容删掉")
            # 持久化
            print(len(codeGenerationDict["codeGeneration"]))
            connection, cursor = _connectMySQL()
            codeSql = """INSERT INTO code_ans (id,codeContent,entityNum) VALUES (%s, %s, %s)"""
            cursor.execute(codeSql,
                           (PublicConfig.simulateIdConfig, codeGenerationDict["codeGeneration"], int(entityNum)))
            connection.commit()
            _closeMySQL(connection, cursor)
            break
        except Exception as e:
            retry_count += 1
            print(f"第{retry_count}次重试，错误信息: {e}")
            if retry_count >= max_retries:
                print(f"达到最大重试次数{max_retries}，跳过此属性的调整。")
                raise Exception(f"已达到最大重试次数 {max_retries}") from e