import requests
import json
import time
import warnings
import functools
import numpy as np
import os
from openai import OpenAI
from sentence_transformers import SentenceTransformer
# 忽略HTTPS证书验证警告
warnings.filterwarnings('ignore', category=requests.packages.urllib3.exceptions.InsecureRequestWarning)


def retry_on_failure(max_retries=3, backoff_factor=0.3):
    """
    网络请求失败重试装饰器

    参数:
        max_retries: 最大重试次数
        backoff_factor: 退避因子，用于计算重试间隔时间
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if retries >= max_retries:
                        print(f"请求失败，已达到最大重试次数({max_retries}): {e}")
                        raise
                    wait_time = backoff_factor * (2 ** retries)
                    print(f"请求失败，将在{wait_time:.2f}秒后重试: {e}")
                    time.sleep(wait_time)
                    retries += 1
        return wrapper
    return decorator
from typing import Union, List, Dict, Any
from config import LLM_APP_CODE, LLM_API_URL, EMBEDDING_URL, EMBEDDING_APP_CODE

class LLMClient:
    """大模型客户端类，提供生成embedding和大模型推理功能"""
    
    # 类变量，用于缓存embedding模型，避免重复加载
    _embedding_pipeline = None
    
    def __init__(self, embedding_url=None, embedding_appcode=None, 
                 llm_url=None, llm_appcode=None, model_name="qwen72b"):
        """
        初始化大模型客户端
        
        参数:
            embedding_url: embedding服务URL
            embedding_appcode: embedding服务认证码
            llm_url: 大模型推理服务URL
            llm_appcode: 大模型推理服务认证码
            model_name: 模型名称 (qwen72b 或 deepseek14)
        """
        # 设置embedding服务参数
        self.embedding_url = embedding_url or EMBEDDING_URL
        self.embedding_appcode = embedding_appcode or EMBEDDING_APP_CODE
        self.embedding_headers = {
            "Authorization": "Bearer " + self.embedding_appcode,
            "Content-Type": "application/json"
        }
        
        # 设置大模型推理服务参数
        self.model_name = model_name
        self.llm_url = llm_url or LLM_API_URL
        self.llm_appcode = llm_appcode or LLM_APP_CODE
        self.llm_headers = {
            "Authorization": f"Bearer {self.llm_appcode}",
            "Content-Type": "application/json"
        }
    

    def text_to_embedding_local(self, text):
        """
        使用 sentence-transformers 模型将中文文本转换为向量。

        Args:
            text (str or List[str]): 输入的中文文本字符串或字符串列表。

        Returns:
            List[float] or List[List[float]]: 文本对应的向量表示。
                        如果输入是单个字符串，返回一维列表；
                        如果输入是列表，返回二维列表。
        """
        # 使用类变量缓存模型，避免重复加载
        if LLMClient._embedding_pipeline is None:
            print("正在加载embedding模型...")
            # 使用中文优化的模型
            # 可选模型：
            # - 'shibing624/text2vec-base-chinese' (768维)
            # - 'moka-ai/m3e-base' (768维)
            # - 'BAAI/bge-large-zh-v1.5' (1024维)
            LLMClient._embedding_pipeline = SentenceTransformer('BAAI/bge-large-zh-v1.5')
            print("embedding模型加载完成")
        
        # 检查输入类型
        if isinstance(text, str):
            input_texts = [text]
            single_input = True
        elif isinstance(text, list):
            input_texts = text
            single_input = False
        else:
            raise TypeError("Input must be a string or a list of strings.")

        try:
            # 调用 sentence-transformers 获取嵌入
            embeddings = LLMClient._embedding_pipeline.encode(input_texts)

            # 如果原始输入是单个字符串，则返回一维数组
            if single_input:
                embeddings = embeddings[0]  # shape: (1024,)

            return embeddings.tolist()

        except Exception as e:
            print(f"Error during embedding generation: {e}")
            return None


    @retry_on_failure(max_retries=3, backoff_factor=0.3)
    def get_text_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        获取文本的embedding

        参数:
            text: 单个文本字符串或文本字符串列表

        返回:
            如果输入是字符串，返回单个embedding列表
            如果输入是列表，返回embedding列表的列表
        """
        # 使用本地sentence-transformers模型生成embedding
        return self.text_to_embedding_local(text)

        # 以下是API调用方式（已注释）
        try:
            # 处理输入类型
            if isinstance(text, str):
                text_lst = [text]
                single_input = True
            else:
                text_lst = text
                single_input = False
            
            # 准备请求数据
            data = {
                "input": text_lst
            }
            
            # 发起请求
            response = requests.post(
                self.embedding_url,
                headers=self.embedding_headers,
                data=json.dumps(data),
                verify=False
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                embeddings = [item['embedding'] for item in result['data']]
                
                # 根据输入类型返回结果
                if single_input:
                    return embeddings[0]
                else:
                    return embeddings
            else:
                error_msg = f"获取embedding失败，状态码: {response.status_code}，错误信息: {response.text}"
                print(error_msg)
                # 抛出异常以触发重试机制
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"获取embedding异常: {e}")
            return [] if not single_input else [0.0]
    
    # 原有的generate函数（已注释，使用DeepSeek API替代）
    # @retry_on_failure(max_retries=3, backoff_factor=0.3)
    # def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    #     """
    #     大模型推理生成文本

    #     参数:
    #         prompt: 提示文本
    #         system_prompt: 系统提示文本
    #         max_tokens: 生成的最大token数
    #         temperature: 温度参数，控制生成的随机性

    #     返回:
    #         生成的文本
    #     """
    #     # print("llm_url",self.llm_url)
    #     # print("llm_appcode",self.llm_appcode)

    #     try:
    #         if not self.llm_url or not self.llm_appcode:
    #             print("大模型推理服务参数未配置")
    #             return ""
            
    #         # 准备请求数据
    #         data = {
    #             "model": self.model_name,
    #             "messages": [],
    #             "temperature": temperature,
    #             "max_tokens": max_tokens
    #         }
            
    #         # 添加系统提示
    #         if system_prompt:
    #             data["messages"].append({
    #                 "role": "system",
    #                 "content": system_prompt
    #             })
            
    #         # 添加用户提示
    #         data["messages"].append({
    #             "role": "user",
    #             "content": prompt
    #         })
            
    #         # 发起请求
    #         response = requests.post(
    #             self.llm_url,
    #             headers=self.llm_headers,
    #             data=json.dumps(data),
    #             verify=False
    #         )
            
    #         # 处理响应
    #         if response.status_code == 200:
    #             result = response.json()
    #             return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    #         else:
    #             error_msg = f"大模型推理失败，状态码: {response.status_code}，错误信息: {response.text}"
    #             print(error_msg)
    #             # 抛出异常以触发重试机制
    #             raise Exception(error_msg)
                
    #     except Exception as e:
    #         print(f"大模型推理异常: {e}")
    #         return ""

    @retry_on_failure(max_retries=3, backoff_factor=0.3)
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        使用DeepSeek API进行大模型推理生成文本

        参数:
            prompt: 提示文本
            system_prompt: 系统提示文本
            max_tokens: 生成的最大token数
            temperature: 温度参数，控制生成的随机性

        返回:
            生成的文本
        """
        try:
            # 设置DeepSeek API密钥
            api_key = "sk-30d2ad2a63574699b0b848d8ee637107"
            os.environ['DEEPSEEK_API_KEY'] = api_key
            
            # 初始化DeepSeek客户端
            client = OpenAI(
                api_key=os.environ.get('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com"
            )
            
            # 构建消息列表
            messages = []
            
            # 添加系统提示
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加用户提示
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # 调用DeepSeek API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # 返回生成的文本
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"DeepSeek API调用异常: {e}")
            return ""

# 使用示例
if __name__ == "__main__":
    #{"model": "qwen72b","messages": [{"role": "user", "content": "你是谁"}], "stream":false, "max_tokens":128}
    # 初始化客户端 (qwen72b)
    # llm_client_qwen = LLMClient(model_name="qwen72b")
    # llm_client_qwen.text_to_embedding_modelscope("保险合同是投保人与保险人约定保险权利义务关系的协议")

    llm_client = LLMClient()

# 单个文本embedding
    text = "这是一个测试文本"
    embedding = llm_client.get_text_embedding(text)
    print(f"向量维度: {len(embedding)}")  # 输出: 1024

    # 多个文本embedding
    texts = ["文本1", "文本2", "文本3"]
    embeddings = llm_client.get_text_embedding(texts)
    print(f"文本数量: {len(embeddings)}")  # 输出: 3
    print(f"每个向量维度: {len(embeddings[0])}")  # 输出: 102
    # 测试单个文本embedding
    # single_text = "保险合同是投保人与保险人约定保险权利义务关系的协议"
    # single_embedding = llm_client_qwen.get_text_embedding(single_text)
    # print(f"单个文本embedding长度: {len(single_embedding)}")
    # print(f"embedding前5个值: {single_embedding[:5]}")
    
    # # 测试多个文本embedding
    # multiple_texts = [
    #     "保险合同是投保人与保险人约定保险权利义务关系的协议",
    #     "保险责任是指保险人依照保险合同对被保险人或者受益人承担的保险金给付责任"
    # ]
    # multiple_embeddings = llm_client_qwen.get_text_embedding(multiple_texts)
    # print(f"多个文本embedding数量: {len(multiple_embeddings)}")
    # print(f"第一个embedding长度: {len(multiple_embeddings[0])}")
    # print(f"第二个embedding长度: {len(multiple_embeddings[1])}")
    
    # # 测试大模型推理 (qwen72b)
    # prompt = "科比是谁"
    # system_prompt = "回答问题需包含：\n</reflection>\n推理步骤\n</reflection>\n 最终结论 (用\\boxed{} 包裹)。"
    # result = llm_client_qwen.generate(prompt, system_prompt)
    # print(f"qwen72b大模型推理结果: {result}")
    
    # 初始化客户端 (deepseek14)
    # llm_client_deepseek = LLMClient(model_name="deepseek14")
    # 测试deepseek14模型推理
    # result = llm_client_deepseek.generate("请解释什么是保险合同")
    # print(f"deepseek14大模型推理结果: {result}")