import json
import os
import logging
import re
from src.utils.llm_utils import load_qwen_model, call_my_4b_model
from src.constants.prompt import REFERENCE_LINKING_TEMPLATE

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# --- 路径配置 ---
INPUT_DIR = "./data/raw/overview/json"
MAP_OUTPUT_DIR = "./data/extraction_map"
RELATION_OUTPUT_DIR = "./data/relationship"

# --- 编译正则表达式 ---
# 匹配 [1], [3-4], [1, 5], [ 9 ], ［９］ (半角/全角)
CITATION_REGEX = re.compile(r'[\[［]\s*([\d\s,-]+?)\s*[\]］]')
# 匹配 "参考文献[1]" 中的数字
REF_TOPIC_REGEX = re.compile(r'\[(\d+)\]')


def parse_citation_string(text: str) -> list[int]:
    """
    将引用字符串 (例如 "1, 3-4", " 9 ") 解析为数字列表 (例如 [1, 3, 4], [9])。
    """
    numbers = set()
    try:
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                # 处理范围, 例如 "3-4"
                range_parts = part.split('-')
                if len(range_parts) == 2:
                    start = int(range_parts[0].strip())
                    end = int(range_parts[1].strip())
                    if end >= start:
                        numbers.update(range(start, end + 1))
            else:
                # 处理单个数字
                numbers.add(int(part))
    except ValueError:
        logging.warning(f"解析引用字符串时出错: '{text}'")
    return sorted(list(numbers))


def check_entities_exist(entity_map: dict) -> bool:
    """检查实体映射中是否至少有一个实体"""
    total = (
            len(entity_map.get("concept", [])) +
            len(entity_map.get("technology", [])) +
            len(entity_map.get("document", [])) +
            len(entity_map.get("application", []))
    )
    return total > 0


