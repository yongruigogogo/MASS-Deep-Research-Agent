import configparser
import json
import math
import random
import string

import chardet
import faiss
import numpy as np
import mysql.connector
from mysql.connector import Error

from Config.PublicConfig import PublicConfig
from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import evaluate_prompt1

model = ModelFactory("socialSimulate").GetModel()
# 格式化JSON字符串
def getFormatOutput(text):
    """
    提取字符串中所有完整的花括号{}内容，包括花括号本身
    参数:
        text (str): 输入字符串
    返回:
        list: 包含所有完整花括号内容的列表
    """
    ans = ''
    stack = []
    start_index = -1

    for i, char in enumerate(text):
        if char == '{':
            if not stack:  # 新的最外层花括号
                start_index = i
            stack.append(i)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:  # 闭合最外层花括号
                    end_index = i + 1
                    ans = text[start_index:end_index]

    return ans


# 检查输出内容是否正常
def evaluateOutput(question, answer):

    if answer.strip() == '':
        return False
    if getFormatOutput(answer) == '':
        return False
    return True
        # res = model.invoke(evaluate_prompt1.format(LlmAns=answer))
        # res_json = getFormatOutput(res.content)
        # if res_json == '':
        #     continue
        # res_dict = json.loads(res_json)
        # if not 'is_passed' in res_dict:
        #     continue
        # if str(res_dict['is_passed']) == 'True':
        #     return True
        # else:
        #     return False

import pickle
import os
#类实例持久化
def save_instance(instance, filename):
    try:
        with open(filename, 'wb') as file:
            pickle.dump(instance, file)
        print(f"实例已保存到 {filename}")
    except Exception as e:
        print(f"保存失败: {e}")

#持久化实例读取
def load_instance(filename):
    """从文件加载类实例"""
    if not os.path.exists(filename):
        print(f"文件 {filename} 不存在")
        return None
    try:
        with open(filename, 'rb') as file:
            instance = pickle.load(file)
        print(f"已从 {filename} 加载实例")
        return instance
    except Exception as e:
        print(f"加载失败: {e}")
        return None


#寻找两个集合中坐标近的entity
def findNearEntity(thisEntity,entityMap,num):
    nearEntity = {}
    randomKey = None
    for key,val in entityMap.items():
        if key == thisEntity.Id:
            continue
        if len(nearEntity) < num:
            nearEntity[key] = calDistance(thisEntity.Position,val)
        else:
            maxKey = max(nearEntity, key=nearEntity.get)
            maxVal = nearEntity[maxKey]
            if maxVal > calDistance(thisEntity.Position,val):
                del nearEntity[maxKey]
                nearEntity[key] = calDistance(thisEntity.Position,val)
    if nearEntity:
        nearEntityKeys = list(nearEntity.keys())
        randomKey = random.choice(nearEntityKeys)
    return randomKey
#计算两个坐标
def calDistance(pos1,pos2):
    if len(pos1) < 2 or len(pos2)<2:
        return float('inf')
    return math.sqrt(pow(abs(pos1[0]-pos2[0]),2)+pow(abs(pos1[1]-pos2[1]),2))

#连接数据库与释放数据库
def _connectMySQL():
    try:
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        config_path = os.path.join(current_dir, "../Config/config.ini")
        config_path = os.path.normpath(config_path)
        config = configparser.ConfigParser()
        config.read(config_path,encoding="utf-8")
        t = config.get("mySql", "host")
        connection = mysql.connector.connect(
            host = config.get("mySql", "host"),
            database = config.get("mySql", "database"),
            user = config.get("mySql", "username"),
            passwd = config.get("mySql", "password"),
        )
        if connection.is_connected():
            cursor = connection.cursor()
            return connection,cursor
    except Error as e:
        print(f"MySQL连接错误：{e}")

def _closeMySQL(connection,cursor):
    if connection.is_connected():
        cursor.close()
        connection.close()


