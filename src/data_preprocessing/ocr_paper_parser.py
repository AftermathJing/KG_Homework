import os
import re
import json

# --- 配置项 ---

# 4. 单个文字块的最大字符长度（用于正文分割）
MAX_CONTENT_LENGTH = 300

# 4. 识别为“标题”的最大字符长度
# 如果发现标题被错误地识别为正文，您可以适当调高此值。
MAX_TITLE_LENGTH = 15


# --- 辅助函数 ---

def generate_id(prefix, counter):
    """生成唯一的、带前缀的ID"""
    return f"{prefix}_{counter}"


def clean_text(text):
    """
    清理文本块：
    1. 替换所有连续的空白字符（包括换行、制表符）为单个空格。
    2. 移除中文汉字（及全角标点）之间的多余空格（保留英文单词间的空格）。
    3. 移除开头和结尾的空格。
    """
    if not text:
        return ""

    # 1. 替换所有连续的空白字符（包括换行、制表符）为单个空格
    text = re.sub(r'\s+', ' ', text)

    # 2. 移除中文汉字（及全角标点）之间的空格
    # \u4e00-\u9fff 是汉字
    # \u3000-\u303f 是 CJK 标点
    # \uff01-\uff0f, \uff1a-\uff20, \uff3b-\uff40, \uff5b-\uff65 是特定的全角标点范围
    # (此规则排除了全角字母 \uff21-\uff3a, \uff41-\uff5a)
    text = re.sub(
        r'([\u4e00-\u9fff\u3000-\u303f\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65])\s+(?=[\u4e00-\u9fff\u3000-\u303f\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65])',
        r'\1', text)

    # 3. 移除开头和结尾的空格
    return text.strip()


def split_content_block(text_block, max_length):
    """
    将一个长文本块（已清理）按照句子分割成多个不超过max_length的子块。
    """
    # 如果文本块本身未超长，直接返回
    if len(text_block) <= max_length:
        return [text_block]

    # 1. 按照句子结束符分割，并保留结束符
    # 使用正则表达式的捕获组 re.split(r'([delimiter])', text)
    # 这会将 'a.b' 分割为 ['a', '.', 'b']
    parts = re.split(r'([。？！.!?．])', text_block)

    sentences = []
    # 2. 将句子和它的结束符重新组合
    for i in range(0, len(parts) - 1, 2):
        sentence = (parts[i] + parts[i + 1]).strip()
        if sentence:
            sentences.append(sentence)

    # 3. 添加可能遗漏的最后一部分（如果没有结束符）
    if len(parts) % 2 == 1 and parts[-1].strip():
        sentences.append(parts[-1].strip())

    # 4. 如果没有找到句子（例如，一块没有标点的文本），则进行硬分割
    if not sentences:
        return [text_block[i:i + max_length] for i in range(0, len(text_block), max_length)]

    # 5. 按顺序拼接句子，直到达到max_length
    output_blocks = []
    current_block = ""
    for sentence in sentences:
        if not current_block:
            current_block = sentence
        # 检查（当前块 + 1个空格 + 下一句）是否超长
        elif len(current_block) + 1 + len(sentence) <= max_length:
            current_block += " " + sentence  # 用空格连接句子
        else:
            # 当前块已满，保存它
            output_blocks.append(current_block)
            # 启动新块
            current_block = sentence

    # 6. 添加最后一个未满的块
    if current_block:
        output_blocks.append(current_block)

    return output_blocks


