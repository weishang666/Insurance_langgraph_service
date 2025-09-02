# PDF保险文档问答生成系统

## 功能介绍

这个系统可以从保险PDF文档中自动提取内容，并使用大模型生成测试问答对。主要用于创建保险知识测评系统，帮助用户检验对保险产品的理解。

## 目录结构

```
test/
├── pdf_to_qa.py       # 核心功能模块：从PDF生成问答对
├── test_pdf_to_qa.py  # 测试脚本：测试单个PDF文件处理
├── README.md          # 使用说明
└── output/            # 输出目录：存储生成的问答对JSON文件
```

## 依赖项

- Python 3.8+
- PyPDF2 (用于PDF文件读取)
- requests (用于API调用)
- 其他项目已有依赖项

## 核心类说明

### PDFToQAGenerator

主要类，提供从PDF生成问答对的功能。

#### 方法

- `__init__()`: 初始化生成器，设置LLM客户端和PDF处理器
- `generate_qa_from_text(text, num_questions=5)`: 从文本生成指定数量的问答对
- `process_single_pdf(pdf_path, output_dir)`: 处理单个PDF文件并保存问答对
- `process_folder(root_folder, output_dir)`: 批量处理文件夹中的所有PDF文件

## 使用方法

### 批量处理文件夹中的PDF文件

```python
from test.pdf_to_qa import PDFToQAGenerator

# 初始化问答生成器
qa_generator = PDFToQAGenerator()

# 定义PDF根目录和输出目录
pdf_root_folder = "D:\data\内部"
output_dir = "d:\BaiduNetdiskDownload\code\langgraph\new\insurance_agent_backendv2\test\output"

# 处理所有PDF文件
success_count = qa_generator.process_folder(pdf_root_folder, output_dir)
print(f"成功处理了 {success_count} 个PDF文件")
```

### 处理单个PDF文件

```python
from test.pdf_to_qa import PDFToQAGenerator

# 初始化问答生成器
qa_generator = PDFToQAGenerator()

# 设置PDF文件路径和输出目录
pdf_path = "D:\data\内部\产品名称\保险文档.pdf"
output_dir = "d:\BaiduNetdiskDownload\code\langgraph\new\insurance_agent_backendv2\test\output\产品名称"

# 处理单个PDF文件
result = qa_generator.process_single_pdf(pdf_path, output_dir)
print(f"处理结果: {'成功' if result else '失败'}")
```

## 运行测试

```bash
python test\test_pdf_to_qa.py
```

> 注意：测试前需要修改`test_pdf_to_qa.py`中的`test_pdf_path`为实际存在的PDF文件路径

## 输出格式

生成的问答对以JSON格式保存，示例：

```json
{
  "file_name": "保险文档.pdf",
  "pdf_path": "D:\data\内部\产品名称\保险文档.pdf",
  "questions": [
    {
      "question": "某保险产品的投保年龄范围是多少？",
      "answer": "出生满28天至65周岁"
    },
    {
      "question": "该保险的保险期间是多久？",
      "answer": "1年"
    }
  ]
}
```

## 配置说明

所有配置都在项目根目录的`config.py`文件中，主要包括：

- `LLM_APP_CODE`: 大模型API认证码
- `LLM_API_URL`: 大模型API地址
- `EMBEDDING_URL`: 嵌入向量API地址
- `EMBEDDING_APP_CODE`: 嵌入向量API认证码

## 注意事项

1. 确保PDF文件路径正确，且系统有权限访问
2. 大模型API需要有效的认证码才能使用
3. 处理大量PDF文件时，可能需要较长时间，请耐心等待
4. 生成的问答对质量取决于PDF文档的清晰度和大模型的能力