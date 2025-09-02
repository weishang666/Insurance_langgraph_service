import os
import json
from PyPDF2 import PdfReader
import requests
from requests.auth import HTTPBasicAuth
from llm_client import LLMClient

class ElasticsearchClient:
    """Elasticsearch REST API 客户端封装"""
    
    def __init__(self, host, port, username, password, scheme="http"):
        """
        初始化 Elasticsearch 客户端
        
        参数:
            host: Elasticsearch 主机地址
            port: Elasticsearch 端口
            username: 用户名
            password: 密码
            scheme: 协议 (http/https)
        """
        self.base_url = f"{scheme}://{host}:{port}"
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {"Content-Type": "application/json"}
    
    def insert_document(self, index, doc_id=None, document=None):
        """
        插入或更新文档
        
        参数:
            index: 索引名称
            doc_id: 文档ID (可选，自动生成时为None)
            document: 文档内容 (字典格式)
            
        返回:
            成功返回 True，失败返回 False
        """
        try:
            # 构建URL
            url = f"{self.base_url}/{index}/_doc"
            if doc_id:
                url += f"/{doc_id}"
                
            # 发送请求
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(document)
            )
            
            # 处理响应
            if response.status_code in (200, 201):
                result = response.json()
                print(f"文档 {result['_id']} 已成功索引到 {index}")
                return True
            else:
                print(f"插入失败，状态码: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"插入异常: {e}")
            return False
    
    def get_document(self, index, doc_id):
        """
        获取文档
        
        参数:
            index: 索引名称
            doc_id: 文档ID
            
        返回:
            成功返回文档内容 (字典)，失败返回 None
        """
        try:
            url = f"{self.base_url}/{index}/_doc/{doc_id}"
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()["_source"]
            else:
                print(f"获取失败，状态码: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"查询异常: {e}")
            return None
    
    def search(self, index, query):
        """
        执行搜索查询
        
        参数:
            index: 索引名称
            query: 查询体 (字典格式)
            
        返回:
            成功返回搜索结果，失败返回 None
        """
        try:
            url = f"{self.base_url}/{index}/_search"
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"搜索失败，状态码: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"搜索异常: {e}")
            return None

class PDFProcessor:
    """PDF处理类，用于读取PDF文件、分块、向量化并存储到Elasticsearch"""
    
    def __init__(self, es_client, llm_client=None):
        """
        初始化PDF处理器
        
        参数:
            es_client: ElasticsearchClient 实例
            llm_client: LLMClient 实例，用于生成embedding
        """
        self.es_client = es_client
        self.llm_client = llm_client or LLMClient()
    
    def read_pdf(self, pdf_path):
        """
        读取PDF文件内容
        
        参数:
            pdf_path: PDF文件路径
            
        返回:
            成功返回PDF文本内容，失败返回空字符串
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"读取PDF异常: {e}")
            return ""
    
    def chunk_text(self, text, chunk_size=1000, overlap=100):
        """
        将文本分块
        
        参数:
            text: 要分块的文本
            chunk_size: 每块文本的最大长度
            overlap: 块之间的重叠长度
            
        返回:
            文本块列表
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks
    
    def vectorize_text(self, text):
        """
        将文本向量化
        
        参数:
            text: 要向量化的文本
            
        返回:
            向量表示
        """
        return self.llm_client.get_text_embedding(text)
    
    def process_and_store_pdf(self, pdf_path, index_name, doc_id=None):
        """
        处理PDF文件并存储到Elasticsearch
        
        参数:
            pdf_path: PDF文件路径
            index_name: 索引名称
            doc_id: 文档ID (可选)
            
        返回:
            成功返回 True，失败返回 False
        """
        try:
            # 读取PDF
            text = self.read_pdf(pdf_path)
            if not text:
                print(f"PDF文件 {pdf_path} 没有提取到文本")
                return False
            
            # 分块
            chunks = self.chunk_text(text)
            if not chunks:
                print(f"文本分块失败")
                return False
            
            # 处理每个块
            for i, chunk in enumerate(chunks):
                # 向量化
                vector = self.vectorize_text(chunk)
                
                # 构建文档
                document = {
                    "file_name": os.path.basename(pdf_path),
                    "chunk_id": i,
                    "content": chunk,
                    "vector": vector,
                    "total_chunks": len(chunks),
                    "created_at": "2025-07-23"
                }
                
                # 生成文档ID (如果未提供)
                if doc_id:
                    chunk_doc_id = f"{doc_id}_chunk_{i}"
                else:
                    chunk_doc_id = None
                
                # 存储到Elasticsearch
                if not self.es_client.insert_document(
                    index=index_name,
                    doc_id=chunk_doc_id,
                    document=document
                ):
                    print(f"存储块 {i} 失败")
                    return False
            
            print(f"PDF文件 {pdf_path} 已成功处理并存储到索引 {index_name}")
            return True
        except Exception as e:
            print(f"处理PDF异常: {e}")
            return False
    
    def process_folder(self, folder_path, index_name):
        """
        处理文件夹中的所有PDF文件
        
        参数:
            folder_path: 文件夹路径
            index_name: 索引名称
            
        返回:
            成功处理的文件数
        """
        success_count = 0
        try:
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith(".pdf"):
                    pdf_path = os.path.join(folder_path, file_name)
                    print(f"处理文件: {pdf_path}")
                    if self.process_and_store_pdf(pdf_path, index_name):
                        success_count += 1
            return success_count
        except Exception as e:
            print(f"处理文件夹异常: {e}")
            return 0

# 使用示例
if __name__ == "__main__":
    # 初始化Elasticsearch客户端
    es = ElasticsearchClient(
        host="10.176.27.142",
        port=9200,
        username="tenant",
        password="Root@10086"
    )
    
    # 初始化LLM客户端
    llm_client = LLMClient()
    
    # 初始化PDF处理器
    pdf_processor = PDFProcessor(es, llm_client)
    
    # 处理单个PDF文件
    pdf_path = "path/to/your/pdf/file.pdf"
    pdf_processor.process_and_store_pdf(pdf_path, "insurance_documents")
    
    # 处理文件夹中的所有PDF文件
    folder_path = "path/to/your/pdf/folder"
    success_count = pdf_processor.process_folder(folder_path, "insurance_documents")
    print(f"成功处理了 {success_count} 个PDF文件")