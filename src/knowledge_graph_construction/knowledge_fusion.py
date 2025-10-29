import json
import os
import logging
import glob
from collections import defaultdict
from src.utils.llm_utils import load_qwen_model, call_my_4b_model
from src.constants.prompt import ENTITY_FUSION_TEMPLATE

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# --- 路径配置 ---
ENTITY_INPUT_DIR = "./data/entity"
RELATION_INPUT_DIR = "./data/relationship"

FUSED_ENTITY_DIR = "./data/KG/entity"
FUSED_RELATION_DIR = "./data/KG/relationship"
FUSED_RELATION_FILE = os.path.join(FUSED_RELATION_DIR, "all_relations_fused.json")

# LLM 调用批次大小，用于解决"同名实体过多"的问题
MAX_FUSION_BATCH_SIZE = 10


def fuse_relations():
    """
    (用户要求 2) 融合所有关系。
    读取 relationship/ 目录下的所有 .json 文件，
    对 ("subject", "relation", "object") 完全相同的三元组进行去重。
    """
    logging.info("--- 开始融合关系 (程序化去重) ---")
    os.makedirs(FUSED_RELATION_DIR, exist_ok=True)

    relation_files = glob.glob(os.path.join(RELATION_INPUT_DIR, "*.json"))
    if not relation_files:
        logging.warning(f"在 {RELATION_INPUT_DIR} 中未找到任何关系文件。")
        return

    # 使用集合进行高效去重
    unique_relations_set = set()

    for file_path in relation_files:
        logging.info(f"正在读取关系文件: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                relations = json.load(f)

            for rel in relations:
                # 确保关系是标准格式
                if "subject" in rel and "relation" in rel and "object" in rel:
                    # 创建一个可哈希的元组作为键
                    triplet_key = (rel["subject"], rel["relation"], rel["object"])
                    unique_relations_set.add(triplet_key)
        except Exception as e:
            logging.error(f"处理关系文件 {file_path} 时出错: {e}")

    # 将去重后的元组转换回字典列表
    fused_relations_list = [
        {"subject": s, "relation": r, "object": o}
        for s, r, o in unique_relations_set
    ]

    logging.info(f"关系融合完毕。总关系数: {len(unique_relations_set)}")

    # 保存融合后的关系
    try:
        with open(FUSED_RELATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(fused_relations_list, f, ensure_ascii=False, indent=4)
        print(f"融合后的关系已保存到: {FUSED_RELATION_FILE}")
    except Exception as e:
        logging.error(f"写入融合关系文件时出错: {e}")


def run_llm_fusion(batch: list, name: str, model, tokenizer, device: str) -> dict | None:
    """
    调用 LLM 执行单个批次的融合。
    """
    try:
        prompt_text = ENTITY_FUSION_TEMPLATE.format(
            count=len(batch),
            name=name,
            entity_list_json=json.dumps(batch, ensure_ascii=False, indent=2)
        )

        response_str = call_my_4b_model(prompt_text, model, tokenizer, device)
        fused_entity = json.loads(response_str)[0]  # 预期输出是单个 JSON 对象

        if isinstance(fused_entity, dict):
            return fused_entity
        else:
            logging.warning(f"LLM 融合返回的不是一个 JSON 对象: {fused_entity}")
            return None  # 或者返回 batch[0] 作为后备
    except json.JSONDecodeError:
        logging.error(f"LLM 融合返回了无效的 JSON: {response_str}")
    except Exception as e:
        logging.error(f"LLM 融合批次时发生未知错误: {e}")

    # 如果失败，返回批次中的第一个元素作为非融合的后备
    return batch[0]


def fuse_entities(model, tokenizer, device: str):
    """
    (用户要求 1) 融合所有实体。
    读取 data/entity/ 目录下的文件，按 name/title 分组，
    并使用 LLM 对同名实体进行分层融合。
    """
    logging.info("--- 开始融合实体 (基于 LLM) ---")
    os.makedirs(FUSED_ENTITY_DIR, exist_ok=True)

    if not os.path.exists(ENTITY_INPUT_DIR):
        logging.error(f"实体输入目录未找到: {ENTITY_INPUT_DIR}")
        return

    entity_files_to_process = [
        ("concept.json", "name"),
        ("technology.json", "name"),
        ("document.json", "title"),
        ("application.json", "name")
    ]

    for filename, key_field in entity_files_to_process:
        input_file = os.path.join(ENTITY_INPUT_DIR, filename)
        output_file = os.path.join(FUSED_ENTITY_DIR, filename)

        if not os.path.exists(input_file):
            logging.warning(f"实体文件未找到: {input_file}。跳过。")
            continue

        logging.info(f"--- 正在融合: {filename} (基于 '{key_field}') ---")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                all_entities = json.load(f)
        except Exception as e:
            logging.error(f"读取 {input_file} 时出错: {e}")
            continue

        # 1. 按 name/title 分组
        groups = defaultdict(list)
        for entity in all_entities:
            key = entity.get(key_field)
            if key:
                groups[key].append(entity)

        fused_list = []

        # 2. 遍历所有分组
        for name, entity_list in groups.items():
            if len(entity_list) == 1:
                # 2.1. 无需融合
                fused_list.append(entity_list[0])
            else:
                # 2.2. 需要融合
                logging.info(f"正在融合 '{name}' (共 {len(entity_list)} 个实体)...")

                # *** 分层融合 (Hierarchical Merging) ***
                # 这解决了 "同名实体过多" 的问题。
                current_list = entity_list

                # 持续融合，直到这一组只剩 1 个实体
                while len(current_list) > 1:
                    logging.info(f"  > 融合轮次: {len(current_list)} -> ...")
                    next_list = []

                    # 按 MAX_FUSION_BATCH_SIZE 分批
                    for i in range(0, len(current_list), MAX_FUSION_BATCH_SIZE):
                        batch = current_list[i:i + MAX_FUSION_BATCH_SIZE]

                        if len(batch) == 1:
                            next_list.append(batch[0])  # 此批次无需融合，直接进入下一轮
                            continue

                        logging.info(f"    > 正在调用 LLM 融合 {len(batch)} 个...")
                        # (同步执行，如果需要加速，可以改为异步)
                        fused_entity = run_llm_fusion(batch, name, model, tokenizer, device)
                        if fused_entity:
                            next_list.append(fused_entity)

                    current_list = next_list  # 更新列表以进行下一轮融合

                if current_list:  # current_list[0] 是最终融合的实体
                    fused_list.append(current_list[0])

        # 3. 保存该类型实体的融合结果
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(fused_list, f, ensure_ascii=False, indent=4)
            print(f"融合后的实体已保存到: {output_file}")
        except Exception as e:
            logging.error(f"写入融合实体文件 {output_file} 时出错: {e}")


def main():
    """
    主执行函数：加载模型，执行关系融合，然后执行实体融合。
    """

    # 1. 关系融合 (不需要 LLM)
    fuse_relations()

    # 2. 实体融合 (需要 LLM)
    logging.info("加载真实模型 (用于实体融合)...")
    model, tokenizer, device = load_qwen_model()
    if not model or not tokenizer:
        logging.error("模型加载失败，实体融合程序退出。")
        return

    fuse_entities(model, tokenizer, device)

    logging.info("所有知识融合任务处理完毕。")


if __name__ == "__main__":
        main()
