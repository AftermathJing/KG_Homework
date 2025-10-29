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

"""
关系抽取 (Relationship Extraction) Prompt
"""

RELATION_EXTRACTION_TEMPLATE = """# 任务：知识图谱关系抽取 (Task: Knowledge Graph Relation Extraction)

你是一个精准的关系抽取助手。
你的任务是从给定的 "Content" (原始文本) 中，找出 "Entity Lists" (实体列表) 中实体之间存在的关系。

## 1. 约束条件 (Rules)
1.  你必须只从 "Entity Lists" 提供的四个列表中选择实体作为关系的主语 (Subject) 和宾语 (Object)。
2.  你必须只使用以下定义的 "Relation List" (关系列表) 中的关系。
3.  关系必须在 "Content" 文本中有明确或强烈的暗示。
4.  主语 (Subject) 和宾语 (Object) 不能是同一个实体。

## 2. 实体类型定义 (Entity Types Definition)
这是你需要处理的四类实体：
* `Concepts`: 抽象思想、模型、任务 (例如: "知识表示学习", "TransE")。
* `Technologies`: 具体工具、平台、语言 (例如: "Neo4j", "SPARQL")。
* `Documents`: 论文、博客、报告 (例如: "Translating Embeddings...")。
* `Applications`: 具体产品、系统 (例如: "Siri", "Google 搜索")。

## 3. 关系列表 (Relation List) - 你只能使用这 6 种
* `IS_A`: (是一个) 表示子类或实例关系。
* `RELATED_TO`: (相关于) 表示两个实体在上下文中相关。
* `IMPLEMENTS`: (实现) 表示一个技术实现了一个概念，或一个应用实现了一个任务。
* `USES`: (使用) 表示一个应用/技术使用了另一个技术/概念。
* `DESCRIBED_IN`: (记载于) 表示一个实体被一个文档描述。
* `CREATED_BY`: (创建于) 表示一个产品或技术由某个组织创建。

## 4. 推荐的关系模式 (Recommended Patterns)
请优先寻找符合以下模式的关系：
* (Concept) - `IS_A` -> (Concept)
* (Concept) - `RELATED_TO` -> (Concept)
* (Technology) - `IMPLEMENTS` -> (Concept)
* (Application) - `IMPLEMENTS` -> (Concept)
* (Application) - `USES` -> (Technology)
* (Application) - `USES` -> (Concept)
* (Technology) - `USES` -> (Concept)
* (Concept) - `DESCRIBED_IN` -> (Document)
* (Technology) - `DESCRIBED_IN` -> (Document)
* (Application) - `DESCRIBED_IN` -> (Document)
* (Application) - `CREATED_BY` -> (Concept or Application)  (例如 "Apple" 必须在列表中)

## 5. 输入数据 (Input)

### 5.1 实体列表 (Entity Lists)
(这些是已从文本中提取的、允许你使用的实体，按类型分类)

**Concepts (概念):**
{concept_list_json}

**Technologies (技术):**
{technology_list_json}

**Documents (文档):**
{document_list_json}

**Applications (应用):**
{application_list_json}

### 5.2 原始文本 (Content)
{content}

## 6. 输出格式 (Output)
请严格按照以下 JSON 列表格式返回你抽取到的关系三元组。
三元组的格式必须是: `["Subject Entity Name", "RELATION_TYPE", "Object Entity Name"]`
如果找不到任何关系，请返回一个空列表 `[]`。

[
  ["Subject Entity Name", "RELATION_TYPE", "Object Entity Name"],
  ["...", "...", "..."]
]

## 7. 开始抽取
"""


"""
参考文献链接 (Reference Linking) Prompt
"""