def save_texts_to_jsonl(texts, file_path):
    """
    将长文本列表保存为JSON Lines格式

    参数:
        texts: 文本列表，例如 ["文本1...", "文本2...", ...]
        file_path: 保存路径，例如 "data.jsonl"
    """
    with open(file_path, 'a', encoding='utf-8') as f:
        for text in texts:
            # 每条文本用一个JSON对象存储，字段名为"content"
            json.dump({"content": text}, f, ensure_ascii=False)
            f.write('\n')  # 每行一条JSON

def append_text_to_jsonl(text, file_path):
    """
    逐条追加文本到JSON Lines文件（每次写入一条）

    参数:
        text: 单条文本内容（字符串）
        file_path: 目标文件路径（如"texts.jsonl"）
    """
    # 使用追加模式（'a'）打开文件，每次写入不会覆盖已有内容
    with open(file_path, 'a', encoding='utf-8') as f:
        # 写入单条JSON对象（包含文本字段）
        json.dump({"content": text}, f, ensure_ascii=False)
        f.write('\n')  # 每条数据占一行

def load_texts_from_jsonl(file_path):
    """从JSON Lines文件读取所有文本（逐行解析）"""
    texts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            texts.append(data["content"])
    return texts

#获取配置文件的内容
def getConfigFile():
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    config_path = os.path.join(current_dir, "../Config/config.ini")
    config_path = os.path.normpath(config_path)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    return config

# 归一化向量（余弦相似度需要）
def normalize_vectors(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1e-12)

#在chroma里面进行检索
def RAGsearch(num,searchEmbedding,dataUrl):
    texts = []
    rawTexts = []
    Ans = []
    dataUrl = dataUrl
    with open(dataUrl, 'r', encoding='utf-8') as f:
        print("开始加载数据集")
        for line_num, line in enumerate(f, 1):
            try:
                # 解析json数据
                json_data = json.loads(line.strip())
                emb = np.array(json_data['embedding'], dtype=np.float32)
                texts.append(emb)
                rawTexts.append(json_data['oldText'])
            except json.JSONDecodeError as e:
                # 捕获解析错误，方便定位问题行
                print(f"解析JSONL文件时出错，行号：{line_num}，错误信息：{e}")
    print("加载数据集结束")
    doc_embeddings = np.array(texts, dtype=np.float32)  # 形状：(num_docs, embedding_dim)
    doc_embeddings = normalize_vectors(doc_embeddings)  # 归一化文档向量
    embedding_dim = doc_embeddings.shape[1]
    index = faiss.IndexFlatIP(embedding_dim)
    # 添加文档向量到索引
    index.add(doc_embeddings)
    query = searchEmbedding
    query = np.array(query, dtype=np.float32)
    query = query.reshape(1, -1)

    scores, indices = index.search(query, k=num)
    indicesList = indices.tolist()[0]
    for indece in indicesList:
        Ans.append(rawTexts[indece])
    return Ans

#调用服务器去进行embedding
def getEmbedding(content):
    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "3"
        #改成你的embedding模型地址
        model = SentenceTransformer('/data/models/M3E-Large')
        embeddings = model.encode(content)
        return embeddings[0].tolist(),True
    except Exception as e:
        print(f"Embedding失败:{e}")
        return "", False

#拿到遗忘概率
def getForgetProbability(score):
    score_mappings = [
        (71 , 100 , 0 ,0),
        (65, 70, 0, 3),  # 65-70分 对应 0-3 的平均值
        (60, 64, 3, 8),  # 60-64分 对应 3-8 的平均值
        (55, 59, 8, 15),  # 55-59分 对应 8-15 的平均值
        (50, 54, 15, 20),  # 50-54分 对应 15-20 的平均值
        (45, 49, 20, 28),  # 45-49分 对应 20-28 的平均值
        (35, 44, 28, 40),  # 35-44分 对应 28-40 的平均值
        (30, 34, 40, 55),  # 30-34分 对应 40-55 的平均值
        (0, 29, 55, 80)  # 10-29分 对应 55-80 的平均值
    ]
    for score_low, score_high, val_low, val_high in score_mappings:
        if score_low <= score <= score_high:
            # 计算对应数值区间的平均值并返回
            return (val_low + val_high) / 2
    return 0
