import ast
import configparser
import json
import os
import time

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from Agents.DeepResearch.DeepResearchPlannerAgent import preDemand
from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import executorInstruction, executorPrompt1, executorPrompt2
from Utils.Tools import _connectMySQL, _closeMySQL, evaluateOutput, getFormatOutput
from Utils.crawlQA import getPaperByOpenAlex, get_dois_by_keyword, baiduSearch


##执行Deepresearch论文具体内容生成的智能体

def deepResearchExecutor():
    userDemand =preDemand()
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
    findCotSql = f"SELECT cotList FROM `cot_ans` WHERE id = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findCotSql)
    cotProcess = ast.literal_eval(cursor.fetchall()[0][0])
    _closeMySQL(connection, cursor)

    model = ModelFactory("deepResearch").GetModel()
    executorHistory = []
    executorHistory.append(SystemMessage(executorInstruction.format()))
    connection, cursor = _connectMySQL()
    findGenreSql = f"SELECT styleContent FROM `genre` WHERE writingStyle = \'{userDemand.outputStyle}\'"
    cursor.execute(findGenreSql)
    genreContent = ast.literal_eval(cursor.fetchall()[0][0])
    _closeMySQL(connection, cursor)
    #根据思维链拿到
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    config_path = os.path.join(current_dir, "../../Config/config.ini")
    config_path = os.path.normpath(config_path)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    toolAns = {}
    toolType = {}
    isSocialExperiment = False
    i = 0
    while i < len(cotProcess):
        original_chat_len = len(executorHistory)
        try:
            executorHistory.append(HumanMessage(executorPrompt1.format(topic = userDemand.topic, socialScienceType = str(userDemand.socialScienceType),researchTrend = userDemand.researchTrend,genre = userDemand.outputStyle,
                                                                 genreContent = genreContent , thinkingProcess = str(cotProcess[i]),isSocialExperiment = ("已经进行过社会模拟实验，只能调用文献检索工具，不能再次进行社会模拟实验" if isSocialExperiment else "还未进行过社会模拟实验，可以选择进行社会模拟实验"))))
            while True:
                toolUseAns = model.invoke(executorHistory)
                inspectAns = evaluateOutput(executorHistory[-1],toolUseAns.content)
                if inspectAns == True:
                    break
            toolUseDict = json.loads(getFormatOutput(toolUseAns.content))
            executorHistory.append(AIMessage(toolUseAns.content))
            #工具调用
            toolDetail = toolUseDict
            toolType[i] = "暂时未使用工具"
            toolAns[i] = "暂时没有使用工具产生的结果"
            if toolDetail["isSearchPaper"] == True:
                toolType[i] = "检索相关文献"
                searchCount = 0
                for key in toolDetail["searchKey"]:
                    if searchCount == 0 or searchCount == 1:
                        ansContent = getPaperByOpenAlex(key)
                        if len(ansContent) != 0:
                            searchAns = []
                            connection, cursor = _connectMySQL()
                            for ansContentItem in ansContent:
                                searchAns.append(f"文献标题为:{ansContentItem['title']}。文献内容为:{ansContentItem['fullText'] if len(ansContentItem['fullText'])!=0 else ansContentItem['abstract']}。")
                                searchSql = """INSERT INTO search_ans (topic,cotIndex,searchKey,searchContent,paperName,taskId,author,publishYear,jounalName) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                                cursor.execute(searchSql,(userDemand.topic, str(i), str(toolDetail["searchKey"]), ansContentItem['abstract'],ansContentItem['title'],PublicConfig.taskIdConfig,ansContentItem['author'],ansContentItem['publishTime'],ansContentItem['journal'],))
                                connection.commit()
                            _closeMySQL(connection, cursor)
                            toolAns[i] = str(searchAns)
                    else:
                        if toolAns[i] == "暂时没有使用工具产生的结果":
                            break
                        baiduAns = baiduSearch(key)
                        baiduTmp = ""
                        for key,value in baiduAns.items():
                            baiduTmp = baiduTmp + f"联网检索的结果如下:标题为{str(key)},检索结果为{str(value)}。\n"
                        toolAns[i] = baiduTmp
                    searchCount += 1
            if toolDetail["isSocialSimulate"] == True:
                isSocialExperiment = True
                toolType[i] = "使用社会模拟器进行社会实验"
                # simulationContent = startSimulation()
                # analyseAns = simulationAnsAnalyse(simulationContent,cotProcess[i])
                # connection, cursor = _connectMySQL()
                # searchSql = """INSERT INTO simulation_ans (simulationAnalyseContent) VALUES (%s)"""
                # cursor.execute(searchSql, (analyseAns))
                # connection.commit()
                # _closeMySQL(connection, cursor)
                toolAns[i] = "社会实验进行当中"
                pass
            writingDetailDict = {"writingContent":"待后续补充"}
            if toolAns[i] != "暂时没有使用工具产生的结果" and toolAns[i] != "文献查找当中" and toolAns[i] != "社会实验进行当中":
                executorHistory.append(HumanMessage(executorPrompt2.format(topic = userDemand.topic,socialScienceType = str(userDemand.socialScienceType),
                                                               thinkingNode = str(cotProcess[i]),toolAns = toolAns[i])))
                while True:
                    writingDetailAns = model.invoke(executorHistory)
                    inspectAns = evaluateOutput(executorHistory[-1], writingDetailAns.content)
                    if inspectAns == True:
                        break
                connection, cursor = _connectMySQL()
                writingDetailDict = json.loads(getFormatOutput(writingDetailAns.content))
                _closeMySQL(connection, cursor)
            if "writingContent" not in writingDetailDict:
                writingDetailDict["writingContent"] = "待后续补充"
            if toolDetail["isSearchPaper"] == False and toolDetail["isSocialSimulate"] == False:
                writingDetailDict["writingContent"] = "不需要调用工具"
            connection, cursor = _connectMySQL()
            searchSql = """INSERT INTO research_ans (topic,cotIndex,generationContent,cotContent,taskId,toolDetail) VALUES (%s, %s, %s,%s,%s,%s)"""
            cursor.execute(searchSql, (userDemand.topic, str(i), writingDetailDict["writingContent"],cotProcess[i],PublicConfig.taskIdConfig,json.dumps(toolDetail, ensure_ascii=False)))
            connection.commit()
            _closeMySQL(connection, cursor)
            i += 1
            print("工具调用结束")
        except Exception as e:
            executorHistory = executorHistory[:original_chat_len]
            time.sleep(10)
            print(e)
