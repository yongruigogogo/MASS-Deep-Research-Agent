# -*- coding: utf-8 -*-
import ast
import json
from langchain_core.messages import SystemMessage, HumanMessage
from Agents.DeepResearch.DeepResearchPlannerAgent import deepResearchPlanner, preDemand
from Agents.DeepResearch.ExecutorAgent import deepResearchExecutor
from Agents.DeepResearch.WritingAgent import writeAndIntegration
from Agents.SocialSimulation.StartSimulation import startSimulation
from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import executorInstruction, executorPrompt2
from Utils.Tools import _connectMySQL, _closeMySQL, evaluateOutput, getFormatOutput
from Utils.crawlQA import baiduSearch

"""DeepResearch启动包"""
def supplyExecutor():
    model = ModelFactory("deepResearch").GetModel()
    userDemand = preDemand()
    connection, cursor = _connectMySQL()
    findDemandSql = f"SELECT topic,socialScienceType,outputStyle,researchTrend FROM `user_demand` WHERE id = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findDemandSql)
    demandResult = cursor.fetchall()
    userDemand.topic = demandResult[0][0]
    userDemand.socialScienceType = ast.literal_eval(demandResult[0][1])
    userDemand.outputStyle = demandResult[0][2]
    userDemand.researchTrend = demandResult[0][3]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    findResearchAnsSql = f"SELECT cotIndex,generationContent,cotContent,toolDetail FROM `research_ans` WHERE taskId = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findResearchAnsSql)
    ReserchAnses = cursor.fetchall()
    _closeMySQL(connection, cursor)

    i = 0
    maxretry = 3
    retry = 0
    while i < len(ReserchAnses):
        researchAns = ReserchAnses[i]
        try:
            chatHistory =[]
            chatHistory.append(SystemMessage(executorInstruction.format()))
            cotIndex = researchAns[0]
            generationContent = researchAns[1]
            cotContent = researchAns[2]
            toolDetailDict = json.loads(researchAns[3])
            if generationContent != "待后续补充":
                i += 1
                continue
            serchAns = None
            simulationAnalyseContent = None
            if toolDetailDict["isSearchPaper"] == True and researchAns[1] == "待后续补充":
                connection, cursor = _connectMySQL()
                findSearchAnsSql = f"SELECT searchKey,paperName,searchContent FROM `search_ans` WHERE taskId = \'{PublicConfig.taskIdConfig}\' and cotIndex = {cotIndex}"
                cursor.execute(findSearchAnsSql)
                serchAns = cursor.fetchall()
                _closeMySQL(connection, cursor)
                if serchAns is None or len(serchAns) == 0:
                    serchAns = "联网检索"
            if toolDetailDict["isSocialSimulate"] == True and researchAns[1] == "待后续补充":
                connection, cursor = _connectMySQL()
                findSearchAnsSql = f"SELECT simulationAnalyseContent FROM `simulation_ans` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
                cursor.execute(findSearchAnsSql)
                simulationAnalyseContent = cursor.fetchall()[0][0]
                _closeMySQL(connection, cursor)
            toolAns = ""
            if serchAns == "联网检索" or (serchAns is not None and len(serchAns) != 0):
                if serchAns != "联网检索":
                    paperContent = [f"查找关键词: {row[0]}, 文献名称: {row[1]}, 文献查找结果: {row[2]}" for row in serchAns]
                    toolAns += f"对于该部分的推理内容，文献检索如下所示:{str(paperContent)}\n"
                #联网宽泛检索资料
                baiduAns = baiduSearch(toolDetailDict["searchKey"][2])
                baiduTmp = ""
                for key, value in baiduAns.items():
                    baiduTmp = baiduTmp + f"联网检索的结果如下:标题为{str(key)},检索结果为{str(value)}。\n"
                toolAns += baiduTmp
                chatHistory.append(HumanMessage(
                    executorPrompt2.format(topic=userDemand.topic, socialScienceType=str(userDemand.socialScienceType),
                                           thinkingNode=str(cotContent), toolAns=toolAns)))
                while True:
                    writingDetailAns = model.invoke(chatHistory)
                    inspectAns = evaluateOutput(chatHistory[-1], writingDetailAns.content)
                    if inspectAns == True:
                        break
                writingDetailDict = json.loads(getFormatOutput(writingDetailAns.content))
                connection, cursor = _connectMySQL()
                findSearchAnsSql = f"UPDATE research_ans SET generationContent = %s WHERE taskId = \'{PublicConfig.taskIdConfig}\' and cotIndex = {cotIndex}"
                cursor.execute(findSearchAnsSql, (writingDetailDict["writingContent"],))
                connection.commit()
                _closeMySQL(connection, cursor)
            if simulationAnalyseContent is not None and len(simulationAnalyseContent) != 0:
                connection, cursor = _connectMySQL()
                findSearchAnsSql = f"UPDATE research_ans SET generationContent = %s WHERE taskId = \'{PublicConfig.taskIdConfig}\' and cotIndex = {cotIndex}"
                cursor.execute(findSearchAnsSql, (simulationAnalyseContent,))
                connection.commit()
                _closeMySQL(connection, cursor)
            i += 1
        except Exception as e:
            retry += 1
            if retry > maxretry:
                raise f"执行{maxretry}失败，停止执行。"
            print(f"第{i}部分执行失败：{e}，即将重新执行第{i}部分...")


def agentStart(query):
    deepResearchPlanner(query)
    deepResearchExecutor()
    index = 0
    connection, cursor = _connectMySQL()
    findResearchAnsSql = f"SELECT toolDetail FROM `research_ans` WHERE taskId = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findResearchAnsSql)
    ReserchAnses = cursor.fetchall()
    _closeMySQL(connection, cursor)
    for researchAns in ReserchAnses:
        toolDetailDict = json.loads(researchAns[0])
        if toolDetailDict["isSocialSimulate"]:
            startSimulation(toolDetailDict["SocialSimulateContent"],index)
        index +=1
    supplyExecutor()
    writeAndIntegration(query)