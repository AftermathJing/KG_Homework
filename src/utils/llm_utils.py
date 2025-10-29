import os
import json
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- 配置日志 (已精简) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# --- 模型和数据路径配置 ---
MODEL_PATH = os.path.expanduser('~/Qwen3-4B')


def load_qwen_model(model_path: str = MODEL_PATH):
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