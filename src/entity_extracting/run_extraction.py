import json
import os
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from prompt import (
    CONCEPT_EXTRACTION_TEMPLATE,
    TECHNOLOGY_EXTRACTION_TEMPLATE,
    DOCUMENT_EXTRACTION_TEMPLATE,
    APPLICATION_EXTRACTION_TEMPLATE
)

# --- 配置日志 (已精简) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# --- 模型和数据路径配置 ---
MODEL_PATH = os.path.expanduser('~/Qwen3-4B')
INPUT_DIR = "../../data/raw/overview/json"  # 存放包含 JSON 列表的文件的目录

# *** (修改) 映射表现在按文件输出到此目录 ***
MAP_OUTPUT_DIR = "../../data/extraction_map"

# *** (新配置) 实体 JSON 文件的输出路径 ***
ENTITY_OUTPUT_DIR = "../../data/entity"
CONCEPT_OUTPUT_FILE = os.path.join(ENTITY_OUTPUT_DIR, "concept.json")
TECHNOLOGY_OUTPUT_FILE = os.path.join(ENTITY_OUTPUT_DIR, "technology.json")
DOCUMENT_OUTPUT_FILE = os.path.join(ENTITY_OUTPUT_DIR, "document.json")
APPLICATION_OUTPUT_FILE = os.path.join(ENTITY_OUTPUT_DIR, "application.json")


def load_qwen_model(model_path: str):
    """
    从指定路径加载 Qwen3-4B 模型和分词器。
    """
    logging.info(f"正在从以下路径加载 Qwen3-4B 模型: {model_path}...")

    if not os.path.exists(model_path):
        logging.error(f"模型路径未找到: {model_path}")
        logging.error("请确保模型权重已正确下载到 '~/Qwen3-4B'")
        return None, None, None

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"正在使用设备: {device}")

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.bfloat16,
            device_map="auto"
        )

        logging.info(f"模型和分词器加载成功。")
        return model, tokenizer, device

    except Exception as e:
        logging.error(f"加载模型时出错: {e}")
        return None, None, None


def call_my_4b_model(prompt_text: str, model, tokenizer, device: str) -> str:
    """
    使用加载的 Qwen3-4B 模型实例执行 Prompt。
    """
    if not model or not tokenizer:
        logging.error("模型或分词器未加载。")
        return "[]"

    # (日志已移除) logging.info(f"正在调用 Qwen3-4B ...")

    messages = [
        {"role": "system",
         "content": "You are a helpful assistant that strictly follows formatting instructions and only returns valid JSON lists."},
        {"role": "user", "content": prompt_text}
    ]

    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # <-- *** (修改 2) 关闭 Qwen 思考模式 ***
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        # 3. 生成响应
        generated_ids = model.generate(
            model_inputs.input_ids,
            max_new_tokens=2048,  # <-- *** (修改) token 限制已更新为 2048 ***
            pad_token_id=tokenizer.eos_token_id
        )

        response_ids = generated_ids[0][model_inputs.input_ids.shape[1]:]
        response_text = tokenizer.decode(response_ids, skip_special_tokens=True)

        # *** (修改) 输出完整的模型响应 ***
        logging.info(f"模型原始响应: {response_text}")

        json_start = response_text.find('[')
        json_end = response_text.rfind(']')

        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end + 1]
            try:
                json.loads(json_str)
                logging.debug("成功解析模型返回的 JSON。")  # (精简日志) 改为 debug 级别
                return json_str
            except json.JSONDecodeError:
                logging.warning(f"模型输出疑似JSON但解析失败。响应: {response_text}")
                return "[]"
        else:
            logging.warning(f"模型未返回有效的 JSON 列表。响应: {response_text}")
            return "[]"

    except Exception as e:
        logging.error(f"模型生成过程中发生错误: {e}")
        return "[]"


