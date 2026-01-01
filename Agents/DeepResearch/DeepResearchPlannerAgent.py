import configparser
import copy
import json
import time
from pydoc import describe
from typing import Optional, List
from exceptiongroup import catch
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from pydantic import Field, BaseModel
from Agents.DeepResearch.EvaluateAgent import evaluateCOT
from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import deepResearchPlannerInstruction, deepResearchPlannerPrompt1, aiReQuestionPrompt, \
    deepResearchPlannerPrompt2, deepResearchPlannerPrompt3, deepResearchPlannerPrompt4, deepResearchVotePrompt, \
    deepResearchPlannerPrompt5
from Utils.Tools import evaluateOutput, getFormatOutput, _connectMySQL, _closeMySQL
from Utils.crawlQA import baiduSearch
import mysql.connector
from mysql.connector import Error


class preDemand(BaseModel):
    #预先的要求
    topic:Optional[str] = Field(default="",description="社科研究课题的的大致科研主题")
    socialScienceType:Optional[List[str]] = Field(default="",description="社科研究课题所属于的研究门类")
    outputStyle:Optional[str] = Field(default="",description="研究人员所需要输出文本的体裁类型")
    researchTrend:Optional[str] = Field(default="",description="研究人员的研究倾向，希望后续进行什么样的研究多一些")

    def to_dict(self):
        return{
            "topic":self.topic,
            "socialScienceType":self.socialScienceType,
            "outputStyle":self.outputStyle,
            "researchTrend":self.researchTrend
        }