def save_json(data, filepath):
    """将数据保存为JSON文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存JSON文件时出错 {filepath}: {e}")
        return False


def parse_paper_txt(input_filepath, output_dir):
    """
    主解析函数
    """
    print(f"开始处理文件: {input_filepath}")

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except FileNotFoundError:
        print(f"错误：文件未找到 {input_filepath}")
        return
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 1. 获取文件名作为ID前缀
    filename = os.path.basename(input_filepath)
    prefix = os.path.splitext(filename)[0]

    paper_info_references = []
    abstract_main_body = []
    global_id_counter = 1

    # 2. 定义四大块的正则表达式
    # 使用 re.DOTALL 使 . 匹配换行符
    # 使用非贪婪匹配 .*?
    # 添加 (?=...) 正向先行断言，以确保我们能正确处理部分缺失的文本块
    section_patterns = {
        "info": r"<论文信息>(.*?)($|<摘要>|<正文>|<参考文献>)",
        "abstract": r"<摘要>(.*?)($|<正文>|<参考文献>)",
        "main_body": r"<正文>(.*?)($|<参考文献>)",
        "references": r"<参考文献>(.*)($)"
    }

    # --- 3. 处理 <论文信息> ---
    match = re.search(section_patterns["info"], full_text, re.DOTALL)
    if match:
        content = clean_text(match.group(1))
        if content:
            record = {
                "id": generate_id(prefix, global_id_counter),
                "topic": "论文信息",
                "content": content
            }
            paper_info_references.append(record)
            global_id_counter += 1
        print("处理完成：论文信息")

    # --- 4. 处理 <摘要> ---
    match = re.search(section_patterns["abstract"], full_text, re.DOTALL)
    if match:
        content = clean_text(match.group(1))
        if content:
            record = {
                "id": generate_id(prefix, global_id_counter),
                "topic": "摘要",
                "content": content
            }
            abstract_main_body.append(record)
            global_id_counter += 1
        print("处理完成：摘要")

    # --- 5. 处理 <正文> ---
    match = re.search(section_patterns["main_body"], full_text, re.DOTALL)
    if match:
        main_body_content = match.group(1).strip()

        # 识别所有可能的标题行 (基于规则：以数字或(数字开头)
        # re.MULTILINE 使 ^ 匹配每行的开头
        TITLE_REGEX_FIND = re.compile(r'^\s*([（\(]?\d[\d\.]*[\s）\)]?.*)$', re.MULTILINE)

        titles = []
        for m in TITLE_REGEX_FIND.finditer(main_body_content):
            title_text = m.group(0).strip()  # 获取完整的标题行文本

            # 应用长度限制规则
            if len(title_text) <= MAX_TITLE_LENGTH:
                # 存储 (标题文本, 标题开始位置, 标题结束位置)
                titles.append((title_text, m.start(), m.end()))

        default_topic = "正文"  # 用于存放第一个标题前的引言内容

        if not titles:
            # 5.1 如果未找到任何标题，将整个正文视为一个块
            cleaned_block = clean_text(main_body_content)
            if cleaned_block:
                split_blocks = split_content_block(cleaned_block, MAX_CONTENT_LENGTH)
                for block in split_blocks:
                    record = {"id": generate_id(prefix, global_id_counter), "topic": default_topic, "content": block}
                    abstract_main_body.append(record)
                    global_id_counter += 1
        else:
            # 5.2 处理第一个标题之前的引言内容
            pre_title_content = main_body_content[0:titles[0][1]].strip()
            if pre_title_content:
                cleaned_block = clean_text(pre_title_content)
                split_blocks = split_content_block(cleaned_block, MAX_CONTENT_LENGTH)
                for block in split_blocks:
                    record = {"id": generate_id(prefix, global_id_counter), "topic": default_topic, "content": block}
                    abstract_main_body.append(record)
                    global_id_counter += 1

            # 5.3 循环处理每个标题和它对应的正文
            for i in range(len(titles)):
                topic_text, title_start, title_end = titles[i]

                # 正文内容开始于标题行之后
                content_start = title_end

                # 正文内容结束于下一个标题行之前，或者是整个正文的末尾
                content_end = titles[i + 1][1] if (i + 1) < len(titles) else len(main_body_content)

                # 提取原始正文块
                content_block_raw = main_body_content[content_start:content_end].strip()

                if content_block_raw:
                    # 清理并分割
                    cleaned_block = clean_text(content_block_raw)
                    split_blocks = split_content_block(cleaned_block, MAX_CONTENT_LENGTH)
                    for block in split_blocks:
                        record = {"id": generate_id(prefix, global_id_counter), "topic": topic_text, "content": block}
                        abstract_main_body.append(record)
                        global_id_counter += 1
        print(f"处理完成：正文 (共 {len(titles)} 个小节)")

    # --- 6. 处理 <参考文献> ---
    match = re.search(section_patterns["references"], full_text, re.DOTALL)
    if match:
        references_content = match.group(1).strip()
        lines = references_content.split('\n')

        ref_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 规则：以数字或[数字]开头 (支持全角/半角)
            # [\[［]? 匹配半角 [ 或全角 ［
            # ([\d\uFF10-\uFF19]+) 匹配半角数字 0-9 或全角数字 ０-９
            # [\]］]? 匹配半角 ] 或全角 ］
            ref_match = re.match(r'^\s*[\[［]?\s*([\d\uFF10-\uFF19]+)\s*[\]］]?', line)

            ref_number = "未知"
            if ref_match:
                # 获取匹配到的数字（可能是全角）
                full_width_num = ref_match.group(1)
                # 将全角数字转换为半角
                ref_number = full_width_num.translate(str.maketrans('０１２３４５６７８９', '0123456789'))

            topic = f"参考文献[{ref_number}]"
            content = clean_text(line)  # 清理整行

            record = {
                "id": generate_id(prefix, global_id_counter),
                "topic": topic,
                "content": content
            }
            paper_info_references.append(record)
            global_id_counter += 1
            ref_count += 1
        print(f"处理完成：参考文献 (共 {ref_count} 条)")

    # --- 7. 保存文件 ---
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    info_ref_path = os.path.join(output_dir, f"{prefix}_info_references.json")
    abstract_main_path = os.path.join(output_dir, f"{prefix}_abstract_main_body.json")

    if save_json(paper_info_references, info_ref_path):
        print(f"成功保存：{info_ref_path}")
    if save_json(abstract_main_body, abstract_main_path):
        print(f"成功保存：{abstract_main_path}")


# --- 运行示例 ---
if __name__ == "__main__":
    TEST_TXT_FILENAME = "./data/raw/overview/txt/cn_4_fulltext.txt"
    TEST_OUTPUT_DIR = "./data/raw/overview/json"

    # 运行解析器
    parse_paper_txt(TEST_TXT_FILENAME, TEST_OUTPUT_DIR)