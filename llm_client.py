import requests
import json
import time
import warnings
import functools

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
    

    def text_to_embedding_modelscope(text):
        """
        使用 ModelScope 的 text2vec-large-chinese 模型将中文文本转换为 1024 维向量。

        Args:
            text (str or List[str]): 输入的中文文本字符串或字符串列表。

        Returns:
            numpy.ndarray: 文本对应的 1024 维向量表示。
                        如果输入是单个字符串，返回一维数组 (1024,)；
                        如果输入是列表，返回二维数组 (n_texts, 1024)。
        """
        # 全局加载模型 (避免重复加载，提高效率)
        # 使用 text2vec-large-chinese 模型，输出维度为 1024，专为中文优化
        embedding_pipeline = pipeline(Tasks.text_embedding, model='damo/nlp_corom_sentence-embedding_chinese-large')
        
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
            # 调用 ModelScope pipeline 获取嵌入
            # 输出是一个字典，其中 'text_embedding' 包含了向量
            result = embedding_pipeline(input_texts)
            embeddings = np.array(result['text_embedding'])  # shape: (n_texts, 1024)

            # 如果原始输入是单个字符串，则返回一维数组
            if single_input:
                embeddings = embeddings[0]  # shape: (1024,)

            return list(embeddings)

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
        #return text_to_embedding_modelscope(text)

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
    
    @retry_on_failure(max_retries=3, backoff_factor=0.3)
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        大模型推理生成文本

        参数:
            prompt: 提示文本
            system_prompt: 系统提示文本
            max_tokens: 生成的最大token数
            temperature: 温度参数，控制生成的随机性

        返回:
            生成的文本
        """
        try:
            if not self.llm_url or not self.llm_appcode:
                print("大模型推理服务参数未配置")
                return ""
            
            # 准备请求数据
            data = {
                "model": self.model_name,
                "messages": [],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 添加系统提示
            if system_prompt:
                data["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加用户提示
            data["messages"].append({
                "role": "user",
                "content": prompt
            })
            
            # 发起请求
            response = requests.post(
                self.llm_url,
                headers=self.llm_headers,
                data=json.dumps(data),
                verify=False
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                error_msg = f"大模型推理失败，状态码: {response.status_code}，错误信息: {response.text}"
                print(error_msg)
                # 抛出异常以触发重试机制
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"大模型推理异常: {e}")
            return ""

# 使用示例
if __name__ == "__main__":
    # 初始化客户端 (qwen72b)
    llm_client_qwen = LLMClient(model_name="qwen72b")
    
    # 测试单个文本embedding
    single_text = "保险合同是投保人与保险人约定保险权利义务关系的协议"
    single_embedding = llm_client_qwen.get_text_embedding(single_text)
    print(f"单个文本embedding长度: {len(single_embedding)}")
    print(f"embedding前5个值: {single_embedding[:5]}")
    
    # 测试多个文本embedding
    multiple_texts = [
        "保险合同是投保人与保险人约定保险权利义务关系的协议",
        "保险责任是指保险人依照保险合同对被保险人或者受益人承担的保险金给付责任"
    ]
    multiple_embeddings = llm_client_qwen.get_text_embedding(multiple_texts)
    print(f"多个文本embedding数量: {len(multiple_embeddings)}")
    print(f"第一个embedding长度: {len(multiple_embeddings[0])}")
    print(f"第二个embedding长度: {len(multiple_embeddings[1])}")
    
    # 测试大模型推理 (qwen72b)
    prompt = "科比是谁"
    system_prompt = "回答问题需包含：\n</reflection>\n推理步骤\n</reflection>\n 最终结论 (用\\boxed{} 包裹)。"
    result = llm_client_qwen.generate(prompt, system_prompt)
    print(f"qwen72b大模型推理结果: {result}")
    
    # 初始化客户端 (deepseek14)
    # llm_client_deepseek = LLMClient(model_name="deepseek14")
    # 测试deepseek14模型推理
    # result = llm_client_deepseek.generate("请解释什么是保险合同")
    # print(f"deepseek14大模型推理结果: {result}")