#多组思维链进行任务规划
def deepResearchPlanner(query):
    model = ModelFactory("deepResearch").GetModel()
    chatHistory = []
    chatHistory.append(SystemMessage(deepResearchPlannerInstruction.format()))
    aiGuidingAns = model.invoke(chatHistory)
    chatHistory.append(AIMessage(aiGuidingAns.content))
    print(aiGuidingAns.content)
    researchTopic = query
    chatHistory.append(HumanMessage(deepResearchPlannerPrompt1.format(userResponse = researchTopic)))
    while True:
        inputAnalyseAns = model.invoke(chatHistory)
        inspectAns = evaluateOutput(chatHistory[-1],inputAnalyseAns.content)
        if inspectAns == True:
            break
    inputAnalyseDict = json.loads(getFormatOutput(inputAnalyseAns.content))
    chatHistory.append(AIMessage(inputAnalyseAns.content))
    demandAns = preDemand.model_validate(inputAnalyseDict)
    connection, cursor = _connectMySQL()
    findGenreSql = """INSERT IGNORE INTO user_demand (id,topic,socialScienceType,outputStyle,researchTrend) VALUES (%s, %s, %s, %s, %s)"""
    cursor.execute(findGenreSql,(PublicConfig.taskIdConfig,demandAns.topic,str(demandAns.socialScienceType),demandAns.outputStyle,demandAns.researchTrend))
    connection.commit()
    _closeMySQL(connection, cursor)
    fields = demandAns.model_fields
    for field_name,field in fields.items():
        field_value = getattr(demandAns, field_name)
        if field_name == "socialScienceType" and (not field_value or field_value is None):
            print("您所提供的研究课题不属于社会科学的研究范畴，请在社会科学的研究范围内提出研究课题谢谢。")
        elif field_value == "":
            chatHistory.append(SystemMessage(aiReQuestionPrompt.format(field.description)))
            response = model.invoke(chatHistory)
            chatHistory.append(AIMessage(response.content))
            setattr(demandAns, field_name, response.content)
    searchDict = baiduSearch(demandAns.topic)
    connection,cursor = _connectMySQL()
    findGenreSql = f"SELECT styleContent FROM `genre` WHERE writingStyle = \'{demandAns.outputStyle}\'"
    cursor.execute(findGenreSql)
    writingStyle = cursor.fetchall()[0]
    _closeMySQL(connection,cursor)
    COTProcess = []
    cotHistory = []
    cotHistory.append(
        SystemMessage(deepResearchPlannerPrompt2.format(topic=demandAns.topic, searchContent=str(searchDict),
                                                        genreType=demandAns.outputStyle, genreContent=writingStyle,
                                                        researchTrend=demandAns.researchTrend,
                                                        socialScienceType=str(demandAns.socialScienceType))))
    while True:
        cotAns = model.invoke(cotHistory)
        inspectAns = evaluateOutput(cotHistory[-1], cotAns.content)
        if inspectAns == True:
            break
    cotDict = json.loads(getFormatOutput(cotAns.content))
    COTProcess.append(cotDict['thinkingContent'])
    cotHistory.append(AIMessage(cotAns.content))
    thinkingIndex = 0
    while True:
        original_chat_len = len(chatHistory)
        try:
            tmpCotProcess = []
            tmpCotProcessScore = []
            if cotDict["ISInternet"] == "True" and cotDict["keyWord"] != "":
                searchDict = baiduSearch(cotDict["keyWord"])
            for i in range(1,6):
                tmpCotHistory = copy.deepcopy(cotHistory)
                tmpCotHistory.append(HumanMessage(deepResearchPlannerPrompt3.format(searchAns = str(searchDict),thinkingProcess = str(tmpCotProcess))))
                while True:
                    tmpCotAns = model.invoke(tmpCotHistory)
                    inspectAns = evaluateOutput(tmpCotHistory[-1], tmpCotAns.content)
                    if inspectAns == True:
                        break
                tmpCotDict = json.loads(getFormatOutput(tmpCotAns.content))
                tmpCotScore = evaluateCOT(demandAns,COTProcess,tmpCotDict["thinkingContent"])
                tmpCotHistory.append(AIMessage(tmpCotAns.content))
                for item,score in tmpCotScore.items():
                    if float(score) < 5:
                        tmpCotHistory.append(HumanMessage(deepResearchPlannerPrompt4.format(scoreItem = item,scoreNum = score,oldThinking = tmpCotDict["thinkingContent"])))
                        while True:
                            reShapeAns = model.invoke(tmpCotHistory)
                            inspectAns = evaluateOutput(tmpCotHistory[-1], reShapeAns.content)
                            if inspectAns == True:
                                break
                        reShapeDict = json.loads(getFormatOutput(reShapeAns.content))
                        tmpCotHistory.append(AIMessage(reShapeAns.content))
                        tmpCotDict["thinkingContent"] = reShapeDict["thinkingContent"]
                tmpCotProcess.append(tmpCotDict)
                total = 0.0  # 初始化总和为0.0
                for value_str in tmpCotScore.values():
                    try:
                        value_float = float(value_str)
                        total += value_float  # 累加
                    except ValueError:
                        print(f"警告：'{value_str}' 不是有效的数字字符串，已跳过")
                tmpCotProcessScore.append(total)
                print("处理完一个")
                # time.sleep(2)
            print("开始投票")
            while True:
                voteAns = model.invoke(deepResearchVotePrompt.format(views = str(tmpCotProcess)))
                inspectAns = evaluateOutput(deepResearchVotePrompt.format(views = str(tmpCotProcess)), voteAns.content)
                if inspectAns == True:
                    break
            voteDict = json.loads(getFormatOutput(voteAns.content))
            cotDict = tmpCotProcess[int(voteDict["index"])]
            COTProcess.append(tmpCotProcess[int(voteDict["index"])]['thinkingContent'])
            cotHistory.append(AIMessage("本次规划Agent想出来的思维链如下所示:"+str(COTProcess[-1])))
            thinkingIndex += 1
            if thinkingIndex <= 6:
                continue
            cotHistory.append(HumanMessage(deepResearchPlannerPrompt5.format(thinkingProcess = str(COTProcess),genre = demandAns.outputStyle, genreContent = writingStyle,thinkingNum = len(COTProcess))))
            while True:
                finishAns = model.invoke(cotHistory)
                inspectAns = evaluateOutput(cotHistory[-1], finishAns.content)
                if inspectAns == True:
                    break
            finishDict = json.loads(getFormatOutput(finishAns.content))
            if str(finishDict["IsEnd"]) == "True":
                break
            # time.sleep(2)
        except Exception as e:
            chatHistory = chatHistory[:original_chat_len]
            time.sleep(8)
            print(e)
    connection, cursor = _connectMySQL()
    findGenreSql = """INSERT INTO cot_ans (id,cotList) VALUES (%s,%s)"""
    cursor.execute(findGenreSql,(PublicConfig.taskIdConfig,str(COTProcess)))
    connection.commit()
    _closeMySQL(connection, cursor)