REFERENCE_LINKING_TEMPLATE = """# 任务：正文-参考文献 关系链接

你是一个精准的关系链接助手。
你的任务是基于"正文"（其中包含引用）和它所引用的"参考文献"的文本，
找出 "正文实体" 和 "参考文献实体" 之间的关系。

## 1. 背景
"正文" (Main Content) 是一段普通文本，它引用了 "参考文献" (Reference Content)。
你需要阅读这两段文本，并在两组实体列表之间建立联系。

## 2. 约束条件 (Rules)
1.  你必须只从 "正文实体" 和 "参考文献实体" 提供的列表中选择实体。
2.  你必须只使用以下定义的 "Relation List" (关系列表)。
3.  关系必须在两段文本的综合上下文中得到支持。
4.  请**重点关注** "正文实体" 和 "参考文献实体" 之间的**跨组关系**。

## 3. 关系列表 (Relation List) - 你只能使用这 6 种
* `IS_A`: (是一个) 表示子类或实例关系。
* `RELATED_TO`: (相关于) 表示两个实体在上下文中相关。
* `IMPLEMENTS`: (实现) 表示一个技术实现了一个概念，或一个应用实现了一个任务。
* `USES`: (使用) 表示一个应用/技术使用了另一个技术/概念。
* `DESCRIBED_IN`: (记载于) **(高频)** 表示一个概念/技术在参考文献中被描述。
* `CREATED_BY`: (创建于) 表示一个产品或技术由某个组织创建。

## 4. 推荐的关系模式 (Recommended Patterns)
请优先寻找符合以下模式的关系：
* (正文 Concept) - `DESCRIBED_IN` -> (参考文献 Document)
* (正文 Concept) - `RELATED_TO` -> (参考文献 Concept)
* (正文 Technology) - `DESCRIBED_IN` -> (参考文献 Document)
* (正文 Entity) - `IS_A` -> (参考文献 Entity)

## 5. 输入数据 (Input)

### 5.1 正文 (Main Content)
(这是发现引用的地方)
{main_content}

### 5.2 参考文献 (Reference Content)
(这是被引用的参考文献的文本)
{ref_content}

### 5.3 实体列表 (Entity Lists)

**正文实体 (Main Content Entities):**
* Concepts: {main_concept_list_json}
* Technologies: {main_tech_list_json}
* Documents: {main_doc_list_json}
* Applications: {main_app_list_json}

**参考文献实体 (Reference Entities):**
* Concepts: {ref_concept_list_json}
* Technologies: {ref_tech_list_json}
* Documents: {ref_doc_list_json}
* Applications: {ref_app_list_json}

## 6. 输出格式 (Output)
请严格按照以下 JSON 列表格式返回你抽取到的关系三元组。
三元组的格式必须是: `["Subject Entity Name", "RELATION_TYPE", "Object Entity Name"]`
如果找不到任何关系，请返回一个空列表 `[]`。

[
  ["Subject Entity Name", "RELATION_TYPE", "Object Entity Name"],
  ["...", "...", "..."]
]

## 7. 开始抽取
"""


"""
实体融合 Prompt
"""

ENTITY_FUSION_TEMPLATE = """任务：知识图谱实体融合

你是一个知识融合专家。你的任务是读取一个 JSON 列表，其中包含多个关于 同一个实体 (同名) 的信息，并将它们融合成一个 单一的、权威的 JSON 对象。

1. 约束条件 (Rules)

输入是一个 JSON 列表 (N 个实体)。

输出必须是 一个 JSON 对象 (1 个实体)。

name (或 title): 保持不变，因为它们都是一样的。

definition / abstract_or_summary / purpose: 从列表中选择一个最清晰、最完整、最准确的描述，如果列表中的描述均不能满足要求，则根据这些描述生成一份清晰、完整、准确的描述，**注意生成的时候必须贴近原描述**。

aliases / key_features: 合并所有列表，并去除重复项。

category / sub_domain / organization / domain / task_category: 从列表中选择最常见 (most common) 或最准确 (most specific) 的一个或几个。

publication_year / vendor_or_originator: 选择最权威或最常见的一个或几个。

2. 输入数据 (Input)

(这是一个 JSON 列表，包含 {count} 个关于 "{name}" 的实体)
{entity_list_json}

3. 输出格式 (Output)

请严格按照原始 JSON 对象的格式，返回 一个 融合后的 JSON 对象。

(例如，对于 Concept 类型):
{{
"name": "{name}",
"definition": "...",
"aliases": ["...", "..."],
"category": "...",
"sub_domain": "...",
"purpose": "..."
}}

4. 开始融合
"""