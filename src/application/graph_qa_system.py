import os
import re
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFacePipeline
from langchain_core.runnables import RunnableLambda
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from src.constants.prompt import CYPHER_GENERATION_TEMPLATE, QA_TEMPLATE

# --- 1. 配置信息 ---
MODEL_PATH = os.path.expanduser('~/Qwen3-8B')
NEO4J_URI = "neo4j+ssc://a3d54e0b.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "17_Up5JUzf-iRepWtq_XP5QbrPe7HpbkXOLgPn-HSzY"


class KnowledgeGraphQA:
    """
    封装了知识图谱问答系统的所有逻辑。
    - 加载本地 LLM
    - 连接 Neo4j 数据库
    - 构建 LangChain RAG 链
    - 提供一个用于查询的接口
    """

    def __init__(self):
        """
        初始化系统，加载模型和连接数据库。
        """
        print("--- 正在初始化知识图谱问答系统 ---")
        self.llm = self._load_llm()
        self.graph = self._connect_graph()

        if self.llm is None or self.graph is None:
            print("错误：LLM 或 Neo4j 未能成功初始化。退出程序。")
            exit()

        self.chain = self._build_chain()
        print("--- 系统初始化完毕，准备就绪 ---")

    def _load_llm(self):
        """
        私有方法：从本地路径加载 Transformers 模型和 Pipeline。
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"准备在 {device} 上加载模型...")

        try:
            # 1.1 加载 Tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                MODEL_PATH,
                trust_remote_code=True
            )

            # 1.2 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            model.eval()

            # 1.3 创建 Transformers Pipeline
            transformer_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=1024,
                temperature=0.01,
                top_p=0.95,
                repetition_penalty=1.15
            )

            # 1.4 包装为 LangChain LLM
            llm = HuggingFacePipeline(pipeline=transformer_pipeline)
            print(f"模型 {MODEL_PATH} 在 {device} 上加载并包装完毕。")
            return llm

        except Exception as e:
            print(f"加载本地模型失败: {e}")
            print(f"请确保 Transformers 和 Torch 已安装 (pip install transformers torch accelerate)")
            print(f"并检查 MODEL_PATH ('{MODEL_PATH}') 是否正确。")
            return None

    def _connect_graph(self):
        """
        私有方法：连接到 Neo4j 数据库并刷新 schema。
        """
        try:
            print("正在连接 Neo4j 数据库...")
            graph = Neo4jGraph(
                url=NEO4J_URI,
                username=NEO4J_USER,
                password=NEO4J_PASSWORD
            )
            graph.refresh_schema()
            print("Neo4j 数据库连接成功，模式刷新完毕。")
            # print(graph.schema) # 取消注释以查看 schema
            return graph
        except Exception as e:
            print(f"连接 Neo4j 或刷新模式失败: {e}")
            print("请检查您的 Neo4j 凭据和网络连接。")
            return None

    def _extract_cypher_from_think(self, llm_output: str) -> str:
        """
        【新增方法】
        私有方法：从 LLM 的输出中提取 Cypher 语句，
        忽略可能存在的 <think>...</think> 标签。
        """
        match = re.search(r"^\s*<think>([\s\S]*?)</think>([\s\S]*)", llm_output, re.DOTALL | re.IGNORECASE)

        if match:
            # 如果找到 think 标签，假定 Cypher 是标签 *之后* 的内容
            cypher_query = match.group(2).strip()
            return cypher_query
        else:
            # 如果没有 think 标签，假定整个输出就是 Cypher
            return llm_output.strip()

    def _build_chain(self):
        """
        私有方法：使用 LLM 和 Graph 构建 GraphCypherQAChain。
        """
        print("正在构建 QA 链...")
        cypher_prompt = ChatPromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)
        qa_prompt = ChatPromptTemplate.from_template(QA_TEMPLATE)

        # 1. 使用 from_llm 构建基础链条
        base_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt,
            verbose=True,  # 仍然在控制台打印 Cypher 语句
            return_intermediate_steps=True,
            allow_dangerous_requests=True
        )

        # 2. 构建一个 *新* 的 Cypher 生成链，它包含了解析逻辑
        new_cypher_chain = (
                cypher_prompt
                | self.llm
                | RunnableLambda(self._extract_cypher_from_think)  # <-- 注入解析器
        )

        # 3. 将基础链条的默认 cypher_chain 替换为我们带解析器的新链条
        base_chain.cypher_generation_chain = new_cypher_chain

        print("QA 链已应用 Cypher 解析逻辑。")
        return base_chain

    def _parse_output(self, result_text: str) -> (str, str):
        """
        私有方法：解析 LLM 的 *最终* 输出，分离 "思考" 和 "回答" 内容。
        假设 "思考" 内容以 "<think>...</think>" 标签包裹。
        """
        match = re.search(r"^\s*<think>([\s\S]*?)</think>([\s\S]*)", result_text, re.DOTALL | re.IGNORECASE)

        if match:
            thinking = match.group(1).strip()  # 提取思考内容 (Group 1)
            answer = match.group(2).strip()  # 提取回答内容 (Group 2)
            return thinking, answer
        else:
            # 如果没有匹配到 "思考" 模式，则认为全部都是回答
            return None, result_text.strip()

    def query(self, question: str) -> dict:
        """
        公共方法：接收一个问题，返回一个包含所有信息的结构化字典。
        这是为前端或 API 准备的。
        """
        print(f"\n正在处理问题: {question}")
        try:
            response = self.chain.invoke({"query": question})

            result_text = response['result']
            thinking, answer = self._parse_output(result_text)

            intermediate_steps = response.get('intermediate_steps', [{}, {}])
            cypher_query = intermediate_steps[0].get('query', 'N/A')
            db_results = intermediate_steps[1].get('context', 'N/A')

            return {
                "success": True,
                "question": question,
                "thinking": thinking,  # Qwen 的思考过程
                "answer": answer,  # 最终的回答
                "cypher_query": cypher_query,  # 中间的 Cypher 查询
                "db_results": db_results,  # Cypher 的原始结果
                "error": None
            }

        except Exception as e:
            print(f"处理问题时出错: {e}")
            return {
                "success": False,
                "question": question,
                "thinking": None,
                "answer": None,
                "cypher_query": None,
                "db_results": None,
                "error": str(e)
            }


# --- 5. 运行问答循环 ---
if __name__ == "__main__":

    # 1. 初始化QA系统
    qa_system = KnowledgeGraphQA()

    print("--- 知识图谱问答系统 (Qwen + Neo4j) ---")
    print("输入 'exit' 退出。")

    while True:
        question = input("\n请输入您的问题: ")
        if question.lower() == 'exit':
            break
        if not question:
            continue

        # 2. 调用 query 方法
        result = qa_system.query(question)

        # 3. 打印结构化结果
        if result["success"]:
            if result["thinking"]:
                print(f"\n[思考过程]:\n{result['thinking']}")

            print(f"\n< 回答:\n{result['answer']}")

            print("\n[调试信息]:")
            print(f"  Cypher 查询:\n{result['cypher_query']}")
            # print(f"  DB 结果:\n{result['db_results']}") # 默认关闭，结果可能太长
        else:
            print(f"\n处理问题时出错: {result['error']}")

