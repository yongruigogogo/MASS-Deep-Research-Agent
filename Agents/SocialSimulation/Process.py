import ast
import configparser
import importlib
import json
import math
import os.path
import random
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from typing import List, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import controlSystemInstruction, socialEntityIntroduction, socialEntityPrompt1, \
    controlSystemPrompt1, communicatePrompt1, socialEntityPrompt2, scoringPrompt1, scoringPrompt2, socialEntityPrompt3, \
    memoryActivationPrompt
from Utils.Tools import load_instance, evaluateOutput, getFormatOutput, findNearEntity, save_instance, _connectMySQL, \
    _closeMySQL, getForgetProbability

"""
模拟器模拟过程
每次模拟，改一下round和entity_finish
一定要注意每一个量化的值到底改没改
"""

stop_all_threads = False
stop_lock = threading.Lock()

def simulateProcess():
    global stop_all_threads
    model = ModelFactory("socialSimulate").GetModel()
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

    connection, cursor = _connectMySQL()
    findNumSql = f"SELECT entityNum FROM `code_ans` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(findNumSql)
    entityNum = cursor.fetchall()[0][0]
    _closeMySQL(connection, cursor)

    connection, cursor = _connectMySQL()
    restraintSql = f"SELECT restraintContent,pathPlanning FROM `env_restraint` WHERE id = \'{PublicConfig.simulateIdConfig}\'"
    cursor.execute(restraintSql)
    envContent = cursor.fetchall()
    envRestraint = envContent[0][0]
    pathPlanningList = ast.literal_eval(envContent[0][1])
    _closeMySQL(connection, cursor)

    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    config_path = os.path.join(current_dir, "../../Config/config.ini")
    config_path = os.path.normpath(config_path)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')

    entity_nums = range(1,entityNum+1)
    entity_finish = []
    round = 1
    tmp_entity_nums = [x for x in entity_nums if x not in entity_finish]
    #分若干个线程来做,先分块
    threadCound = int(config.get("simulateConfig","simulationThreadNum"))
    total = len(tmp_entity_nums)
    parts = []
    if total == 0:
        parts = [range(0) for _ in range(threadCound)]
    else:
        base = total // threadCound
        remainder = total % threadCound
        start = 0

        for i in range(threadCound):
            length = base + 1 if i < remainder else base
            end = start + length
            parts.append(tmp_entity_nums[start:end])
            start = end

    entityMap = {}
    saveCodePath = '../../Data/Coding/Example' + str(PublicConfig.simulateIdConfig) + ".py"
    module_name = os.path.splitext(os.path.basename(saveCodePath))[0]
    spec = importlib.util.spec_from_file_location(module_name, saveCodePath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    for i in entity_nums:
        tmpEntity= load_instance("../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/entity"+str(i)+".pkl")
        entityMap["entity"+str(i)] = tmpEntity.Position
    while True:
        with stop_lock:
            if stop_all_threads:
                print("检测到有线程达到最大重试次数，程序中止运行")
                return
        if round >= len(pathPlanningList)*int(config.get("simulateConfig","simulationFreqPerRound")):
            break
        threadList = []
        for i in range(1,threadCound+1):
            Tmpthread = threading.Thread(target=startProcess, name="Thread-"+str(i),args = (parts[i-1],overview_content,design_content,detail_content,pathPlanningList,round,model,envRestraint,entityMap,entityNum,int(config.get("simulateConfig","simulationFreqPerRound"))))
            threadList.append(Tmpthread)
        for thread in threadList:
            thread.start()
        for thread in threadList:
            thread.join()
        # 再次检查是否应该停止
        with stop_lock:
            if stop_all_threads:
                print("检测到有线程达到最大重试次数，程序中止运行")
                return
        print(f"第 {round} 轮所有线程执行完毕，准备进入下一轮...\n")
        with open(r"../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/record"+str(PublicConfig.simulateIdConfig)+".txt", 'a', encoding='utf-8') as f:
            f.write(f"\n 第{round}轮执行完毕。\n")
        round += 1
        entity_finish.clear()
        tmp_entity_nums = [x for x in entity_nums if x not in entity_finish]
        total = len(tmp_entity_nums)
        parts = []
        if total == 0:
            parts = [range(0) for _ in range(threadCound)]
        else:
            base = total // threadCound
            remainder = total % threadCound
            start = 0

            for i in range(threadCound):
                length = base + 1 if i < remainder else base
                end = start + length
                parts.append(tmp_entity_nums[start:end])
                start = end

def startProcess(tmp_entity_nums,overview_content,design_content,detail_content,pathPlanningList,round,model,envRestraint,entityMap,entityNum,freqPerRound):
    global stop_all_threads
    i = 0
    while i < len(tmp_entity_nums):
        # 检查是否应该停止
        with stop_lock:
            if stop_all_threads:
                print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                return
        item = tmp_entity_nums[i]
        max_retries = 10
        retry_count = 0
        success = False
        while retry_count < max_retries and not success:
            # 检查是否应该停止
            with stop_lock:
                if stop_all_threads:
                    print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                    return
            try:
                thisEntity = load_instance("../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/entity"+str(item)+".pkl")
                # 社会环境上下文
                ChatHistoryEnv: List[Any] = []
                ChatHistoryEnv.append(
                    SystemMessage(controlSystemInstruction.format(overview = overview_content,design = design_content,details = detail_content)))
                # 社会实体上下文
                ChatHistoryAgent: List[Any] = []
                ChatHistoryAgent.append(
                    SystemMessage(socialEntityIntroduction.format(overview=overview_content, design=design_content,
                                                                  details=detail_content, feature=str(thisEntity),pathPlanning = str(pathPlanningList))))
                # 艾宾浩斯遗忘
                historyActions = thisEntity.Actions.copy()
                remaining = []
                if len(thisEntity.Actions) > 9:
                    for actionIndex in range(0, len(thisEntity.Actions)-1):
                        forgetodds = getForgetProbability(
                            #获取分数
                            90 * math.exp(-4.8 * ((len(thisEntity.Actions) - actionIndex) / (len(thisEntity.Actions) + 1))) + 20)/100
                        #记忆激活
                        while True:
                            # 检查是否应该停止
                            with stop_lock:
                                if stop_all_threads:
                                    print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                                    return
                            activateAns = model.invoke(memoryActivationPrompt.format(content1=historyActions[actionIndex],content2 = historyActions[-1]))
                            inspectAns = evaluateOutput(memoryActivationPrompt.format(content1=historyActions[actionIndex],content2 = historyActions[-1]), activateAns.content)
                            if inspectAns == True:
                                break
                        activateDict = json.loads(getFormatOutput(activateAns.content))
                        forgetodds += int(activateDict["score"])
                        if random.random() > forgetodds:
                            remaining.append(historyActions[actionIndex])
                    remaining.append(historyActions[-1])
                ChatHistoryAgent.append(HumanMessage(socialEntityPrompt1.format(actions = str(remaining),pathNode = str(pathPlanningList[round//freqPerRound]))))
                while True:
                    # 检查是否应该停止
                    with stop_lock:
                        if stop_all_threads:
                            print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                            return
                    modelAns = model.invoke(ChatHistoryAgent)
                    inspectAns = evaluateOutput(ChatHistoryAgent[-1], modelAns.content)
                    if inspectAns == True:
                        break
                modelDict = json.loads(getFormatOutput(modelAns.content))
                ChatHistoryAgent.append(AIMessage(modelAns.content))

                ChatHistoryEnv.append(
                    HumanMessage(controlSystemPrompt1.format(features=str(thisEntity), action=modelDict["action_content"],envRestraint = str(envRestraint))))
                while True:
                    with stop_lock:
                        if stop_all_threads:
                            print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                            return
                    evaluateAns = model.invoke(ChatHistoryEnv)
                    inspectAns = evaluateOutput(ChatHistoryEnv[-1], evaluateAns.content)
                    if inspectAns == True:
                        break
                ChatHistoryEnv.append(AIMessage(evaluateAns.content))
                evaluateDict = json.loads(getFormatOutput(evaluateAns.content))
                while True:
                    with stop_lock:
                        if stop_all_threads:
                            print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                            return
                    if str(evaluateDict['is_passed']) == 'True':
                        thisEntity.Actions.append(modelDict["action_content"])
                        if str(modelDict['is_socialize']) == 'True':
                            commuEntityId = findNearEntity(thisEntity,entityMap,math.ceil(entityNum*0.2))
                            commuEntity = load_instance("../../Data/persistence/example" + str(PublicConfig.simulateIdConfig) + "/" + str(commuEntityId) + ".pkl")
                            while True:
                                with stop_lock:
                                    if stop_all_threads:
                                        print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                                        return
                                contactAns = model.invoke(
                                    communicatePrompt1.format(overview = overview_content,design = design_content,details = detail_content,
                                                              my_feature = str(thisEntity),entity_feature = str(str(commuEntity)),communicate_content = modelDict["socialize_content"]))
                                inspectAns = evaluateOutput(communicatePrompt1.format(overview = overview_content,design = design_content,details = detail_content,
                                                              my_feature = str(thisEntity),entity_feature = str(str(commuEntity)),communicate_content = modelDict["socialize_content"]),contactAns.content)

                                if inspectAns == True:
                                    break
                            contactAnsDict = json.loads(getFormatOutput(contactAns.content))
                            if str(contactAnsDict['is_accept']) == "True":
                                contact_action_ans = "与" + commuEntityId + "交互成功。" + str(
                                    contactAnsDict['communicate_out'])
                            else:
                                contact_action_ans = "与" + commuEntityId + "交互失败。" + str(
                                    contactAnsDict['communicate_out'])
                            thisEntity.Actions.append(contact_action_ans)
                        else:
                            contact_action_ans = "暂未进行社交行为。"
                            thisEntity.Actions.append(f"{str(thisEntity.Id)}本次行动后暂未进行社交行为。")
                        break
                    else:
                        ChatHistoryAgent.append(SystemMessage(socialEntityPrompt2.format(suggestions=str(evaluateDict['suggestion']))))
                        while True:
                            with stop_lock:
                                if stop_all_threads:
                                    print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                                    return
                            modelAns = model.invoke(ChatHistoryAgent)
                            inspectAns = evaluateOutput(ChatHistoryAgent[-1], modelAns.content)
                            if inspectAns == True:
                                break
                        ChatHistoryAgent.append(AIMessage(modelAns.content))
                        modelDict = json.loads(getFormatOutput(modelAns.content))
                        evaluateDict["is_passed"] = True
                ChatHistoryEnv.append(HumanMessage(scoringPrompt2.format(features = str(thisEntity),action = modelDict['action_content'],associate = contact_action_ans)))
                while True:
                    # 检查是否应该停止
                    with stop_lock:
                        if stop_all_threads:
                            print(f"线程 {threading.current_thread().name} 检测到停止信号，提前终止")
                            return
                    actionOut = model.invoke(ChatHistoryEnv)
                    inspect_Ans = evaluateOutput(ChatHistoryEnv[-1], actionOut.content)
                    if inspect_Ans == True:
                        break
                ChatHistoryEnv.append(AIMessage(actionOut.content))
                actionOutDict = json.loads(getFormatOutput(actionOut.content))
                for propertyName, propertyValue in actionOutDict["changeFeatures"].items():
                    if isinstance(propertyValue, list) and len(propertyValue) > 0:
                        propertyValue = propertyValue[0]
                    if hasattr(thisEntity,str(propertyName)):
                        currentPropertyValue = getattr(thisEntity,str(propertyName))
                        if isinstance(currentPropertyValue,list):
                            currentPropertyValue.append(propertyValue)
                save_instance(thisEntity,"../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/entity"+str(item)+".pkl")
                with open(r"../../Data/persistence/example"+str(PublicConfig.simulateIdConfig)+"/record"+str(PublicConfig.simulateIdConfig)+".txt", 'a', encoding='utf-8') as f:
                    f.write(f"{item},")
                success = True
                time.sleep(10)
            except Exception as e:
                retry_count += 1
                print(f"处理实体 {item} 第 {retry_count} 次尝试失败:")
                print(f"异常类型: {type(e).__name__}")
                print(f"异常信息: {str(e)}")
                print("堆栈跟踪:")
                traceback.print_exc()
                print("-" * 50)

                if retry_count < max_retries:
                    print(f"等待60秒后重试...")
                    time.sleep(20)
        if success:
            i += 1
        else:
            print(f"实体 {item} 重试 {max_retries} 次后仍失败，跳过处理")
            with stop_lock:
                stop_all_threads = True
            return  # 直接返回，停止当前线程
