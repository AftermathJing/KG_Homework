# **知识图谱：关系抽取策略定义文档**

本文档基于 prompt.py 文件中的 RELATION\_EXTRACTION\_TEMPLATE (v2)，定义了关系抽取的策略和 Schema。

## **1\. 核心策略：受约束的抽取 (Constrained Extraction)**

为了适应 4B 模型的能力，我们不采用开放式的关系抽取。相反，我们使用一种“受约束”的方法：

1. **输入源**：对于每一个文本块 (Chunk)，我们同时向模型提供**原始文本 (Content)** 和**按类型分类的实体名称列表**（即 extraction\_map 的输出）。  
2. **任务降维**：模型不再需要“寻找”实体，只需在我们提供的列表中“连接”实体。  
3. **模式引导**：我们通过“推荐的关系模式”来指导模型，只在有意义的实体类型之间（例如 Concept 和 Document）寻找特定关系。

## **2\. 实体类型定义 (Entity Types)**

在关系抽取任务中，模型被告知有以下四类实体：

* **Concepts (概念)**: 抽象思想、模型、任务 (例如: "知识表示学习", "TransE")。  
* **Technologies (技术)**: 具体工具、平台、语言 (例如: "Neo4j", "SPARQL")。  
* **Documents (文档)**: 论文、博客、报告 (例如: "Translating Embeddings...")。  
* **Applications (应用)**: 具体产品、系统 (例如: "Siri", "Google 搜索")。

## **3\. 关系类型定义 (Relation List)**

模型**只能**使用以下 6 种预定义的关系类型：

1. **IS\_A (是一个)**:  
   * 描述：表示子类或实例关系。  
   * *示例*: \["TransE", "IS\_A", "知识表示模型"\]  
2. **RELATED\_TO (相关于)**:  
   * 描述：表示两个实体在上下文中相关。  
   * *示例*: \["知识图谱", "RELATED\_TO", "搜索引擎"\]  
3. **IMPLEMENTS (实现)**:  
   * 描述：表示一个技术实现了一个概念，或一个应用实现了一个任务。  
   * *示例*: \["Neo4j", "IMPLEMENTS", "图数据库"\]  
   * *示例*: \["Siri", "IMPLEMENTS", "问答系统"\]  
4. **USES (使用)**:  
   * 描述：表示一个应用或技术使用了另一个技术或概念。  
   * *示例*: \["Siri", "USES", "Neo4j"\]  
5. **DESCRIBED\_IN (记载于)**:  
   * 描述：表示一个实体（概念、技术或应用）被一个文档所描述。  
   * *示例*: \["TransE", "DESCRIBED\_IN", "Translating Embeddings..."\]  
6. **CREATED\_BY (创建于)**:  
   * 描述：表示一个产品或技术由某个组织创建（该组织必须在实体列表中）。  
   * *示例*: \["Siri", "CREATED\_BY", "Apple"\]

## **4\. 推荐的关系模式 (Recommended Patterns)**

这是指导 4B 模型的核心逻辑。模型被要求**优先**寻找符合以下 (主语类型) \-\> \[关系\] \-\> (宾语类型) 模式的关系：

* (Concept) \- **IS\_A** \-\> (Concept)  
* (Concept) \- **RELATED\_TO** \-\> (Concept)  
* (Technology) \- **IMPLEMENTS** \-\> (Concept)  
* (Application) \- **IMPLEMENTS** \-\> (Concept)  
* (Application) \- **USES** \-\> (Technology)  
* (Application) \- **USES** \-\> (Concept)  
* (Technology) \- **USES** \-\> (Concept)  
* (Concept) \- **DESCRIBED\_IN** \-\> (Document)  
* (Technology) \- **DESCRIBED\_IN** \-\> (Document)  
* (Application) \- **DESCRIBED\_IN** \-\> (Document)  
* (Application) \- **CREATED\_BY** \-\> (Concept or Application) *（注：此模式在 Prompt 中定义，通常用于组织）*

## **5\. 输入与输出**

### **5.1 输入 (Input)**

调用模型时需要格式化 5 个占位符：

* {concept\_list\_json}: 该文本块中包含的 **概念** 实体名称的 JSON 列表。  
* {technology\_list\_json}: 该文本块中包含的 **技术** 实体名称的 JSON 列表。  
* {document\_list\_json}: 该文本块中包含的 **文档** 实体名称的 JSON 列表。  
* {application\_list\_json}: 该文本块中包含的 **应用** 实体名称的 JSON 列表。  
* {content}: 该文本块的 **原始文本**。

### **5.2 输出 (Output)**

模型被要求严格返回一个 JSON 列表，格式为三元组：  
\["Subject Entity Name", "RELATION\_TYPE", "Object Entity Name"\]