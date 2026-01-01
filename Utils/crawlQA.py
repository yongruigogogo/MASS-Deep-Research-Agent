import os
import time
from io import BytesIO

import requests
import json
from bs4 import BeautifulSoup
from Utils.Tools import _connectMySQL, _closeMySQL


#百度搜索API
def baiduSearch(query,search_source="baidu_search_v2",
               resource_type_filter=[{"type": "web", "top_k": 10}],
               search_filter=None, search_recency_filter="year"):
    base_url = "https://qianfan.baidubce.com/v2/ai_search/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY_BAIDU')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {
                "content": query,
                "role": "user"
            }
        ],
        "search_source": search_source,
        "resource_type_filter": resource_type_filter,
        "search_recency_filter": search_recency_filter
    }
    if search_filter:
        payload["search_filter"] = search_filter

    try:
        # 发送POST请求
        response = requests.post(
            base_url,
            headers=headers,
            data=json.dumps(payload)
        )

        # 检查响应状态码
        response.raise_for_status()

        # 解析JSON格式的响应内容
        resp = response.json()
        respDict = resp['references']
        searchContent = {}
        for ref in respDict:
            searchContent[ref["title"]] = ref["content"]
        return searchContent

    except requests.exceptions.RequestException as e:
        print(f"API请求出错: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        return None

#进行社科文献的检索
# 用OpenAlex API进行检索
def getPaperByOpenAlex(searchKey):
    url = "https://api.openalex.org/works"
    params = {
        "search": f"\"{searchKey}\"",  # 检索关键词：深度学习 2023年
        "per-page": 2,  # 只取前2条结果
        "sort": "relevance_score:desc,publication_date:desc"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = []
        for i, paper in enumerate(data["results"], 1):
            # 提取核心信息
            title = paper.get("title", "无标题")
            authors = [auth["author"]["display_name"] for auth in paper.get("authorships", [])]
            journal = paper.get("host_venue", {}).get("display_name", "无期刊信息")
            pub_date = paper.get("publication_date", "无发表时间")  # 发表时间
            # 1. 提取论文摘要（核心内容片段）
            abstract_index = paper.get("abstract_inverted_index", {})  # 倒排索引格式
            if abstract_index:
                # 按索引位置排序，还原正常摘要文本
                sorted_words = sorted(abstract_index.items(), key=lambda x: min(x[1]))
                abstract = " ".join([word for word, positions in sorted_words])
            else:
                continue
            results.append({
                "title": str(title),
                "author": str(", ".join(authors)),
                "abstract": str(abstract),
                "journal": str(journal),
                "fullText": "",
                "publishTime": str(pub_date)
            })
        print("检索完成")
        return results
    except Exception as e:
        print(e)
        return []
##用coreapi进行全文查询
def get_dois_by_keyword(keyword: str, limit: int = 2) -> list:
    url = "https://api.core.ac.uk/v3/search/works"  # CORE搜索端点
    params = {
        "q": keyword,  # 关键词搜索
        "apiKey": os.getenv('API_KEY_CORE'),  # 标准认证方式：作为参数传递
        "limit": limit,
        "fields": "title,fullText,authors,publishedDate,journal",
        "sorts":"_score:desc,publishedDate:desc"
    }
    searchAns = []
    time.sleep(1)
    try:
        time.sleep(1)  # 控制请求频率，避免限流
        response = requests.get(url, params=params)
        response.raise_for_status()  # 检查请求是否成功

        results = response.json().get("results", [])
        for result in results:
            searchAns.append({
                "title": str(result["title"]),
                "author": str(result["authors"]),
                "abstract": str(result["abstract"]),
                "fullText": str(result["fullText"]),
                "publishTime": str(result["updatedDate"]),
                "journal": str(result["journals"])
            })
        print("检索完成")
        return searchAns

    except Exception as e:
        print(f"关键词搜索失败: {e}")
        return []

if __name__ == "__main__":
    pass