def process_single_chunk(chunk_data: dict, model, tokenizer, device: str) -> tuple[dict, dict] | tuple[None, None]:
    """
    处理单个文字块字典：
    1. 提取 'id' 和 'content'。
    2. 调用4次LLM进行抽取。
    3. 构建并返回 (ID到名称的映射, 完整的实体字典)。
    """
    chunk_id = chunk_data.get("id")
    content = chunk_data.get("content")

    if not chunk_id or not content:
        logging.warning(f"跳过一个文字块: 缺少 'id' 或 'content' 字段。")
        return None, None

    logging.info(f"--- 正在处理文字块: {chunk_id} ---")

    # 1. ID 到 Name 的映射 (用于 extraction_map.json)
    extraction_map_entry = {
        "id": chunk_id,
        "concept": [],
        "technology": [],
        "document": [],
        "application": []
    }

    # 2. 完整的实体对象 (用于 data/entity/*.json)
    full_entities_from_chunk = {
        "concept": [],
        "technology": [],
        "document": [],
        "application": []
    }

    extraction_tasks = {
        "concept": (CONCEPT_EXTRACTION_TEMPLATE, "name"),
        "technology": (TECHNOLOGY_EXTRACTION_TEMPLATE, "name"),
        "document": (DOCUMENT_EXTRACTION_TEMPLATE, "title"),
        "application": (APPLICATION_EXTRACTION_TEMPLATE, "name")
    }

    for entity_type, (template, name_field) in extraction_tasks.items():
        logging.info(f"  > [块: {chunk_id}] 正在抽取 {entity_type}...")  # (精简日志)

        prompt_text = template.format(content=content)

        try:
            response_str = call_my_4b_model(prompt_text, model, tokenizer, device)
            extracted_entities = json.loads(response_str)  # <-- 这是完整的实体列表

            # *** (新) 存储完整的实体列表 ***
            full_entities_from_chunk[entity_type] = extracted_entities

            entity_names = []
            for entity in extracted_entities:
                name = entity.get(name_field)
                if name:
                    entity_names.append(name)
                else:
                    logging.warning(f"  > 在 {chunk_id} 的 {entity_type} 实体中未找到 '{name_field}' 字段。")

            extraction_map_entry[entity_type] = entity_names
            logging.info(f"  > [块: {chunk_id}] 成功提取 {len(entity_names)} 个 {entity_type}。")  # (精简日志)

        except json.JSONDecodeError:
            logging.error(f"  > 严重错误: LLM 为 {entity_type} (块: {chunk_id}) 返回了无效的 JSON。")
            logging.error(f"  > 模型返回: {response_str}")
        except Exception as e:
            logging.error(f"  > 处理 {entity_type} (块: {chunk_id}) 时发生未知错误: {e}")

    return extraction_map_entry, full_entities_from_chunk


# *** (修改 1) 新增辅助函数，用于安全地追加实体到 JSON 列表文件 ***
def _append_entities_to_file(filepath: str, new_entities: list):
    """
    Helper function to read a JSON list from a file, append new entities,
    and write the result back.
    """
    if not new_entities:  # 如果没有新实体要添加，则不执行任何操作
        return

    existing_entities = []
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_entities = json.load(f)
                if not isinstance(existing_entities, list):
                    logging.warning(f"文件 {filepath} 不包含一个 JSON 列表。正在覆盖。")
                    existing_entities = []
        except json.JSONDecodeError:
            logging.warning(f"文件 {filepath} 包含无效的 JSON。正在覆盖。")
            existing_entities = []
        except Exception as e:
            logging.error(f"读取实体文件 {filepath} 时出错: {e}。正在覆盖。")
            existing_entities = []

    existing_entities.extend(new_entities)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_entities, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"无法将追加的实体写入 {filepath}: {e}")


# (已删除) setup_dummy_files 函数


