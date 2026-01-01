/*
 Navicat Premium Dump SQL

 Source Server         : Mysql
 Source Server Type    : MySQL
 Source Server Version : 50744 (5.7.44-log)
 Source Host           : localhost:3306
 Source Schema         : deepresearch

 Target Server Type    : MySQL
 Target Server Version : 50744 (5.7.44-log)
 File Encoding         : 65001

 Date: 02/01/2026 00:06:44
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for code_ans
-- ----------------------------
DROP TABLE IF EXISTS `code_ans`;
CREATE TABLE `code_ans`  (
  `id` int(11) NOT NULL,
  `codeContent` varchar(16000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `entityNum` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for cot_ans
-- ----------------------------
DROP TABLE IF EXISTS `cot_ans`;
CREATE TABLE `cot_ans`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cotList` varchar(12000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 320 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for env_restraint
-- ----------------------------
DROP TABLE IF EXISTS `env_restraint`;
CREATE TABLE `env_restraint`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `restraintContent` varchar(8200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `pathPlanning` varchar(4000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 103 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for genre
-- ----------------------------
DROP TABLE IF EXISTS `genre`;
CREATE TABLE `genre`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `writingStyle` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `styleContent` varchar(5000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `wordCount` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of genre
-- ----------------------------
INSERT INTO `genre` VALUES (1, '学术论文', '[\r\n    \"第一步：撰写标题。要求：精准概括研究核心内容，便于检索，避免模糊表述；标题需包含研究对象、核心变量和研究方法。例如：\'社交媒体使用对大学生社会支持感的影响 —— 基于 XX 高校的问卷调查\'。\",\r\n    \"第二步：撰写摘要和关键词。摘要：约200-300字，浓缩论文核心信息，包括研究目的、方法、结果和结论；社科领域需突出研究问题和理论/实践意义，避免冗余描述（例如，明确为何研究、用什么方法研究、发现了什么、有何价值）。关键词：提炼3-5个核心概念，便于数据库检索，涵盖研究对象和核心变量；例如：\'社交媒体使用；大学生；社会支持感；问卷调查\'。\",\r\n    \"第三步：撰写引言部分。内容：交代研究背景（结合现实背景，如大学生社交媒体日均使用时长超2小时）、提出研究问题、说明研究意义与创新点；社科领域需强调理论缺口（如现有研究未明确社交媒体使用与社会支持感的因果方向），并最终明确本研究要解决的具体问题。\",\r\n    \"第四步：撰写相关研究部分（文献综述）。要求：系统梳理现有研究，定位本研究的学术位置；社科领域需进行批判性综述，而非简单罗列，包括分类梳理相关理论（如社会支持理论、媒介依赖理论），指出已有研究的共识与不足（例如：多数研究发现社交媒体使用与社会支持感负相关，但未考虑使用内容的调节作用）。\",\r\n    \"第五步：撰写研究方法部分。要求：详细说明研究设计，确保研究可重复；需分研究点、分部分进行，每个部分要有小标题并与文章主题相关；具体内容包括研究对象（样本来源、抽样方法、样本量，例如：分层抽样选取XX高校300名大学生，有效样本276份）、实验设计流程等，详略结合地描述每个研究点。\",\r\n    \"第六步：撰写研究结果与分析部分。要求：客观呈现研究数据/资料，结合理论解读结果；社科领域需采用数据与理论双重视角：对于量化研究，用表格/图表呈现描述性统计、相关分析、回归分析结果（例如：社交媒体使用时长与社会支持感呈负相关，r=-0.32，p<0.01）；对于质性研究，引用访谈语录并提炼主题（例如：受访者A提到\'刷手机久了，和朋友见面都没话聊\'，反映社交媒体对现实互动的替代效应）。\",\r\n    \"第七步：撰写讨论部分。要求：深入解释结果的意义，与现有研究对话，并指出研究局限；社科领域需重点回答：结果是否支持预期（例如：本研究发现与Zhang等（2020）一致，验证了过度社交媒体使用削弱社会支持的假设）、结果的理论贡献（例如：首次引入使用内容变量，发现娱乐类使用的负向影响更强）、研究局限（例如：样本仅来自一所高校，代表性不足；横截面研究无法确定因果关系）。\",\r\n    \"第八步：撰写结论部分。要求：总结核心发现，提出实践建议或未来研究方向；确保结论简洁明了，呼应研究问题和目的。\"]\r\n', '[\r\n    \"20-30字\",\r\n    \"300-400字\",\r\n    \"1200-1500字\",\r\n    \"2500-3500字\",\r\n    \"1500-2000字\",\r\n    \"2500-3500字\",\r\n    \"2000-2500字\",\r\n\"500-800字\",\r\n\"11000-14000字\"\r\n]\r\n');
INSERT INTO `genre` VALUES (2, '研究报告', '[\r\n    \"撰写标题：明确体现\'研究对象+核心问题+报告类型\'，直观传递报告主题。例如：《XX市城乡老年人数字鸿沟现状调研报告（2024）》《XX社区适老化改造需求评估报告》\",\r\n    \"撰写执行摘要：浓缩报告核心信息（背景、核心发现、关键建议），采用\'结论先行\'原则，供决策者快速阅读。字数控制在报告总字数的5%-10%，先讲关键问题发现，再提具体建议。例如：\'调研发现农村老年人移动支付使用率仅18%，建议政府联合社区开展一对一数字培训\'\",\r\n    \"撰写研究背景与问题界定：说明研究必要性，结合政策背景、现实问题和研究目标。包括：政策背景（引用相关文件）、现实问题（具体数据支撑）、研究目标（明确要解决的具体问题）\",\r\n    \"撰写研究方法与过程：说明调研方法、范围、对象和数据来源，确保透明性。包括：调研范围（覆盖区域）、调研对象（具体特征）、数据来源（问卷、访谈、二手数据等）及样本量\",\r\n    \"撰写研究发现：客观呈现调研结果，按维度/群体分类呈现，采用\'问题导向+数据支撑\'方式。包括：分群体比较、分场景分析，结合定量数据和典型案例增强说服力\",\r\n    \"撰写问题成因分析：从多层面深入分析问题原因，为对策提供依据。包括：个体层面（生理、心理因素）、社会层面（家庭支持、产品设计）、政策层面（资源分配、服务覆盖）等分析维度\",\r\n    \"撰写对策建议：提出具体可落地的解决方案，按责任主体分类。每个建议包含：做什么+怎么做+预期效果，分别从政府层面、企业层面、社区层面等提出针对性措施\"]\r\n', '[\r\n    \"20-30字\",\r\n    \"1000-1200字\",\r\n    \"1500-1800字\",\r\n    \"1200-1500字\",\r\n    \"3000-3500字\",\r\n    \"2500-3000字\",\r\n    \"3000-3500字\",\r\n	\"12000-140000字\"\r\n]\r\n');
INSERT INTO `genre` VALUES (3, '政策简报', '\r\n[\r\n    \"撰写标题：直接点明\'核心问题+核心建议\'，包含问题领域和关键动作。例如：《关于补齐农村老年人数字助老服务缺口的建议》《强化社区适老化改造的紧迫性及对策》\",\r\n    \"撰写背景与问题：说明为何需关注此问题，结合政策依据、现实紧迫性和核心矛盾。包括：政策依据（引用相关文件）、现实数据（具体统计数据）、核心矛盾（突出问题的尖锐性）\",\r\n    \"提炼核心发现：呈现最关键的3-5个事实，用数据支撑问题严重性。每个发现仅用1句话，聚焦差异/缺口/风险，使用具体数据替代笼统描述。例如：\'农村社区数字助老志愿者人均服务120人，是城市的3倍，人力严重不足\'\",\r\n    \"提出政策建议：提供3-4条可落地的对策，明确责任主体+具体动作+时间节点。建议分主体、可操作、强约束，避免空话套话。例如：\'省民政厅牵头，2024年底前在每个行政村建立1个数字助老服务点\'\",\r\n    \"撰写风险提示与补充说明：预判政策实施中的潜在问题，或补充关键背景信息。包括：资金风险、实施难点、试点经验等。例如：\'若仅靠政府投入，可能存在资金缺口，建议引入企业公益合作；可参考XX县试点的成功经验\'\"]\r\n', '[\r\n    \"20-30字\",\r\n    \"2500-3500字\",\r\n    \"800-1200字\", \r\n    \"3000-3500字\",\r\n\"800-1500字\",\r\n\"8000-10000字\"\r\n]\r\n');
INSERT INTO `genre` VALUES (4, '文献综述', '[\r\n    \"设计精准的综述标题：标题应包含研究对象、核心变量和综述类型，例如《社交媒体使用对青少年心理健康影响的研究综述：基于中西方比较的视角》，确保标题既能准确概括内容又便于学术检索\",\r\n	\"撰写摘要与关键词：用200-300字浓缩综述的核心内容，包括研究目的、梳理框架、主要发现、研究缺口和未来方向；选取3-5个准确的关键词覆盖研究对象、核心变量和研究方法\",\r\n    \"撰写引言部分：开篇阐明研究背景与现实意义，清晰界定核心概念的操作化定义，详细说明文献筛选标准（包括数据库来源、检索策略、时间范围、纳入排除标准及最终文献数量），明确综述的研究目的与理论价值\",  \r\n    \"构建逻辑清晰的综述框架：根据研究主题选择最适合的梳理逻辑（主题式/理论式/方法式），建立层次分明的分类体系，为每个主要类别设置具有理论意义的小标题，确保框架的系统性和完整性\",    \r\n    \"系统梳理与对比分析文献：按照既定框架分类呈现代表性研究，不仅要总结各研究的主要发现，更要深入分析不同研究结论的共识与分歧，探讨分歧产生的深层原因（如样本差异、方法局限、文化背景等）\",   \r\n    \"绘制研究脉络与发展趋势：通过时间维度展示该领域研究热点的演变过程，识别关键转折点和理论突破，分析研究范式的变迁，预测未来可能的研究方向\",   \r\n    \"深入分析研究缺口：从理论建构（如理论解释力不足、文化适应性欠缺）、研究方法（如方法单一、测量工具局限）、样本代表性（如群体覆盖不全、地域分布不均）和研究视角（如维度单一、跨学科整合不足）四个层面系统识别研究空白\",    \r\n    \"提出具体可行的研究展望：针对每个研究缺口提出具有创新性的解决方案，包括理论拓展方向、方法改进策略、样本补充建议和视角融合思路，确保建议具有可操作性和前瞻性\",    \r\n    \"撰写精炼有力的结论：总结综述的核心发现，强调最重要的研究缺口，自然过渡到自身研究计划，清晰阐述后续研究如何填补现有空白及其预期贡献\"]\r\n', '[\r\n    \"20-30字\",\r\n    \"300-400字\",\r\n    \"2000-2500字\",\r\n    \"1500-2000字\",\r\n    \"4000-5000字\",\r\n    \"2000-2500字\",\r\n    \"2000-2500字\",\r\n    \"2000-2500字\",\r\n    \"800-1000字\" , \"15000-18000字\"\r\n]');


-- ----------------------------
-- Table structure for odd
-- ----------------------------
DROP TABLE IF EXISTS `odd`;
CREATE TABLE `odd`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topic` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `cotContent` varchar(3000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `overView` varchar(5200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `designConcept` varchar(6200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 103 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for odd2
-- ----------------------------
DROP TABLE IF EXISTS `odd2`;
CREATE TABLE `odd2`  (
  `id` int(11) NOT NULL,
  `detail` varchar(16300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for research_ans
-- ----------------------------
DROP TABLE IF EXISTS `research_ans`;
CREATE TABLE `research_ans`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topic` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `cotIndex` int(11) NULL DEFAULT NULL,
  `generationContent` varchar(12000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `cotContent` varchar(3000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `taskId` int(11) NULL DEFAULT NULL,
  `toolDetail` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 702 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for search_ans
-- ----------------------------
DROP TABLE IF EXISTS `search_ans`;
CREATE TABLE `search_ans`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topic` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `cotIndex` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `searchKey` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `searchContent` varchar(12000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `paperName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `taskId` int(11) NULL DEFAULT NULL,
  `author` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `publishYear` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `jounalName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 573 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for simulation_ans
-- ----------------------------
DROP TABLE IF EXISTS `simulation_ans`;
CREATE TABLE `simulation_ans`  (
  `id` int(11) NOT NULL,
  `simulationAnalyseContent` varchar(5000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `questionAndAnswer` varchar(8000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for user_demand
-- ----------------------------
DROP TABLE IF EXISTS `user_demand`;
CREATE TABLE `user_demand`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topic` varchar(2550) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `socialScienceType` varchar(2550) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `outputStyle` varchar(2550) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `researchTrend` varchar(2550) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 401 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
