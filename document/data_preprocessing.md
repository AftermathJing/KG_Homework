# **PDF 论文批量解析工具**

本项目使用 Python 和 unstructured 库来批量解析 PDF 论文，根据要求提取正文内容、按粒度分块，并分离参考文献。

## **安装依赖**

本项目依赖 Python 库和一些系统工具。

### **1\. Python 库**

您需要安装 requirements.txt 文件中列出的库。

\# 建议在虚拟环境中运行  
python \-m venv venv  
source venv/bin/activate  \# (Windows: venv\\Scripts\\activate)

\# 安装所有必需的 Python 库  
\# (如果已安装，请再次运行以添加 pi\_heif)  
pip install \-r requirements.txt

**注意**: 如果您遇到了 ModuleNotFoundError: No module named 'pi\_heif' 错误，请确保您的 requirements.txt 文件中包含了 pi\_heif 这一行，然后重新运行 pip install \-r requirements.txt。

### **2\. 系统依赖 (重要)**

unstructured 库在处理 PDF 时，依赖一些外部工具：

* **poppler**: 用于将 PDF 页面转换为图像（unstructured 在某些策略中需要）。  
* **tesseract-ocr**: 用于光学字符识别（OCR），以处理扫描版的 PDF。

**在 macOS 上安装:**

brew install poppler  
brew install tesseract

**在 Ubuntu/Debian 上安装:**

sudo apt-get update  
sudo apt-get install \-y poppler-utils  
sudo apt-get install \-y tesseract-ocr

**在 Windows 上安装:**

1. Poppler (推荐: 使用 Conda)  
   如果您正在使用 Anaconda/Miniconda (如您的 KG\_homework 环境)，最简单的方法是使用 conda 安装：  
   conda install \-c conda-forge poppler

   * **故障排除**: 如果您在安装时遇到 CondaVerificationError (例如 libboost 包损坏，如您所见)，这通常是由于 conda 缓存损坏。  
   * **修复**: 运行 conda clean \--packages \--tarballs 清理缓存，然后重新尝试 conda install \-c conda-forge poppler。  
2. **Tesseract**: [下载地址](https://github.com/tesseract-ocr/tessdoc)。安装时，**请确保勾选“添加中文语言包”**，并将 Tesseract 的安装路径（例如 C:\\Program Files\\Tesseract-OCR）添加到 PATH 环境变量。  
   * **Tesseract 语言包 (重要)**: 如果您在安装 Tesseract 时忘记安装中文包，或者您使用的是 conda install tesseract，您**必须**手动下载 chi\_sim.traineddata 文件 (来自 [tessdata\_fast repo](https://github.com/tesseract-ocr/tessdata_fast)) 并将其放入 Tesseract 的 tessdata 文件夹中。

## **运行脚本**

1. 确保您的 PDF 文件放在 ../data/raw/overview\_pdf 目录下。  
2. 确保 process\_papers.py 和 requirements.txt 在同一目录。  
3. **（重要）** 检查 process\_papers.py 顶部的全局配置，特别是 PROCESS\_GRANULARITY（分块粒度）是否符合您的需求。  
4. 运行脚本：

python process\_papers.py

## **输出说明**

脚本会根据 PROCESS\_GRANULARITY 的配置，在 ../data/raw/overview 目录中生成：

1. **\*\_sentences.json** (当 PROCESS\_GRANULARITY \= "sentence" 或 "all")  
   * **粒度**: "一句一段"。  
   * **格式**: **标准 JSON** 列表 (\[{"id": "sent\_1", "relation": "...", "content": "..."}, ...\])。  
2. **\*\_sections.json** (当 PROCESS\_GRANULARITY \= "section" 或 "all")  
   * **粒度**: "一个小结一段"。  
   * **格式**: **标准 JSON** 列表 (\[{"id": "sec\_1", "relation": "...", "content": "..."}, ...\])。  
3. **\*\_references.txt**  
   * **粒度**: 参考文献。  
   * **格式**: 纯文本文件，每行一条参考文献。

### **关于布局识别 (规则 7\)**

脚本中 strategy="fast" 模式对单栏和双栏有较好的自动检测。如果发现解析效果不佳（例如文本顺序混乱），您可以尝试 strategy="hi\_res"（高分辨率策略）。

**注意**: strategy="hi\_res" 需要 unstructured\[local-inference\]，这会安装 PyTorch 和 Detectron2，依赖项非常庞大且复杂。

\# 如果需要，可以尝试安装  
pip install "unstructured\[local-inference\]"

## **论文OCR TXT 清理脚本使用说明**

### **1\. 准备**

1. **安装 Python:** 确保您的计算机上安装了 Python 3 (推荐 3.6 或更高版本)。  
2. **保存脚本:** 将上面的代码块保存为 process\_paper\_ocr.py 文件。

### **2\. 运行脚本**

1. **准备 .txt 文件:** 将您通过 OCR 识别的 .txt 文件（例如，mypaper.txt）放在与 process\_paper\_ocr.py 相同的目录中，或者您知道它的完整路径。  
2. **打开终端:** 打开您的命令行工具（例如 Windows 上的 CMD 或 PowerShell，macOS 或 Linux 上的 Terminal）。  
3. **运行命令:**  
   * 如果您想使用脚本中自带的 if \_\_name\_\_ \== "\_\_main\_\_": 示例来测试功能，您可以直接运行：  
     python process\_paper\_ocr.py

     这将自动创建一个 cn\_1\_fulltext.txt 示例文件，并生成 output\_json 文件夹，内含两个 json 结果文件。  
   * 处理您自己的文件:  
     您需要稍微修改脚本的最后几行。删除或注释掉 if \_\_name\_\_ \== "\_\_main\_\_": 块内的所有示例代码，并替换为对您自己文件的调用：  
     if \_\_name\_\_ \== "\_\_main\_\_":  
         \# \--- 处理您自己的文件 \---

         \# 1\. 设置您的输入文件路径  
         YOUR\_INPUT\_FILE \= "path/to/your/mypaper.txt" 

         \# 2\. 设置您希望的输出目录  
         YOUR\_OUTPUT\_DIR \= "my\_paper\_output"

         \# 3\. 运行解析器  
         parse\_paper\_txt(YOUR\_INPUT\_FILE, YOUR\_OUTPUT\_DIR)

         \# \--- 示例代码（请删除或注释掉）---  
         \# TEST\_TXT\_FILENAME \= "cn\_1\_fulltext.txt"  
         \# ... (以下全部删除或注释)

     修改后，像这样运行：  
     python process\_paper\_ocr.py

### **3\. 查看结果**

脚本运行后，您将在指定的输出目录（例如 my\_paper\_output）中找到两个 JSON 文件：

1. {文件名}\_info\_references.json: 包含\<论文信息\>和\<参考文献\>的内容。  
2. {文件名}\_abstract\_main\_body.json: 包含\<摘要\>和\<正文\>的内容（正文已按小节和长度分割）。

### **4\. 调整配置（可选）**

如果您发现解析效果不佳，可以打开 process\_paper\_ocr.py 文件，修改头部的配置项：

* MAX\_CONTENT\_LENGTH \= 300: 如果您希望正文的文字块更长或更短，请修改这个数字。  
* MAX\_TITLE\_LENGTH \= 15: 如果您发现某些较长的标题（例如超过15个字）没有被正确识别为标题，您可以适当**调高**这个数字（例如改为 25 或 30）。