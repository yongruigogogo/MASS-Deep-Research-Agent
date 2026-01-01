import json
from typing import List, Any, Optional, Dict

from Agents.DeepResearch.DeepResearchPlannerAgent import preDemand
from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from Utils.PromptHelper import oodStartInstruction, questionPrompt, overviewPrompt, designConceptPrompt, detailPrompt
from Utils.Tools import evaluateOutput, getFormatOutput, _connectMySQL, _closeMySQL
from Utils.crawlQA import baiduSearch

"""
规划器，生成ODD协议，规划模拟流程
"""

def socialSimulationStart(front_input):
    # 问答的历史记录
    chatHistoryPlanner = []
    questionAndAnswer = {}
    model = ModelFactory("deepResearch").GetModel()
    connection, cursor = _connectMySQL()
    findGenreSql = f"SELECT topic FROM `user_demand` WHERE id = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findGenreSql)
    topic = cursor.fetchall()[0][0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    findGenreSql = f"SELECT cotList FROM `cot_ans` WHERE id = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findGenreSql)
    cotContent = cursor.fetchall()[0][0]
    _closeMySQL(connection, cursor)
    chatHistoryPlanner.append(SystemMessage(oodStartInstruction.format()))
    chatHistoryPlanner.append(HumanMessage(questionPrompt.format(topic = topic,front_input = front_input)))
    while True:
        questionsAns = model.invoke(chatHistoryPlanner)
        inspectAns = evaluateOutput(chatHistoryPlanner[-1],questionsAns.content)
        if inspectAns == True:
            break
    chatHistoryPlanner.append(AIMessage(questionsAns.content))
    questionsDict = json.loads(getFormatOutput(questionsAns.content))
    for question in questionsDict["questions"]:
        searchAns = baiduSearch(question)
        questionAndAnswer[question] = str(searchAns)
    #生成Overview的结果
    chatHistoryPlanner.append(HumanMessage(overviewPrompt.format(qAndAnswer = str(questionAndAnswer))))
    while True:
        overviewAns = model.invoke(chatHistoryPlanner)
        inspectAns = evaluateOutput(chatHistoryPlanner[-1],overviewAns.content)
        if inspectAns == True:
            break
    chatHistoryPlanner.append(AIMessage(overviewAns.content))
    overviewDict = json.loads(getFormatOutput(overviewAns.content))
    print("overview完成")
    #生成design的结果
    chatHistoryPlanner.append(HumanMessage(designConceptPrompt.format()))
    while True:
        designConceptAns = model.invoke(chatHistoryPlanner)
        inspectAns = evaluateOutput(chatHistoryPlanner[-1],designConceptAns.content)
        if inspectAns == True:
            break
    chatHistoryPlanner.append(AIMessage(designConceptAns.content))
    designConceptDict = json.loads(getFormatOutput(designConceptAns.content))
    print("design完成")
    #生成detail的结果
    chatHistoryPlanner.append(HumanMessage(detailPrompt.format()))
    while True:
        detailAns = model.invoke(chatHistoryPlanner)
        inspectAns = evaluateOutput(chatHistoryPlanner[-1],detailAns.content)
        if inspectAns == True:
            break
    chatHistoryPlanner.append(AIMessage(detailAns.content))
    detailDict = json.loads(getFormatOutput(detailAns.content))
    print("detail完成")
    print(len(str(cotContent)),len(json.dumps(overviewDict)),len(json.dumps(designConceptDict)),len(json.dumps(detailDict)))
    connection, cursor = _connectMySQL()
    oddSql = """INSERT INTO odd (id,topic,cotContent,overView,designConcept) VALUES (%s, %s, %s, %s, %s)"""
    oddSql2 = """INSERT INTO odd2 (id,detail) VALUES (%s, %s)"""
    cursor.execute(oddSql, (PublicConfig.simulateIdConfig,topic,str(cotContent),json.dumps(overviewDict, ensure_ascii=False, indent=2),json.dumps(designConceptDict, ensure_ascii=False, indent=2)))
    cursor.execute(oddSql2, (PublicConfig.simulateIdConfig,json.dumps(detailDict,ensure_ascii=False, indent=2)))
    connection.commit()
    _closeMySQL(connection,cursor)