def process_document_pair(base_name: str, model, tokenizer, device: str):
    """
    处理一对正文文件和参考文献文件。
    """
    # 1. 定义文件路径
    main_body_file = os.path.join(INPUT_DIR, f"{base_name}_abstract_main_body.json")
    ref_file = os.path.join(INPUT_DIR, f"{base_name}_info_references.json")
    main_map_file = os.path.join(MAP_OUTPUT_DIR, f"{base_name}_abstract_main_body.json")
    ref_map_file = os.path.join(MAP_OUTPUT_DIR, f"{base_name}_info_references.json")

    output_relation_file = os.path.join(RELATION_OUTPUT_DIR, f"{base_name}_ref_relations.json")

    # 2. 检查所有文件是否存在
    required_files = [main_body_file, ref_file, main_map_file, ref_map_file]
    if not all(os.path.exists(f) for f in required_files):
        logging.warning(f"跳过 {base_name}: 缺少一个或多个必需文件。")
        return

    logging.info(f"--- 正在处理 {base_name} ---")

    # 3. 加载所有数据
    try:
        with open(main_body_file, 'r', encoding='utf-8') as f:
            main_chunks = json.load(f)  # List
        with open(ref_file, 'r', encoding='utf-8') as f:
            ref_chunks = json.load(f)  # List
        with open(main_map_file, 'r', encoding='utf-8') as f:
            main_entities = json.load(f)  # List
        with open(ref_map_file, 'r', encoding='utf-8') as f:
            ref_entities = json.load(f)  # List
    except Exception as e:
        logging.error(f"加载 {base_name} 的文件时出错: {e}")
        return

    # 4. 构建快速查找表
    main_content_lookup = {chunk["id"]: chunk["content"] for chunk in main_chunks}
    ref_content_lookup = {chunk["id"]: chunk["content"] for chunk in ref_chunks}  # <-- (修改 2) 新增引文内容查找表
    main_entity_lookup = {chunk["id"]: chunk for chunk in main_entities}
    ref_entity_lookup = {chunk["id"]: chunk for chunk in ref_entities}

    # 构建 参考文献编号 -> 参考文献块ID 的映射
    ref_num_to_id_lookup = {}
    for chunk in ref_chunks:
        topic = chunk.get("topic", "")
        match = REF_TOPIC_REGEX.search(topic)
        if match:
            try:
                ref_num = int(match.group(1))
                ref_num_to_id_lookup[ref_num] = chunk["id"]
            except ValueError:
                pass

    logging.info(f"为 {base_name} 构建了 {len(ref_num_to_id_lookup)} 条参考文献编号映射。")

    all_new_relations = []

    # 5. --- 核心逻辑：遍历正文文字块 ---
    for main_chunk in main_chunks:
        chunk_id = main_chunk.get("id")
        chunk_content = main_chunk.get("content")

        if not chunk_id or not chunk_content:
            continue

        # 5.1 查找引用
        found_citations = CITATION_REGEX.finditer(chunk_content)

        cited_ref_ids = set()
        citations_found = False
        for match in found_citations:
            citations_found = True
            citation_text = match.group(1)  # "1, 3-4"
            numbers = parse_citation_string(citation_text)
            for num in numbers:
                ref_id = ref_num_to_id_lookup.get(num)
                if ref_id:
                    cited_ref_ids.add(ref_id)

        # (用户要求) 如果没有引用，跳过
        if not citations_found or not cited_ref_ids:
            continue

        # 5.2 获取正文实体
        main_entity_map = main_entity_lookup.get(chunk_id)

        # (用户要求) 如果正文块没有实体，跳过
        if not main_entity_map or not check_entities_exist(main_entity_map):
            logging.info(f"[块: {chunk_id}] 找到了引用，但该块本身没有实体，跳过。")
            continue

        logging.info(f"[块: {chunk_id}] 发现 {len(cited_ref_ids)} 个有效引用。正在检查关系...")

        # 5.3 遍历引用的参考文献块
        for ref_id in cited_ref_ids:
            ref_entity_map = ref_entity_lookup.get(ref_id)

            # (用户要求) 如果参考文献块没有实体，跳过
            if not ref_entity_map or not check_entities_exist(ref_entity_map):
                logging.info(f"[块: {chunk_id}] 引用了 [Ref ID: {ref_id}]，但该参考文献块没有实体，跳过。")
                continue

            # (修改 3) 获取引文 content
            ref_content = ref_content_lookup.get(ref_id)
            if not ref_content:
                logging.warning(f"[块: {chunk_id}] 找到了 Ref ID {ref_id} 的实体，但未找到其 content。跳过。")
                continue

            # 5.4 --- 找到匹配：正文块(有实体) 引用 参考文献块(有实体) ---
            logging.info(f"  > 匹配成功！[块: {chunk_id}] 引用 [Ref ID: {ref_id}]。准备调用 LLM...")

            # (修改 4) 准备 Prompt（不再合并列表）
            prompt_text = REFERENCE_LINKING_TEMPLATE.format(
                main_content=chunk_content,
                ref_content=ref_content,

                main_concept_list_json=json.dumps(main_entity_map.get("concept", []), ensure_ascii=False),
                main_tech_list_json=json.dumps(main_entity_map.get("technology", []), ensure_ascii=False),
                main_doc_list_json=json.dumps(main_entity_map.get("document", []), ensure_ascii=False),
                main_app_list_json=json.dumps(main_entity_map.get("application", []), ensure_ascii=False),

                ref_concept_list_json=json.dumps(ref_entity_map.get("concept", []), ensure_ascii=False),
                ref_tech_list_json=json.dumps(ref_entity_map.get("technology", []), ensure_ascii=False),
                ref_doc_list_json=json.dumps(ref_entity_map.get("document", []), ensure_ascii=False),
                ref_app_list_json=json.dumps(ref_entity_map.get("application", []), ensure_ascii=False)
            )

            # 5.5 调用 LLM
            try:
                response_str = call_my_4b_model(prompt_text, model, tokenizer, device)
                extracted_triplets = json.loads(response_str)

                logging.info(f"  > [块: {chunk_id}] -> [Ref ID: {ref_id}] 提取了 {len(extracted_triplets)} 个关系。")

                for triplet in extracted_triplets:
                    if isinstance(triplet, list) and len(triplet) == 3:
                        formatted_relation = {
                            "subject": triplet[0],
                            "relation": triplet[1],
                            "object": triplet[2],
                            "main_chunk_id": chunk_id,
                            "reference_chunk_id": ref_id
                        }
                        all_new_relations.append(formatted_relation)
                    else:
                        logging.warning(f"  > 发现格式不正确的三元组: {triplet}")

            except json.JSONDecodeError:
                logging.error(f"  > 严重错误: LLM 为引用关系 (块: {chunk_id}) 返回了无效的 JSON。")
            except Exception as e:
                logging.error(f"  > LLM 调用失败: {e}")

    # 6. 保存这个文件对的所有关系
    if all_new_relations:
        try:
            with open(output_relation_file, 'w', encoding='utf-8') as f:
                json.dump(all_new_relations, f, ensure_ascii=False, indent=4)
            print(f"参考文献关系已保存到: {output_relation_file}")
        except Exception as e:
            logging.error(f"无法写入 {output_relation_file}: {e}")
    else:
        logging.info(f"--- {base_name} 处理完毕，未提取到新的参考文献关系。 ---")


def main():
    """
    主执行函数：加载模型，查找成对的文件，执行链接和关系抽取。
    """

    logging.info("加载真实模型 (用于引用链接)...")
    model, tokenizer, device = load_qwen_model()
    if not model or not tokenizer:
        logging.error("模型加载失败，程序退出。")
        return

    # 确保目录存在
    os.makedirs(RELATION_OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_DIR) or not os.path.exists(MAP_OUTPUT_DIR):
        logging.error(f"输入目录 {INPUT_DIR} 或 {MAP_OUTPUT_DIR} 未找到。")
        return

    logging.info("正在查找成对的正文/参考文献文件...")

    # 查找所有正文文件 (abstract_main_body)
    base_names = set()
    for f in os.listdir(INPUT_DIR):
        if f.endswith("_abstract_main_body.json"):
            base_names.add(f.replace("_abstract_main_body.json", ""))

    if not base_names:
        logging.warning(f"在 {INPUT_DIR} 中未找到任何 `..._abstract_main_body.json` 文件。")
        return

    logging.info(f"找到了 {len(base_names)} 个文档集: {base_names}")

    for base_name in base_names:
        process_document_pair(base_name, model, tokenizer, device)

    logging.info("所有参考文献链接任务处理完毕。")


if __name__ == "__main__":
        main()

