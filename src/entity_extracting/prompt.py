# prompt.py
"""
此文件存储用于知识图谱实体抽取的专用 Prompt 模板。
"""

CONCEPT_EXTRACTION_TEMPLATE = """# 任务：知识图谱 "概念" 实体抽取

你是一个精准的实体抽取助手。你的唯一任务是从给定的 "content" 文本中，抽取出所有与 "知识图谱" 相关的 "概念" (Concept) 实体。

## "概念" (Concept) 的定义
"概念" 是知识图谱领域中的抽象思想、理论、模型、任务或方法。
例如："知识表示学习"、"TransE"、"链接预测"、"本体"。

## "概念" 的属性 Schema (完整版)
你必须按照以下 JSON 结构抽取所有属性：
1.  `name` (string): 概念的唯一名称。
2.  `definition` (string): 文本中对该概念的简明定义 (如果没有明确定义，留空字符串 "")。
3.  `aliases` (list[string]): 该概念的其他称谓或缩写 (如果未提及，返回空列表 `[]`)。
4.  `category` (string): 概念的类型。必须是以下之一：
    - "Task" (任务)
    - "Model" (模型)
    - "Theory" (理论)
    - "Method" (方法)
    - "Data Structure" (数据结构)
    - "Metric" (评估指标)
    - (如果无法分类，留空字符串 "")
5.  `sub_domain` (string): 该概念所属的细分领域 (例如: "知识表示学习", "知识抽取")。
6.  `purpose` (string): 该概念被提出或用于解决什么问题 (如果未提及，留空字符串 "")。

## 输入文本 (Input)
{content}

## 输出格式 (Output)
你必须严格返回一个 JSON 列表。如果找不到任何 "概念" 实体，必须返回一个空列表 `[]`。

[
  {{
    "name": "...",
    "definition": "...",
    "aliases": ["...", "..."],
    "category": "...",
    "sub_domain": "...",
    "purpose": "..."
  }},
  ...
]

## 开始抽取：
"""


TECHNOLOGY_EXTRACTION_TEMPLATE = """# 任务：知识图谱 "技术" 实体抽取

你是一个精准的实体抽取助手。你的唯一任务是从给定的 "content" 文本中，抽取出所有与 "知识图谱" 相关的 "技术" (Technology) 实体。

## "技术" (Technology) 的定义
"技术" 是用于实现、构建或应用知识图谱的具体工具、框架、平台、语言或标准。
例如："Neo4j"、"SPARQL"、"OpenIE"、"Jena"。

## "技术" 的属性 Schema (完整版)
你必须按照以下 JSON 结构抽取所有属性：
1.  `name` (string): 技术的官方名称。
2.  `category` (string): 技术的类别。必须是以下之一：
    - "Graph Database" (图数据库)
    - "Framework / Library" (框架/库)
    - "System / Tool" (系统/工具)
    - "Query Language" (查询语言)
    - "Specification / Standard" (规范/标准)
    - (如果无法分类，留空字符串 "")
3.  `purpose` (string): 该技术的主要功能或目的 (如果没有明确说明，留空字符串 "")。
4.  `vendor_or_originator` (string): 开发或发布该技术的组织 (如果没有提及，留空字符串 "")。
5.  `key_features` (list[string]): 该技术的关键特性 (如果未提及，返回空列表 `[]`)。

## 输入文本 (Input)
{content}

## 输出格式 (Output)
你必须严格返回一个 JSON 列表。如果找不到任何 "技术" 实体，必须返回一个空列表 `[]`。

[
  {{
    "name": "...",
    "category": "...",
    "purpose": "...",
    "vendor_or_originator": "...",
    "key_features": ["...", "..."]
  }},
  ...
]

## 开始抽取：
"""


DOCUMENT_EXTRACTION_TEMPLATE = """# 任务：知识图谱 "文档" 实体抽取

你是一个精准的实体抽取助手。你的唯一任务是从给定的 "content" 文本中，抽取出所有被提及的 "文档" (Document) 实体。

## "文档" (Document) 的定义
"文档" 是承载知识图谱知识的信息来源，如学术论文、技术博客或官方手册。
例如："Translating Embeddings for Modeling..."、"Neo4j Cypher Manual"。

## "文档" 的属性 Schema (完整版)
你必须按照以下 JSON 结构抽取所有属性：
1.  `title` (string): 文档的完整标题。
2.  `category` (string): 文档的类别。必须是以下之一：
    - "Research Paper" (研究论文)
    - "Technical Report" (技术报告)
    - "Technical Blog" (技术博客)
    - "Official Documentation" (官方文档)
    - "Book / Chapter" (书籍/章节)
    - (如果无法分类，留空字符串 "")
3.  `authors` (list[string]): 文档的作者或组织 (如果未提及，返回空列表 `[]`)。
4.  `publication_year` (int or null): 发表年份 (如果未提及，返回 `null`)。
5.  `source_name` (string): 来源名称 (如期刊、会议、博客名) (如果未提及，留空字符串 "")。
6.  `url_or_doi` (string): 指向该文档的唯一 URL 或 DOI (如果未提及，留空字符串 "")。
7.  `abstract_or_summary` (string): 文档的摘要或简介 (如果未提及，留空字符串 "")。

## 输入文本 (Input)
{content}

## 输出格式 (Output)
你必须严格返回一个 JSON 列表。如果找不到任何 "文档" 实体，必须返回一个空列表 `[]`。

[
  {{
    "title": "...",
    "category": "...",
    "authors": ["...", "..."],
    "publication_year": ...,
    "source_name": "...",
    "url_or_doi": "...",
    "abstract_or_summary": "..."
  }},
  ...
]

## 开始抽取：
"""


APPLICATION_EXTRACTION_TEMPLATE = """# 任务：知识图谱 "应用" 实体抽取

你是一个精准的实体抽取助手。你的唯一任务是从给定的 "content" 文本中，抽取出所有与 "知识图谱" 相关的 "应用" (Application) 实体。

## "应用" (Application) 的定义
"应用" 是利用知识图谱技术解决问题的具体实例、产品、项目或系统。
例如："Siri"、"Amazon 推荐算法"、"Google Knowledge Panel"。

## "应用" 的属性 Schema (完整版)
你必须按照以下 JSON 结构抽取所有属性：
1.  `name` (string): 该具体应用、产品或项目的专有名称。
2.  `task_category` (string): 该应用的“横向”功能分类 (例如: "问答系统", "推荐系统", "语义搜索")。
3.  `organization` (string): 开发或运营该应用的组织 (如果未提及，留空字符串 "")。
4.  `domain` (string): 该应用的“垂直”行业领域 (例如: "电商", "医疗", "金融")。
5.  `purpose_summary` (string): 该应用的核心目的简介 (如果未提及，留空字符串 "")。
6.  `key_kg_function` (string): 知识图谱在该应用中扮演的关键角色 (如果未提及，留空字符串 "")。

## 输入文本 (Input)
{content}

## 输出格式 (Output)
你必须严格返回一个 JSON 列表。如果找不到任何 "应用" 实体，必须返回一个空列表 `[]`。

[
  {{
    "name": "...",
    "task_category": "...",
    "organization": "...",
    "domain": "...",
    "purpose_summary": "...",
    "key_kg_function": "..."
  }},
  ...
]

## 开始抽取：
"""