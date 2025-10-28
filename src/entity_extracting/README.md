## **知识图谱构建：实体 Schema 定义文档**

本文档定义了用于从文本中抽取“知识图谱”领域知识的四种核心实体类型及其属性。

### **1\. 实体：概念 (Concept)**

**核心定义：**

概念 是知识图谱领域中的**抽象思想、理论、模型、任务或方法**。它回答的是“是什么”（What）的问题。

* **示例：** “知识表示学习”（理论）、“TransE”（模型）、“链接预测”（任务）。

#### **属性详情**

| 属性 (Property) | 类型 (Type) | 描述 (Description) | 示例 (Example) |
| :---- | :---- | :---- | :---- |
| name | String | 概念的唯一名称或标识符。 | "TransE", "知识抽取" |
| definition | String | 从文本中提取的该概念的简明定义。 | "一个基于平移的知识表示学习模型。" |
| aliases | List\[String\] | 该概念的其他称谓或缩写。 | \["KE", "知识获取"\] |
| category | Enum (String) | 概念的类型。**（核心区分属性）** | Task (任务), Model (模型), Theory (理论), Method (方法), Data Structure (数据结构), Metric (评估指标) |
| sub\_domain | String | 该概念所属的细分研究领域。 | "知识表示学习", "知识抽取" |
| purpose | String | 该概念被提出或用于解决什么问题。 | "用于链接预测和知识图谱补全。" |

---

### **2\. 实体：技术 (Technology)**

**核心定义：**

技术 是用于实现、构建或应用知识图谱的**具体工具、框架、平台、语言或标准**。它回答的是“怎么做”（How）的问题。

* **示例：** “Neo4j”（图数据库）、“SPARQL”（查询语言）、“OpenIE”（工具）。

#### **属性详情**

| 属性 (Property) | 类型 (Type) | 描述 (Description) | 示例 (Example) |
| :---- | :---- | :---- | :---- |
| name | String | 技术的官方或通用名称。 | "Neo4j", "OpenIE", "Jena" |
| category | Enum (String) | 技术的具体类别。**（核心区分属性）** | Graph Database, Framework / Library, System / Tool, Query Language, Specification / Standard |
| purpose | String | 该技术被创造出来的主要目的和功能。 | "一个高性能的原生图数据库，用于存储和查询图数据。" |
| vendor\_or\_originator | String | 开发、维护或发布该技术的组织。 | "Neo4j Technology", "W3C", "University of Washington" |
| key\_features | List\[String\] | (可选) 该技术区别于其他的关键特性。 | \["原生图存储", "Cypher 查询语言"\] |

---

### **3\. 实体：文档 (Document)**

**核心定义：**

文档 是承载知识图谱相关知识的**信息来源**，包括学术论文、技术报告、博客或官方手册。它是知识的“证据” (Source of Truth)。

* **示例：** "Translating Embeddings for..."（论文）、"Neo4j Cypher Manual"（官方文档）。

#### **属性详情**

| 属性 (Property) | 类型 (Type) | 描述 (Description) | 示例 (Example) |
| :---- | :---- | :---- | :---- |
| title | String | 文档的完整、官方标题。 | "Translating Embeddings for Modeling Multi-relational Data" |
| category | Enum (String) | 文档的类别。**（核心区分属性）** | Research Paper, Technical Report, Technical Blog, Official Documentation, Book / Chapter |
| authors | List\[String\] | 编写该文档的一个或多个作者或组织。 | \["Bordes, Antoine", ...\], "Neo4j Team" |
| publication\_year | Integer | 文档公开发表的年份。 | 2013 |
| source\_name | String | 发布文档的平台或出版物（如期刊、会议、博客名）。 | "NIPS", "Medium", "W3C" |
| url\_or\_doi | String | 指向该文档的唯一 URL 或 DOI。 | "10.1109/NIPS.2013.12345" |
| abstract\_or\_summary | String | 论文的摘要，或博客/文档的简介。 | "本文提出了一种新的知识表示模型 TransE..." |

---

### **4\. 实体：应用 (Application)**

**核心定义：**

应用 是利用知识图谱技术解决特定领域问题的**具体实例、产品、项目或系统**。它回答的是“用来做什么”（For What）的问题。

* **示例：** “Siri”（产品）、“Amazon 推荐算法”（系统）、“Google Knowledge Panel”（功能）。

#### **属性详情**

| 属性 (Property) | 类型 (Type) | 描述 (Description) | 示例 (Example) |
| :---- | :---- | :---- | :---- |
| name | String | 该具体应用系统、产品或项目的专有名称。 | "Siri", "Google Knowledge Panel" |
| **task\_category** | **String** | **(横向领域)** 指明该应用所属的功能分类。 | **"问答系统"**, **"推荐系统"**, "语义搜索" |
| organization | String | 开发、部署或运营该应用的具体组织。 | "Apple", "Google", "Amazon" |
| domain | String | **(垂直领域)** 该应用主要服务的垂直行业。 | "消费电子", "搜索引擎", "电商" |
| purpose\_summary | String | 该**具体应用**为用户提供的核心价值。 | "为 Apple 设备用户提供语音交互以完成任务和回答问题。" |
| key\_kg\_function | String | 知识图谱在该应用中扮演的关键角色。 | "提供背景知识库以理解用户意图并检索答案。" |

