import json
import time
from typing import List, Any
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import envGenerationPrompt, actionPlanningPrompt
from Utils.Tools import evaluateOutput, getFormatOutput, _connectMySQL, _closeMySQL

"""
生成环境相关的限制
"""
def enviromentGeneration(SocialSimulateContent):
    ChatHistory: List[Any] = []
    model = ModelFactory("deepResearch").GetModel()
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
    _closeMySQL(connection, cursor)

    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            #环境约束
            ChatHistory.append(SystemMessage(envGenerationPrompt.format(overview=overview_content,
                                                             design=design_content,details=detail_content)))
            while True:
                envGenerationAns = model.invoke(ChatHistory)
                inspectAns = evaluateOutput(ChatHistory[-1],envGenerationAns.content)
                if inspectAns == True:
                    break
            envGenerationDict = json.loads(getFormatOutput(envGenerationAns.content))
            ChatHistory.append(AIMessage(envGenerationAns.content))
            #做下行动路径的大体规划
            ChatHistory.append(HumanMessage(actionPlanningPrompt.format(topic = SocialSimulateContent,detailContent = detail_content,restraintContent = str(envGenerationDict["envRetrain"]))))
            while True:
                pathPlanningAns = model.invoke(ChatHistory)
                inspectAns = evaluateOutput(ChatHistory[-1],pathPlanningAns.content)
                if inspectAns == True:
                    break
            pathPlanningDict = json.loads(getFormatOutput(pathPlanningAns.content))
            ChatHistory.append(SystemMessage(pathPlanningAns.content))
            #保存
            connection, cursor = _connectMySQL()
            envSql = """INSERT INTO env_restraint(id,restraintContent,pathPlanning) VALUES (%s, %s ,%s)"""
            cursor.execute(envSql,(PublicConfig.simulateIdConfig,str(envGenerationDict["envRetrain"]),str(pathPlanningDict["pathPlanning"])))
            connection.commit()
            _closeMySQL(connection,cursor)
            break
        except Exception as e:
            retry_count += 1
            print(f"第{retry_count}次重试，错误信息: {e}")
            if retry_count >= max_retries:
                print(f"达到最大重试次数{max_retries}，跳过此属性的调整。")
                raise Exception(f"已达到最大重试次数 {max_retries}") from e

