import os
import json
import re
import nltk
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    CompositeElement,
    Text,
    Title,
    NarrativeText,
    ListItem,
    Header,
    Footer,
    PageNumber,
    Table,
    FigureCaption,
)

# --- 全局配置 ---

# 1. 路径配置
INPUT_DIR = "../../data/raw/overview/pdf"
OUTPUT_DIR = "../../data/raw/overview/txt"

# 2. 丢弃过短的文字块
MIN_CHUNK_LENGTH = 20

# 3. 分块粒度配置
PROCESS_GRANULARITY = "section"  # "sentence", "section", "all"

# 4. 参考文献关键词
REFERENCE_KEYWORDS = ["references", "参考文献"]

# 5. OCR 语言配置
OCR_LANGUAGES = ["chi_sim", "eng"]

# 6. (新功能) 是否保存完整的 .txt 文本
SAVE_FULL_TEXT = True


# -----------------

def clean_text(text: str) -> str:
    """
    4. 文字块中的行换行符等特殊符号全部删除
    """
    # 将多个空白字符（包括换行符、制表符）替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    """
    使用 NLTK 将文本块分割为句子
    """
    try:
        return nltk.sent_tokenize(text)
    except LookupError:
        print("正在下载 NLTK 'punkt' 标记器...")
        nltk.download('punkt')
        return nltk.sent_tokenize(text)


def process_pdf(pdf_path: str, base_name: str, output_dir: str):
    """
    处理单个 PDF 文件
    """
    print(f"--- 正在处理: {base_name}.pdf ---")

    try:
        elements = partition_pdf(
            pdf_path,
            strategy="fast",
            infer_table_structure=False,
            languages=OCR_LANGUAGES
        )
    except Exception as e:
        print(f"处理 {base_name}.pdf 时出错: {e}")
        return

    # 存储不同粒度的分块
    json_data_sentence = []  # 粒度1: 一句一段
    json_data_section = []  # 粒度2: 一个小结一段
    references_content = []  # 5. 参考文献

    # (新功能) 存储所有文本
    full_text_content = []

    current_heading = "Unknown"
    current_section_texts = []

    sentence_id = 1
    section_id = 1
    is_ref_section = False

    for el in elements:

        # --- 2. 页眉、页脚、图、表均不识别 ---
        if isinstance(el, (Header, Footer, PageNumber, Table, FigureCaption)):
            continue

        text = clean_text(str(el))

        # --- 4. 丢弃过短的文字块 ---
        if not text or len(text) < MIN_CHUNK_LENGTH:
            continue

        # --- (新功能) 将所有清理过的文本添加到完整列表 ---
        # 这一步在所有其他逻辑之前，确保捕捉所有内容
        if SAVE_FULL_TEXT:
            full_text_content.append(text)

        # --- 5. 参考文献处理 ---
        if isinstance(el, Title) and any(keyword in text.lower() for keyword in REFERENCE_KEYWORDS):
            is_ref_section = True
            if len(text) < 30:  # 假设标题不会太长
                # 结算上一章节
                if current_section_texts:
                    section_content = " ".join(current_section_texts)
                    json_data_section.append({
                        "id": f"sec_{section_id}",
                        "relation": current_heading,
                        "content": section_content
                    })
                    section_id += 1
                current_heading = text
                current_section_texts = []
                continue

        if is_ref_section:
            references_content.append(text)
            continue

        # --- 3. & 6. 提取内容分块 ---

        # (A) 处理小结标题 (Title)
        if isinstance(el, Title):
            if current_section_texts:
                section_content = " ".join(current_section_texts)
                json_data_section.append({
                    "id": f"sec_{section_id}",
                    "relation": current_heading,
                    "content": section_content
                })
                section_id += 1

            current_heading = text
            current_section_texts = []

        # (B) 处理正文 (NarrativeText, ListItem, Text)
        elif isinstance(el, Text):
            current_section_texts.append(text)

            sentences = split_into_sentences(text)
            for sentence in sentences:
                cleaned_sentence = sentence.strip()
                if len(cleaned_sentence) >= MIN_CHUNK_LENGTH:
                    json_data_sentence.append({
                        "id": f"sent_{sentence_id}",
                        "relation": current_heading,
                        "content": cleaned_sentence
                    })
                    sentence_id += 1

    # --- 循环结束后，保存最后一个小结的内容 ---
    if current_section_texts and not is_ref_section:
        section_content = " ".join(current_section_texts)
        json_data_section.append({
            "id": f"sec_{section_id}",
            "relation": current_heading,
            "content": section_content
        })

    # --- 存储结果 ---

    # 存储 "一句一段" 的结果
    if PROCESS_GRANULARITY in ("sentence", "all") and json_data_sentence:
        json_path_sent = os.path.join(output_dir, f"{base_name}_sentences.json")
        with open(json_path_sent, 'w', encoding='utf-8') as f:
            json.dump(json_data_sentence, f, ensure_ascii=False, indent=4)
        print(f"  已保存 (句子粒度): {json_path_sent}")

    # 存储 "一个小结一段" 的结果
    if PROCESS_GRANULARITY in ("section", "all") and json_data_section:
        json_path_sect = os.path.join(output_dir, f"{base_name}_sections.json")
        with open(json_path_sect, 'w', encoding='utf-8') as f:
            json.dump(json_data_section, f, ensure_ascii=False, indent=4)
        print(f"  已保存 (小结粒度): {json_path_sect}")

    # --- 5. 存储参考文献 ---
    if references_content:
        ref_path = os.path.join(output_dir, f"{base_name}_references.txt")
        with open(ref_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(references_content))
        print(f"  已保存 (参考文献): {ref_path}")

    # --- (新功能) 6. 存储完整文章 ---
    if SAVE_FULL_TEXT and full_text_content:
        full_text_path = os.path.join(output_dir, f"{base_name}_fulltext.txt")
        # 使用双换行符分隔不同的元素块，提高可读性
        full_text = "\n\n".join(full_text_content)
        with open(full_text_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"  已保存 (完整文本): {full_text_path}")


def main():
    """
    主函数，遍历输入文件夹并处理所有PDF
    """
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入文件夹不存在: {INPUT_DIR}")
        return

    if not os.path.exists(OUTPUT_DIR):
        print(f"创建输出文件夹: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("首次运行: G正在下载 NLTK 'punkt' 标记器...")
        nltk.download('punkt')

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            base_name = os.path.splitext(filename)[0]

            process_pdf(pdf_path, base_name, OUTPUT_DIR)

    print("\n--- 所有PDF处理完成 ---")


if __name__ == "__main__":
    main()

