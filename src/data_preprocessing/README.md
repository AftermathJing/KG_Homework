# PDF 论文批量解析工具

本项目使用 Python 和 unstructured 库来批量解析 PDF 论文，根据要求提取正文内容、按粒度分块，并分离参考文献。

使用ocr提取的效果可能并不好,可以将其转化为txt为文件后使用ocr_paper_parser.py文件识别,识别前请将文件的文件详情,摘要,正文,参考文献使用<>单标签界定
## 安装依赖

本项目依赖 Python 库和一些系统工具。

### 1. Python 库

您需要安装 requirements.txt 文件中列出的库。

```
# 建议在虚拟环境中运行
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
```

```
# 安装所有必需的 Python 库
pip install -r requirements.txt
```

### 2. 系统依赖 (重要)

unstructured 库在处理 PDF 时，依赖一些外部工具：

poppler: 用于将 PDF 页面转换为图像（unstructured 在某些策略中需要）。

tesseract-ocr: 用于光学字符识别（OCR），以处理扫描版的 PDF。

**在 macOS 上安装:**

brew install poppler
brew install tesseract



**在 Ubuntu/Debian 上安装:**

sudo apt-get update
sudo apt-get install -y poppler-utils
sudo apt-get install -y tesseract-ocr



**在 Windows 上安装:**

Poppler (推荐: 使用 Conda)
如果您正在使用 Anaconda/Miniconda (如您的 KG_homework 环境)，最简单的方法是使用 conda 安装：

conda install -c conda-forge poppler


**故障排除:** 如果您在安装时遇到 CondaVerificationError (例如 libboost 包损坏，如您所见)，这通常是由于 conda 缓存损坏。

修复: 运行 conda clean --packages --tarballs 清理缓存，然后重新尝试 conda install -c conda-forge poppler。

Tesseract: 安装时，请确保勾选“添加中文语言包”，并将 Tesseract 的安装路径（例如 C:\Program Files\Tesseract-OCR）添加到 PATH 环境变量。

Tesseract 语言包 (重要): 如果您在安装 Tesseract 时忘记安装中文包，或者您使用的是 conda install tesseract，您必须手动下载 chi_sim.traineddata 文件 (来自 tessdata_fast repo) 并将其放入 Tesseract 的 tessdata 文件夹中。

## 运行脚本

1. 确保您的 PDF 文件放在 ../data/raw/overview_pdf 目录下。

2. 确保 process_papers.py 和 requirements.txt 在同一目录。

3. （重要） 检查 process_papers.py 顶部的全局配置，特别是 PROCESS_GRANULARITY（分块粒度）是否符合您的需求。

4. 运行脚本：

    `python process_papers.py`

## 输出说明

脚本会根据 PROCESS_GRANULARITY 的配置，在 ../data/raw/overview 目录中生成：

1. *_sentences.json (当 PROCESS_GRANULARITY = "sentence" 或 "all")

    粒度: "一句一段"。

    格式: 标准 JSON 列表 ([{"id": "sent_1", "relation": "...", "content": "..."}, ...])。

2. *_sections.json (当 PROCESS_GRANULARITY = "section" 或 "all")

    粒度: "一个小结一段"。

    格式: 标准 JSON 列表 ([{"id": "sec_1", "relation": "...", "content": "..."}, ...])。

3. *_references.txt

    粒度: 参考文献。

    格式: 纯文本文件，每行一条参考文献。

## 关于布局识别

脚本中 strategy="fast" 模式对单栏和双栏有较好的自动检测。如果发现解析效果不佳（例如文本顺序混乱），您可以尝试 strategy="hi_res"（高分辨率策略）。

注意: strategy="hi_res" 需要 unstructured[local-inference]，这会安装 PyTorch 和 Detectron2，依赖项非常庞大且复杂。

`# 如果需要，可以尝试安装
pip install "unstructured[local-inference]"`
