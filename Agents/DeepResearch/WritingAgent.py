import ast
import json
import os
import time

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import writingIntroduction, writingPrompt1, writingPrompt2, writingPrompt3
from Utils.Tools import _connectMySQL, _closeMySQL, evaluateOutput, getFormatOutput

"""把规划后调研的内容整合，正式写作"""

def writeAndIntegration(query):
    #准备工作
    model = ModelFactory("writingPaper").GetModel()
    model2 = ModelFactory("writingPaper").GetModel()

    chatHistory = []
    cotAndGneration = {}
    generationPaperList = []

    connection, cursor = _connectMySQL()
    findResearchSql = f"SELECT topic,generationContent FROM `research_ans` WHERE taskId = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findResearchSql)
    researchResults = cursor.fetchall()
    topic = researchResults[0][0]
    generationContent = [row[1] for row in researchResults]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    findCotSql = f"SELECT cotList FROM `cot_ans` WHERE id = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findCotSql)
    cotList = ast.literal_eval(cursor.fetchall()[0][0])
    _closeMySQL(connection, cursor)

    if len(cotList) != len(generationContent):
        print("前一步COT生成内容错误")
    for i in range(0, len(generationContent)):
        cotAndGneration["COT推理思考结果如下，"+cotList[i]] = "通过调研后生成的初步写作结果如下，"+generationContent[i]


    connection, cursor = _connectMySQL()
    findOutputStyle = f"SELECT writingStyle,styleContent,wordCount FROM `genre` INNER JOIN user_demand where user_demand.id = \'{PublicConfig.taskIdConfig}\' and user_demand.outputStyle = genre.writingStyle"
    cursor.execute(findOutputStyle)
    genreContent = cursor.fetchall()
    writingStyle = genreContent[0][0]
    outputStyleList = ast.literal_eval(genreContent[0][1])
    wordCountList = ast.literal_eval(genreContent[0][2])
    _closeMySQL(connection, cursor)

    tmpAns = ""
    #开始写作COT
    chatHistory.append(SystemMessage(writingIntroduction.format(topic = topic,style = writingStyle,styleContent = str(outputStyleList))))
    i = 0
    maxretry = 3
    retry = 0
    while i < len(outputStyleList):
        original_chat_len = len(chatHistory)
        try:
            outputStyle = outputStyleList[i]
            wordCount = wordCountList[i]
            chatHistory.append(
                HumanMessage(writingPrompt1.format(CotContent=str(cotAndGneration), styleContentNode=str(outputStyle),wordCount = str(wordCount))))
            while True:
                writingAns = model.invoke(chatHistory)
                inspectAns = evaluateOutput(chatHistory[-1], writingAns.content)
                if inspectAns == True:
                    break
            chatHistory.append(AIMessage(writingAns.content))
            writingDict = json.loads(getFormatOutput(writingAns.content))
            generationPaperList.append(writingDict["writingPart"])
            tmpAns += writingDict["writingPart"]+"\n"
            print(f"第{i}部分写作思考结束")
            i += 1
        except Exception as e:
            chatHistory = chatHistory[:original_chat_len]
            print(f"第{i}部分执行失败：{e}，即将重新执行第{i}部分...")
            time.sleep(20)
            retry += 1
            if retry > maxretry:
                raise f"执行{maxretry}失败，停止执行。"
    print(generationPaperList)
    integrationHistory =  []
    integrationHistory.append(SystemMessage(writingIntroduction.format(topic = topic,style = writingStyle,styleContent = str(outputStyleList))))
    integrationHistory.append(HumanMessage(writingPrompt2.format(writingList = str(generationPaperList),paperWords = str(wordCountList[-1]))))
    while True:
        integrationAns = model2.invoke(integrationHistory)
        inspectAns = evaluateOutput(integrationHistory[-1], integrationAns.content)
        if inspectAns == True:
            break
    integrationDict = json.loads(getFormatOutput(integrationAns.content))
    generationPaper = integrationDict["writingAns"]
    # 生成内容持久化
    file_path = "D:\技术资料\Agent相关\SocialScience&&DeepResearch\Data\paperAns\paper" + str(PublicConfig.taskIdConfig) + ".jsonl"
    folder_path = os.path.dirname(file_path)
    os.makedirs(folder_path, exist_ok=True)
    """!!!这个最后要做一个参考文献的生成与拼接"""
    referenceInfoList = []
    connection, cursor = _connectMySQL()
    findResearchSql = f"SELECT paperName,author,publishYear,jounalName FROM `search_ans` WHERE taskId = \'{PublicConfig.taskIdConfig}\'"
    cursor.execute(findResearchSql)
    searchResults = cursor.fetchall()
    _closeMySQL(connection, cursor)
    for searchResult in searchResults:
        referenceInfoList.append(f"参考文献标题:{searchResult[0]}。参考文献作者:{searchResult[1]}。参考文献出版年份:{searchResult[2]}。参考文献的出版期刊:{searchResult[3]}")
    referenceGeneration = [HumanMessage(writingPrompt3.format(referenceInfo = str(referenceInfoList)))]
    time.sleep(20)
    while True:
        referenceAns = model.invoke(referenceGeneration)
        inspectAns = evaluateOutput(referenceGeneration, referenceAns.content)
        if inspectAns == True:
            break
    referenceDict = json.loads(getFormatOutput(referenceAns.content))
    generationPaper += "\n".join(referenceDict["referenceList"])
    # 写入字符串到jsonl里面
    generationDict = {"id": PublicConfig.taskIdConfig, "prompt": query, "article": generationPaper}
    with open(file_path, "a", encoding="utf-8") as f:
        json.dump(generationDict, f , ensure_ascii=False)
        f.write("\n")
    print("论文生成结束")
