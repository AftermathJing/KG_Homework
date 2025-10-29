import json
import os
import logging
from src.constants.prompt import RELATION_EXTRACTION_TEMPLATE
from src.utils.llm_utils import load_qwen_model, call_my_4b_model


# --- 配置日志 (已精简) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# --- 路径配置 ---
INPUT_DIR = "./data/raw/overview/json"  # 包含原始文本块 JSON 列表的目录
MAP_OUTPUT_DIR = "./data/extraction_map"  # 包含实体映射文件的目录
RELATION_OUTPUT_DIR = "./data/relationship"  # 关系三元组的输出目录


def process_single_map_file(map_file_path: str, model, tokenizer, device: str):
    """
    处理单个映射文件，查找其对应的原始文本文件，并抽取关系。
    """

    filename = os.path.basename(map_file_path)
    # 假设映射文件名为 'data.json'，原始文件名也为 'data.json'
    input_file_path = os.path.join(INPUT_DIR, filename)

    if not os.path.exists(input_file_path):
        logging.error(f"找不到对应的原始文本文件: {input_file_path}。跳过 {filename}。")
        return

    logging.info(f"--- 正在处理文件对 ---")
    logging.info(f"  > 映射文件: {map_file_path}")
    logging.info(f"  > 文本文件: {input_file_path}")

    # 1. 加载两个文件
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            # input_data/data_chunks.json -> [{"id": "...", "content": "..."}, ...]
            content_list = json.load(f)

        with open(map_file_path, 'r', encoding='utf-8') as f:
            # extraction_map/data_chunks.json -> [{"id": "...", "concept": [...], ...}, ...]
            entity_map_list = json.load(f)
    except Exception as e:
        logging.error(f"加载文件时出错: {e}。跳过 {filename}。")
        return

    # 2. 创建快速查找字典
    content_lookup = {chunk["id"]: chunk["content"] for chunk in content_list if "id" in chunk and "content" in chunk}
    entity_map_lookup = {chunk["id"]: chunk for chunk in entity_map_list if "id" in chunk}

    all_relations_for_this_file = []

    # 3. 遍历 `extraction_map` 中的每一个文字块
    for chunk_id, entity_map in entity_map_lookup.items():

        # 3.1. 检查实体数量
        total_entities = (
                len(entity_map.get("concept", [])) +
                len(entity_map.get("technology", [])) +
                len(entity_map.get("document", [])) +
                len(entity_map.get("application", []))
        )

        # *** 如果实体少于2个，跳过 ***
        if total_entities < 2:
            logging.info(f"  > [块: {chunk_id}] 实体总数 ({total_entities}) < 2，跳过关系抽取。")
            continue

        # 3.2. 查找原始 content
        content = content_lookup.get(chunk_id)
        if not content:
            logging.warning(f"  > [块: {chunk_id}] 在 {input_file_path} 中找不到对应的 content。跳过。")
            continue

        logging.info(f"  > [块: {chunk_id}] 实体总数 {total_entities}。开始抽取关系...")

        # 3.3. 准备 Prompt 占位符
        concept_list_json = json.dumps(entity_map.get("concept", []), ensure_ascii=False)
        technology_list_json = json.dumps(entity_map.get("technology", []), ensure_ascii=False)
        document_list_json = json.dumps(entity_map.get("document", []), ensure_ascii=False)
        application_list_json = json.dumps(entity_map.get("application", []), ensure_ascii=False)

        # 3.4. 格式化 Prompt
        prompt_text = RELATION_EXTRACTION_TEMPLATE.format(
            concept_list_json=concept_list_json,
            technology_list_json=technology_list_json,
            document_list_json=document_list_json,
            application_list_json=application_list_json,
            content=content
        )

        # 3.5. 调用 LLM
        try:
            response_str = call_my_4b_model(prompt_text, model, tokenizer, device)
            extracted_triplets = json.loads(response_str)  # 这是一个列表，例如 [["s", "r", "o"], ...]

            logging.info(f"  > [块: {chunk_id}] 成功提取 {len(extracted_triplets)} 个关系。")

            # 3.6. 格式化三元组并添加来源 ID
            for triplet in extracted_triplets:
                if isinstance(triplet, list) and len(triplet) == 3:
                    formatted_relation = {
                        "subject": triplet[0],
                        "relation": triplet[1],
                        "object": triplet[2],
                        "chunk_id": chunk_id  # 添加来源 ID
                    }
                    all_relations_for_this_file.append(formatted_relation)
                else:
                    logging.warning(f"  > [块: {chunk_id}] 发现格式不正确的三元组: {triplet}")

        except json.JSONDecodeError:
            logging.error(f"  > 严重错误: LLM 为关系抽取 (块: {chunk_id}) 返回了无效的 JSON。")
            logging.error(f"  > 模型返回: {response_str}")
        except Exception as e:
            logging.error(f"  > 处理关系抽取 (块: {chunk_id}) 时发生未知错误: {e}")

    # 4. (用户要求) 每处理完一个文件，就保存关系
    if all_relations_for_this_file:
        try:
            # 输出文件名，例如 'relationship/data_chunks.json'
            output_path = os.path.join(RELATION_OUTPUT_DIR, filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_relations_for_this_file, f, ensure_ascii=False, indent=4)

            print(f"关系文件已保存到: {output_path}")

        except Exception as e:
            logging.error(f"无法写入关系文件 {output_path}: {e}")
    else:
        logging.info(f"文件 {filename} 中未提取到任何关系。")


def main():
    """
    主执行函数：加载模型，遍历映射文件，执行关系抽取，保存结果。
    """

    logging.info("加载真实模型 (用于关系抽取)...")
    model, tokenizer, device = load_qwen_model()
    if not model or not tokenizer:
        logging.error("模型加载失败，程序退出。")
        return

    logging.info(f"开始从 {MAP_OUTPUT_DIR} 目录处理映射文件...")

    if not os.path.exists(MAP_OUTPUT_DIR):
        logging.error(f"映射目录未找到: {MAP_OUTPUT_DIR}。请先运行 run_extraction.py。")
        return
    if not os.path.exists(INPUT_DIR):
        logging.error(f"原始数据目录未找到: {INPUT_DIR}。")
        return

    # 确保输出目录存在
    os.makedirs(RELATION_OUTPUT_DIR, exist_ok=True)

    for filename in os.listdir(MAP_OUTPUT_DIR):
        if filename.endswith(".json"):
            map_file_path = os.path.join(MAP_OUTPUT_DIR, filename)
            process_single_map_file(map_file_path, model, tokenizer, device)

    logging.info(f"所有关系抽取任务处理完毕。")


if __name__ == "__main__":
    if not os.path.exists("./src/constants/prompt.py"):
        print("错误： 'prompt.py' (v5) 文件未找到。请先创建该文件。")
    elif not os.path.exists("./src/utils/llm_utils.py"):
        print("错误： 'llm_utils.py' 文件未找到。请先创建该文件。")
    else:
        main()