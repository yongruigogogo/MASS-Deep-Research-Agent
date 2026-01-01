import importlib
import json
import os
import random
import sys
import time

from Agents.SocialSimulation.CodeGeneration import codeGeneration
from Agents.SocialSimulation.DataAnalyseAgent import simulationAnsAnalyse
from Agents.SocialSimulation.EnvGeneration import enviromentGeneration
from Agents.SocialSimulation.InitializeMemory import initializeMemory
from Agents.SocialSimulation.Planner import socialSimulationStart
from Agents.SocialSimulation.Process import simulateProcess
from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import adjustTopicPrompt
from Utils.Tools import _connectMySQL, _closeMySQL, RAGsearch, load_instance, save_instance, evaluateOutput, \
    getFormatOutput


def Memorysupply(SocialSimulateContent):
    model = ModelFactory("socialSimulate").GetModel()
    connection, cursor = _connectMySQL()
    codeSql = f"SELECT entityNum FROM `code_ans` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(codeSql)
    entityNum = cursor.fetchall()[0][0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    codeSql = f"SELECT restraintContent,pathPlanning FROM `env_restraint` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(codeSql)
    result = cursor.fetchall()
    socialRestraint = result[0][0]
    pathPlanning = result[0][1]
    _closeMySQL(connection, cursor)

    jsnolFilePath = "../../Data/EmbeddingGeneration/queryAndEmbedding/query"+str(PublicConfig.simulateIdConfig)+".jsonl"
    jsonData = []
    with open(jsnolFilePath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                json_obj = json.loads(line)
                jsonData.append(json_obj)
            except json.JSONDecodeError as e:
                print(f"解析错误（行内容：{line}")

    saveCodePath = '../../Data/Coding/Example' + str(PublicConfig.simulateIdConfig) + ".py"
    genreToDbname = {"经济学": "../../Data/EmbeddingGeneration/EmbeddingData/economicalEmbedding.jsonl",
                     "历史学": "../../Data/EmbeddingGeneration/EmbeddingData/historyEmbedding.jsonl",
                     "法学": "../../Data/EmbeddingGeneration/EmbeddingData/jurisprudenceEmbedding.jsonl",
                     "政治学": "../../Data/EmbeddingGeneration/EmbeddingData/polilticsEmbedding.jsonl",
                     "心理学": "../../Data/EmbeddingGeneration/EmbeddingData/psychologyEmbedding.jsonl",
                     "社会学": "../../Data/EmbeddingGeneration/EmbeddingData/societyEmbedding.jsonl"}
    module_name = os.path.splitext(os.path.basename(saveCodePath))[0]
    spec = importlib.util.spec_from_file_location(module_name, saveCodePath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    for i in range(1, entityNum + 1):
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                tmpMemory = []
                entityPath = "../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/entity"+str(i)+".pkl"
                tmpEntity = load_instance(entityPath)
                if not tmpEntity.Actions:
                    for item in jsonData:
                        if item["entityIndex"] == "entity"+str(i):
                            res = RAGsearch(2,item["embedding"],genreToDbname[item["subject"]])
                            tmpMemory.extend(res)
                    momory = tmpMemory[random.randint(0, len(tmpMemory) - 1)]
                    while True:
                        alignmentAns = model.invoke(adjustTopicPrompt.format(topic = SocialSimulateContent,mainPath = pathPlanning,
                                                                       features = str(tmpEntity),restraint = socialRestraint,memory = momory))
                        inspectAns = evaluateOutput(adjustTopicPrompt.format(topic = SocialSimulateContent,mainPath = pathPlanning,
                                                                       features = str(tmpEntity),restraint = socialRestraint,memory = momory), alignmentAns.content)
                        if inspectAns == True:
                            break
                    alignmentAnsDict = json.loads(getFormatOutput(alignmentAns.content))
                    tmpEntity.Actions.append(alignmentAnsDict["updateMemory"])
                print(f"完成了第{i}个。\n")
                save_instance(tmpEntity,entityPath)
                break
            except Exception as e:
                retry_count += 1
                print(f"第{retry_count}次重试，错误信息: {e}")
                if retry_count >= max_retries:
                    print(f"达到最大重试次数{max_retries}，跳过此属性的调整。")
                    raise Exception(f"已达到最大重试次数 {max_retries}") from e


"""社会模拟器开始模拟"""
def startSimulation(SocialSimulateContent,cotIndex):
    socialSimulationStart(SocialSimulateContent)
    enviromentGeneration(SocialSimulateContent)
    codeGeneration(SocialSimulateContent)
    initializeMemory()
    Memorysupply(SocialSimulateContent)
    simulateProcess()
    simulationAnsAnalyse(SocialSimulateContent,cotIndex,True)