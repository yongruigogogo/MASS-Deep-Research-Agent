import json
from enum import Enum

from Factory.LLMFactory import ModelFactory
from Utils.PromptHelper import deepResearchPlannerEvaluate1
from Utils.Tools import evaluateOutput, getFormatOutput


##评分智能体

class evaluateItem(Enum):
    Item1 = "本次推理思考中思维的发散性如何呢，与之前的推理思考过程比较，本次推理思考过程所提出的研究观点是否效整合多学科视角和理论框架，研究拓展性和多样性是否能得到保证。"
    Item2 = "发散思维思考出的研究内容是否与主题相关联，是否有偏离主题的趋势。"
    Item3 = "研究设计的严谨性，研究方法是否适合问题，设计是否科学合理如何。"
    Item4 = "研究的社会意义，评估研究问题的社会价值和应用潜力，这部分研究内容是不是基于问题重要性、政策相关性和社会影响范围的评分。"
    Item5 = "Agent产生的思维链是否连贯，思维链是否能够识别并分析因果关系，而非仅描述相关性，这关系到后面的文章行文是否连贯。"
    Item6 = "研究的创新性，你要思考并评估本次待评估的推理思考内容弄是否有创新性，是否是相对于其他的研究有创新性的发展。"
    Item7 = "与使用者的写作意愿与研究倾向是否契合。"

#给树形COT的每一个节点进行评分
def evaluateCOT(demandAns,thinkingProcess,nowThinking):
    ansDict = {}
    try:
        evaluateItemList = list(evaluateItem)
        item = 0
        model = ModelFactory("deepResearch").GetModel()
        evaluatePrompt = deepResearchPlannerEvaluate1.format(topic = demandAns.topic,genre = demandAns.outputStyle,researchTrend = demandAns.researchTrend,socialScienceType = str(demandAns.socialScienceType),
                                                                           thinkingProcess = str(thinkingProcess),nowThinking = str(nowThinking))
        while True:
            evaluateAns = model.invoke(evaluatePrompt)
            inspectAns = evaluateOutput(evaluatePrompt, evaluateAns.content)
            if inspectAns == True:
                break
        evaluteDict = json.loads(getFormatOutput(evaluateAns.content))
        for score in evaluteDict["evaluateAns"]:
            ansDict[evaluateItemList[item]] = score
            item += 1
        return ansDict
    except Exception as e:
        print(e)
        print("\n JSON格式解析出问题")
        return ansDict