def main():
    """
    主执行函数：加载模型，遍历文件，遍历文件中的文字块，执行抽取，保存结果。
    """

    logging.info("加载真实模型...")
    model, tokenizer, device = load_qwen_model(MODEL_PATH)
    if not model or not tokenizer:
        logging.error("模型加载失败，程序退出。")
        return

    # (已删除) 全局实体列表 (all_concepts_list 等)

    logging.info(f"开始从 {INPUT_DIR} 目录处理文件...")

    if not os.path.exists(INPUT_DIR):
        logging.error(f"输入目录未找到: {INPUT_DIR}。请创建该目录并放入您的 JSON 文件。")
        return

    # (修改 1) 为映射表创建输出目录
    os.makedirs(MAP_OUTPUT_DIR, exist_ok=True)
    # (修改 1) 确保实体目录存在
    os.makedirs(ENTITY_OUTPUT_DIR, exist_ok=True)

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(INPUT_DIR, filename)
            logging.info(f"正在打开文件: {file_path}")  # (精简日志)

            # (修改 1) 为当前文件创建单独的映射表列表
            full_extraction_map_for_this_file = []

            # *** (修改 1) 为当前文件创建实体缓存 ***
            file_concepts_list = []
            file_technologies_list = []
            file_documents_list = []
            file_applications_list = []

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 将文件内容解析为 JSON 列表
                    chunks_list = json.load(f)

                    if not isinstance(chunks_list, list):
                        logging.error(f"  > 文件 {filename} 的内容不是一个 JSON 列表。跳过此文件。")
                        continue

                # (已删除) logging.info(f"  > 文件 {filename} 中找到 ...")

                # 遍历文件中的每一个文字块
                for chunk_data in chunks_list:
                    # (已修改) 接收两个返回值
                    map_entry, full_entities = process_single_chunk(chunk_data, model, tokenizer, device)

                    if map_entry and full_entities:
                        # 1. 添加到 *当前文件* 的 ID-Name 映射表
                        full_extraction_map_for_this_file.append(map_entry)

                        # 2. *** (修改 1 & 3) 添加到 *当前文件* 的实体缓存 (不去重) ***
                        file_concepts_list.extend(full_entities["concept"])
                        file_technologies_list.extend(full_entities["technology"])
                        file_documents_list.extend(full_entities["document"])
                        file_applications_list.extend(full_entities["application"])

            except json.JSONDecodeError:
                logging.error(f"  > 无法解析文件 {filename} 的 JSON。跳过此文件。")
            except Exception as e:
                logging.error(f"  > 处理文件 {filename} 时发生未知错误: {e}")

            # ----------------------------------------------------
            # *** (修改 1) 将此文件的实体追加到主实体文件 ***
            # ----------------------------------------------------
            logging.info(f"正在将文件 {filename} 的实体追加到主文件...")

            _append_entities_to_file(CONCEPT_OUTPUT_FILE, file_concepts_list)
            _append_entities_to_file(TECHNOLOGY_OUTPUT_FILE, file_technologies_list)
            _append_entities_to_file(DOCUMENT_OUTPUT_FILE, file_documents_list)
            _append_entities_to_file(APPLICATION_OUTPUT_FILE, file_applications_list)
            # 缓存 (file_..._list) 在下一次循环开始时自动“清空”(被重新初始化)

            # ----------------------------------------------------
            # (修改 1) 保存当前文件的 ID-Name 映射表
            # ----------------------------------------------------
            if full_extraction_map_for_this_file:  # 仅当此文件有内容时才保存
                try:
                    map_output_path = os.path.join(MAP_OUTPUT_DIR, filename)
                    with open(map_output_path, 'w', encoding='utf-8') as f:
                        json.dump(full_extraction_map_for_this_file, f, ensure_ascii=False, indent=4)

                    # (修改) 只 print 映射表路径
                    print(f"映射表已保存到: {map_output_path}")

                except Exception as e:
                    logging.error(f"无法写入映射文件 {map_output_path}: {e}")

    # ----------------------------------------------------
    # *** (修改 1) 旧的、统一的实体保存逻辑已被移除 ***
    # ----------------------------------------------------
    logging.info(f"所有文件处理完毕。")


if __name__ == "__main__":
    if not os.path.exists("prompt.py"):
        print("错误： 'prompt.py' 文件未找到。请先创建该文件。")
    else:
        main()

