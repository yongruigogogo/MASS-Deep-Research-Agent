import ast
import copy
import importlib
import json
import os
import random
import sys
import time

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import MemoryCOTIntroduction, MemoryCOTPrompt1, MemoryCOTPrompt6, MemoryCOTPrompt2, \
    MemoryCOTPrompt3, MemoryCOTPrompt4, MemoryCOTPrompt5
from Utils.Tools import _connectMySQL, evaluateOutput, RAGsearch, getEmbedding, save_instance, _closeMySQL, \
    getFormatOutput

"""通过RAG去检索相关的初始记忆，进行冷启动"""

def initializeMemory():
    model = ModelFactory("deepResearch").GetModel()

    connection, cursor = _connectMySQL()
    OddSql = f"SELECT detail FROM `odd2` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(OddSql)
    record = cursor.fetchall()[0]
    detail_content = record[0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    restraintSql = f"SELECT restraintContent FROM `env_restraint` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(restraintSql)
    restraintContent = cursor.fetchall()[0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    codeSql = f"SELECT entityNum FROM `code_ans` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(codeSql)
    entityNum = cursor.fetchall()[0][0]
    _closeMySQL(connection, cursor)

    saveCodePath = '../../Data/Coding/Example'+str(PublicConfig.simulateIdConfig)+".py"
    #保存类里面的实例
    module_name = os.path.splitext(os.path.basename(saveCodePath))[0]
    # 动态加载模块
    spec = importlib.util.spec_from_file_location(module_name, saveCodePath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # 执行模块代码（此时实例会被创建）
    for i in range(1,entityNum+1):
        cotAns1 = []
        cotAns2 = []
        cotAns3 = []
        cotAns4 = []
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                tmpEntity = getattr(module,"entity"+str(i))
                chatHistory = []
                chatHistory.append(
                    SystemMessage(MemoryCOTIntroduction.format(details=detail_content, restriant=restraintContent)))
                #进行四次推理
                chatHistory.append(HumanMessage(MemoryCOTPrompt1.format(features = str(tmpEntity))))
                while True:
                    cotAns = model.invoke(chatHistory)
                    inspectAns = evaluateOutput(chatHistory[-1], cotAns.content)
                    if inspectAns == True:
                        break
                cotAns1Dict = json.loads(getFormatOutput(cotAns.content))
                cotAns1.append(cotAns1Dict["reasoningAns"])
                chatHistory.append(AIMessage(cotAns.content))
                print("1\n")

                chatHistory.append(HumanMessage(MemoryCOTPrompt2.format(features=str(tmpEntity))))
                while True:
                    cotAns = model.invoke(chatHistory)
                    inspectAns = evaluateOutput(chatHistory[-1], cotAns.content)
                    if inspectAns == True:
                        break
                cotAns2Dict = json.loads(getFormatOutput(cotAns.content))
                cotAns2.append(cotAns2Dict["reasoningAns"])
                chatHistory.append(AIMessage(cotAns.content))
                print("2\n")

                chatHistory.append(HumanMessage(MemoryCOTPrompt3.format(features=str(tmpEntity))))
                while True:
                    cotAns = model.invoke(chatHistory)
                    inspectAns = evaluateOutput(chatHistory[-1], cotAns.content)
                    if inspectAns == True:
                        break
                cotAns3Dict = json.loads(getFormatOutput(cotAns.content))
                cotAns3.append(cotAns3Dict["reasoningAns"])
                chatHistory.append(AIMessage(cotAns.content))
                print("3\n")

                chatHistory.append(HumanMessage(MemoryCOTPrompt4.format(features=str(tmpEntity))))
                while True:
                    cotAns = model.invoke(chatHistory)
                    inspectAns = evaluateOutput(chatHistory[-1], cotAns.content)
                    if inspectAns == True:
                        break
                cotAns4Dict = json.loads(getFormatOutput(cotAns.content))
                cotAns4.append(cotAns4Dict["reasoningAns"])
                chatHistory.append(AIMessage(cotAns.content))
                print("4\n")

                connection, cursor = _connectMySQL()
                typeSql = f"SELECT socialScienceType FROM `user_demand` WHERE id = \'{PublicConfig.taskIdConfig}\'"
                cursor.execute(typeSql)
                socialScienceTypeContent = cursor.fetchall()[0][0]
                genreList = ast.literal_eval(socialScienceTypeContent)
                chatHistory.append(HumanMessage(MemoryCOTPrompt5.format(styleGenre = str(genreList),cot1=str(cotAns1),cot2=str(cotAns2),cot3=str(cotAns3),cot4=str(cotAns4))))
                while True:
                    summarizeAns = model.invoke(chatHistory)
                    inspectAns = evaluateOutput(chatHistory[-1], summarizeAns.content)
                    if inspectAns == True:
                        break
                summarizeDict = json.loads(getFormatOutput(summarizeAns.content))
                #用结合推理出来的结果去做RAG
                genreToDbname = {"经济学":"../../Data/EmbeddingGeneration/EmbeddingData/economicalEmbedding.jsonl","历史学":"../../Data/EmbeddingGeneration/EmbeddingData/historyEmbedding.jsonl","法学":"../../Data/EmbeddingGeneration/EmbeddingData/jurisprudenceEmbedding.jsonl","政治学":"../../Data/EmbeddingGeneration/EmbeddingData/politicsEmbedding.jsonl","心理学":"../../Data/EmbeddingGeneration/EmbeddingData/psychologyEmbedding.jsonl","社会学":"../../Data/EmbeddingGeneration/EmbeddingData/societyEmbedding.jsonl"}
                tmpQuery = []
                tmpMemory = []
                tmpgenre = []
                for genre,query in summarizeDict.items():
                    tmpQuery.append(query)
                    queryEmbedding,successReturn = getEmbedding(query)
                    tmpgenre.append(genre)
                    if not successReturn:
                        continue
                    res = RAGsearch(2,queryEmbedding,genreToDbname[genre])
                    tmpMemory.extend(res)
                if len(tmpMemory) > 0:
                    tmpEntity.Actions.append(tmpMemory[random.randint(0,len(tmpMemory)-1)])
                else:
                    #如果embedding失败就稍后补充
                    randomIndex = random.randint(0,len(tmpQuery)-1)
                    queryFilePath = "../../Data/EmbeddingGeneration/queryAndEmbedding/query"+str(PublicConfig.simulateIdConfig)+"Old"+".jsonl"
                    with open(queryFilePath, "a", encoding="utf-8") as f:
                        json_obj = {"entityIndex":tmpEntity.Id,"oldText":tmpQuery[randomIndex],"embedding":"","subject":tmpgenre[randomIndex]}
                        f.write(json.dumps(json_obj,ensure_ascii=False)+"\n")
                persistenceFilePath = "../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/entity" + str(i) + ".pkl"
                dir_path = os.path.dirname(persistenceFilePath)
                os.makedirs(dir_path, exist_ok=True)
                save_instance(tmpEntity, persistenceFilePath)
                print(f"{i}保存结束")
                break
            except Exception as e:
                retry_count += 1
                print(f"第{retry_count}次重试，错误信息: {e}")
                if retry_count >= max_retries:
                    print(f"达到最大重试次数{max_retries}，跳过此属性的调整。")
                    raise Exception(f"已达到最大重试次数 {max_retries}") from e


