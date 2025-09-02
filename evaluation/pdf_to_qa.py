import os
import sys
import json
import re
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from es.pdf_processor import PDFProcessor
from llm_client import LLMClient
from es.pdf_processor import ElasticsearchClient
from config import LLM_APP_CODE, LLM_API_URL, EMBEDDING_URL, EMBEDDING_APP_CODE

class PDFToQAGenerator:
    """从PDF文件生成测试题和问答对的类"""

    def __init__(self):
        """初始化PDFToQAGenerator"""
        # 初始化LLM客户端
        self.llm_client = LLMClient(
            embedding_url=EMBEDDING_URL,
            embedding_appcode=EMBEDDING_APP_CODE,
            llm_url=LLM_API_URL,
            llm_appcode=LLM_APP_CODE,
            model_name="qwen72b"
        )

        # 初始化PDF处理器 (注意：这里不需要Elasticsearch客户端，所以传入None)
        self.pdf_processor = PDFProcessor(es_client=None, llm_client=self.llm_client)

    def split_text(self, text, chunk_size=3000, overlap=500):
        """
        将文本分割成多个块，每个块有指定的大小和重叠部分

        参数:
            text: 输入文本
            chunk_size: 每个块的大小
            overlap: 块之间的重叠大小

        返回:
            文本块列表
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            if end > text_length:
                end = text_length
            chunks.append(text[start:end])
            start += chunk_size - overlap
            if start >= text_length and len(chunks) == 0:
                # 确保至少有一个块
                chunks.append(text)
                break

        return chunks

    def generate_qa_from_text(self, text, product_name, num_questions=5):
        """
        从文本生成问答对

        参数:
            text: 输入文本
            product_name: 产品名称
            num_questions: 生成的问题数量

        返回:
            问答对列表
        """
        # 设计系统提示
        system_prompt = "你是一名保险领域的专家，需要根据提供的保险文档内容生成测试题。"

        # 设计用户提示
        user_prompt = f"请根据以下保险文档内容，生成{num_questions}个测试问题及答案。\n"
        user_prompt += "要求：\n"
        user_prompt += "1. 问题应涵盖文档中的关键信息，如保险责任、投保条件、理赔流程等。\n"
        user_prompt += "2. 问题类型为简答题。\n"
        user_prompt += "3. 每个问题都必须有准确、详细的答案。\n"
        user_prompt += f"4. 每个问题中必须包含产品名称 '{product_name}'。\n"
        user_prompt += "5. 请以JSON格式输出，格式如下：\n"
        user_prompt += "{\"questions\": [{\"question\": \"问题文本\", \"answer\": \"答案文本\"}]}\n\n"
        user_prompt += f"文档内容：{text[:5000]}..."
  # 限制文本长度，避免超出模型上下文

        # 调用大模型生成问答对
        try:
            response = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=3000,
                temperature=0.5
            )
            #print(f"大模型响应: {response}")

            # 解析JSON响应
            if response:
                #print(f"完整大模型响应: {response}")
                # 尝试提取JSON部分
                try:
                    # 查找JSON开始和结束位置
                    start_pos = response.find('{')
                    end_pos = response.rfind('}') + 1
                    if start_pos != -1 and end_pos != -1:
                        json_str = response[start_pos:end_pos]
                        #print(f"提取的JSON字符串: {json_str}")
                        qa_data = json.loads(json_str)
                        print(f"解析后的JSON数据: {qa_data}")
                        if 'questions' not in qa_data:
                            print("大模型响应中没有'questions'字段")
                            return []
                        return qa_data['questions']
                    else:
                        print("无法在响应中找到JSON结构")
                        return []
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"无法解析的JSON字符串: {json_str}")
                    # 尝试使用更宽松的解析方式
                    try:
                        import json5
                        qa_data = json5.loads(json_str)
                        print(f"使用json5解析后的JSON数据: {qa_data}")
                        if 'questions' not in qa_data:
                            print("大模型响应中没有'questions'字段")
                            return []
                        return qa_data['questions']
                    except ImportError:
                        print("未安装json5库，无法使用宽松解析")
                    except Exception as e2:
                        print(f"使用json5解析也失败: {e2}")
                    return []
            else:
                print("大模型生成失败，响应为空")
                return []
        except Exception as e:
            print(f"生成问答对异常: {e}")
            return []

    def process_single_pdf(self, pdf_path, output_dir, product_name=None):
        """
        处理单个PDF文件，生成问答对并保存

        参数:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            product_name: 产品名称（可选，如果未提供则从文件名提取）

        返回:
            成功返回True，失败返回False
        """
        try:
            print(f"处理文件: {pdf_path}")

            # 读取PDF内容
            text = self.pdf_processor.read_pdf(pdf_path)
            if not text:
                print(f"PDF文件 {pdf_path} 没有提取到文本")
                return False

            # 确保使用传入的产品名称，不从文件名提取
            print(f"使用的产品名称: {product_name}")
            # 验证产品名称是否有效
            if not product_name or product_name.lower().endswith('.pdf'):
                print(f"警告: 产品名称 '{product_name}' 可能无效，使用文件夹名称作为备用")
                # 尝试使用父文件夹名称作为产品名称
                parent_folder = os.path.basename(os.path.dirname(pdf_path))
                if parent_folder:
                    product_name = parent_folder

            # 分割文本
            chunks = self.split_text(text, chunk_size=3000, overlap=500)
            print(f"文本分割为 {len(chunks)} 个块")

            all_qa_pairs = []
            # 为每个文本块生成问答对
            for i, chunk in enumerate(chunks):
                print(f"处理文本块 {i+1}/{len(chunks)}")
                qa_pairs = self.generate_qa_from_text(chunk, product_name, num_questions=5)
                print(f"块 {i+1} 生成的问答对数量: {len(qa_pairs)}")
                if qa_pairs:
                    all_qa_pairs.extend(qa_pairs)

            # 去重问答对
            unique_qa_pairs = []
            seen_questions = set()
            for qa in all_qa_pairs:
                if qa['question'] not in seen_questions:
                    seen_questions.add(qa['question'])
                    unique_qa_pairs.append(qa)

            print(f"去重后的问答对数量: {len(unique_qa_pairs)}")
            if not unique_qa_pairs:
                print(f"为PDF文件 {pdf_path} 生成问答对失败")
                return False

            # 保存问答对
            file_name = os.path.basename(pdf_path).replace('.pdf', '_qa.json')
            output_path = os.path.join(output_dir, file_name)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'file_name': os.path.basename(pdf_path),
                    'pdf_path': pdf_path,
                    'product_name': product_name,
                    'questions': unique_qa_pairs
                }, f, ensure_ascii=False, indent=2)

            print(f"问答对已保存到: {output_path}")
            return True
        except Exception as e:
            print(f"处理PDF文件 {pdf_path} 异常: {e}")
            return False

    def process_folder(self, root_folder, output_dir):
        """
        处理文件夹中的所有PDF文件

        参数:
            root_folder: 根文件夹路径
            output_dir: 输出目录

        返回:
            成功处理的文件数
        """
        success_count = 0

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 遍历根文件夹下的所有产品文件夹
            for product_name in os.listdir(root_folder):
                product_folder = os.path.join(root_folder, product_name)
                if not os.path.isdir(product_folder):
                    # 如果不是文件夹，跳过
                    continue

                print(f"处理产品文件夹: {product_name}")

                # 创建产品对应的输出子目录
                product_output_dir = os.path.join(output_dir, product_name)
                os.makedirs(product_output_dir, exist_ok=True)

                # 处理产品文件夹中的所有PDF文件
                for file_name in os.listdir(product_folder):
                    file_path = os.path.join(product_folder, file_name)
                    if os.path.isfile(file_path) and file_name.lower().endswith('.pdf'):
                        pdf_path = os.path.join(product_folder, file_name)
                        if self.process_single_pdf(pdf_path, product_output_dir, product_name):
                            success_count += 1

            return success_count
        except Exception as e:
            print(f"处理文件夹异常: {e}")
            return success_count

# 使用示例
if __name__ == "__main__":
    # 初始化问答生成器
    qa_generator = PDFToQAGenerator()

    # 定义PDF根目录和输出目录
    pdf_root_folder = "D:/data/内部"
    output_dir = "d:/BaiduNetdiskDownload/code/langgraph/new/insurance_agent_backendv2/test/output"

    # 处理所有PDF文件
    success_count = qa_generator.process_folder(pdf_root_folder, output_dir)
    print(f"成功处理了 {success_count} 个PDF文件")