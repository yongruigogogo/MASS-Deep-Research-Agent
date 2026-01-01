import ast
import importlib
import inspect
import json
import os
import sys
import time
import numpy as np
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import dataAnalysisPrompt1, dataAnalysisPrompt2, dataAnalysisPrompt3, adjustPrompt1
from Utils.Tools import evaluateOutput, getFormatOutput, _connectMySQL, _closeMySQL, load_instance, save_instance

"""对社会模拟器模拟的结果进行数据分析"""

def simulationAnsAnalyse(simulationContent,cotIndex,dataExam):
    model = ModelFactory("deepResearch").GetModel()
    model2 = ModelFactory("writingPaper").GetModel()
    chatHistory = []
    connection, cursor = _connectMySQL()
    findCotSql = f"SELECT topic,cotContent FROM `odd` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(findCotSql)
    cotResult = cursor.fetchall()
    topic = cotResult[0][0]
    cotProcessNode = cotResult[0][1]
    cotProcessNodeList = ast.literal_eval(cotProcessNode)
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    findCodeSql = f"SELECT entityNum FROM `code_ans` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(findCodeSql)
    entityNum = cursor.fetchall()[0][0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    OddSql = f"SELECT detail FROM `odd2` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(OddSql)
    record = cursor.fetchall()[0]
    detail_content = record[0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    restraintSql = f"SELECT restraintContent,pathPlanning FROM `env_restraint` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(restraintSql)
    envContent = cursor.fetchall()
    pathPlanningList = ast.literal_eval(envContent[0][1])
    _closeMySQL(connection, cursor)

    # 动态加载模块
    saveCodePath = '../../Data/Coding/Example' + str(PublicConfig.simulateIdConfig) + ".py"
    module_name = os.path.splitext(os.path.basename(saveCodePath))[0]
    spec = importlib.util.spec_from_file_location(module_name, saveCodePath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if dataExam:
        for i in range(1,entityNum+1):
            thisEntity = load_instance("../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"Copy2/entity"+str(i)+".pkl")
            instance_attr_names = thisEntity.__dict__.keys()
            instance_attr_list = list(instance_attr_names)
            for j in range(0,len(instance_attr_list)):
                instance_attr = instance_attr_list[j]
                attributeVal = getattr(thisEntity, instance_attr)
                if (not isinstance(attributeVal, list)) or (instance_attr == 'Actions') or (instance_attr == 'Position'):
                    continue
                retry_count = 0
                max_retries = 5
                while retry_count < max_retries:
                    try:
                        evaluatePrompt = adjustPrompt1.format(front_input = simulationContent,detail = str(detail_content),actionPlanner = str(pathPlanningList),actions = str(thisEntity.Actions),property = str(instance_attr),iniVal = str(attributeVal[0]))
                        while True:
                            propertyEvaluateAns = model2.invoke(evaluatePrompt)
                            inspectAns = evaluateOutput(evaluatePrompt, propertyEvaluateAns.content)
                            if inspectAns == True:
                                break
                        propertyEvaluateDict = json.loads(getFormatOutput(propertyEvaluateAns.content))
                        setattr(thisEntity,instance_attr,propertyEvaluateDict["propertyChange"])
                        save_instance(thisEntity,"../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"Copy2/entity"+str(i)+".pkl")
                        print(f"完成{i},{j}个的调整。")
                        break
                    except Exception as e:
                        retry_count += 1
                        print(f"第{retry_count}次重试，错误信息: {e}")
                        time.sleep(2)
                        if retry_count >= max_retries:
                            print(f"达到最大重试次数{max_retries}，跳过此属性的调整。")
                            raise Exception(f"已达到最大重试次数 {max_retries}") from e
            time.sleep(3)
    instance_attr_list = []
    for i in range(1,entityNum+1):
        tmpEntity = getattr(module, "entity"+str(i))
        instance_attr_names = tmpEntity.__dict__.keys()
        if list(instance_attr_names) not in instance_attr_list:
            instance_attr_list.append(list(instance_attr_names))
    instance_attr_list_array = list(set([item for sublist in instance_attr_list for item in sublist]))
    chatHistory.append(HumanMessage(dataAnalysisPrompt1.format(topic = topic,simulatorTopic = simulationContent,cotAns = str(cotProcessNodeList[cotIndex]),attributeName = str(instance_attr_list_array))))
    while True:
        questionAns = model.invoke(chatHistory)
        inspectAns = evaluateOutput(chatHistory[-1],questionAns.content)
        if inspectAns == True:
            break
    chatHistory.append(AIMessage(questionAns.content))
    questionDict = json.loads(getFormatOutput(questionAns.content))
    formatEntity = []
    for item in range(1,entityNum+1):
        formatAttribution = ""
        tmpEntity = getattr(module, "entity"+str(item))
        instance_attr_names = tmpEntity.__dict__.keys()
        instance_attr_list = list(instance_attr_names)
        for instance_attr in instance_attr_list:
            attributeVal = getattr(tmpEntity,instance_attr)
            formatAttribution = formatAttribution + f"属性名{instance_attr};属性内容:{attributeVal}。"
        formatEntity.append(formatAttribution)
    chatHistory.append(HumanMessage(dataAnalysisPrompt2.format(questions = str(questionDict['questions']),simulatorAns = str(formatEntity))))
    while True:
        AnswerAns = model.invoke(chatHistory)
        inspectAns = evaluateOutput(chatHistory[-1],questionAns.content)
        if inspectAns == True:
            break
    chatHistory.append(AIMessage(AnswerAns.content))
    answerDict = json.loads(getFormatOutput(AnswerAns.content))
    chatHistory.append(HumanMessage(dataAnalysisPrompt3.format(QuestionAndAnswer = str(answerDict["QuestionAndAnswer"]))))
    while True:
        conclusionAns = model.invoke(chatHistory)
        inspectAns = evaluateOutput(chatHistory[-1],conclusionAns.content)
        if inspectAns == True:
            break
    chatHistory.append(AIMessage(conclusionAns.content))
    conclusionDict = json.loads(getFormatOutput(conclusionAns.content))

    connection, cursor = _connectMySQL()
    saveSql = """INSERT INTO simulation_ans (id,simulationAnalyseContent,questionAndAnswer) VALUES (%s, %s ,%s)"""
    cursor.execute(saveSql, (PublicConfig.simulateIdConfig,conclusionDict["writingContent"],json.dumps(answerDict,ensure_ascii=False)))
    connection.commit()
    _closeMySQL(connection, cursor)

