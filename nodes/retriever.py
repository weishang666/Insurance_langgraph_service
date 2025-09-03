from state import State
from es_utils import ESUtils
from llm_client import LLMClient
import re
import numpy as np

class RetrieverNode:
    @staticmethod
    def is_overview_query(query: str) -> bool:
        """判断用户查询是否为保险产品概览介绍请求"""
        try:
            # 获取LLM客户端实例（单例模式）
            llm_client = RetrieverNode._get_llm_client()
            
            # 构建提示
            system_prompt = "你是一个保险查询意图识别专家，擅长判断用户的问题是否属于保险产品概览介绍请求。"
            prompt = f"请判断以下问题是否属于保险产品概览介绍请求（如'介绍一下某某产品'），如果是请返回'是'，否则属于具体产品条款查询返回'否'。例如：\n\n问题：介绍一下某某产品的基本条款\n\n判断结果：否\n\n问题：某某产品的保障范围\n\n判断结果：否\n\n问题：请介绍某某产品\n\n判断结果：是\n\n问题：{query}\n\n判断结果："
            
            # 调用大模型生成回答
            result = llm_client.generate(prompt, system_prompt, max_tokens=10)
            
            # 处理结果
            result = result.strip()
            return result == '是'
        except Exception as e:
            print(f"判断概览查询失败: {str(e)}")
            return False

    @staticmethod
    def retrieve(state: State) -> State:
        """从Elasticsearch检索相关条款，支持产品名称识别和向量搜索以及结构化数据检索"""
        try:
            # 更新当前节点
            state.current_node = "retrieve"
            
            # 优先使用改写后的问题
            if state.product_data and state.product_data.get("rewritten_question"):
                user_query = state.product_data["rewritten_question"]
                print(f"RetrieverNode: 使用改写后的查询: {user_query}")
            else:
                # 获取用户查询
                user_query = state.messages[-1]["content"]
                print(f"RetrieverNode: 收到查询: {user_query}")
            
            # 初始化ES工具
            es_utils = ESUtils()
            
            # 获取LLM客户端实例（单例模式）
            llm_client = RetrieverNode._get_llm_client()
            
            print('retrieve_state:',state.product_data)
            # 优先使用product_data中的产品名称
            product_name = None
            if state.product_data and state.product_data.get("product_name"):
                product_name = state.product_data["product_name"]
                print(f"RetrieverNode: 使用product_data中的产品名称: {product_name}")
            else:
                # 如果没有，再从用户查询中提取
                product_name = RetrieverNode.extract_product_name(user_query)
                print(f"RetrieverNode: 提取的产品名称: {product_name}")
            
            retrieved_docs = []
            if not product_name:
                # 无法提取产品名称，设置错误信息
                state.error = "无法从查询中提取保险产品名称"
                print("RetrieverNode: 错误 - 无法提取产品名称")
                return state
            else:
                retrieved_docs = []
                
                # 判断是否为概览查询
                is_overview = RetrieverNode.is_overview_query(user_query)
                print(f"RetrieverNode: 是否为概览查询: {is_overview}")
                
                if is_overview:
                    # 概览查询，从指定的chunk_type列表中检索
                    overview_chunk_types = [
                        "1）生效日期",
                        "2）适用人群（年龄、性别、地区）",
                        "3）保障责任范围",
                        "16）保险期限",
                        "21）所属保险公司",
                        "24）产品分类（医疗险、重疾险、意外险、寿险、车险、宠物险、防诈险、碎屏险、家财险）",
                        "27）保费"
                    ]
                    
                    # 使用新的ES工具实例，指定新索引
                    structured_es_utils = ESUtils(index="insurance_structured_chunk")
                    print(f"RetrieverNode: 开始从结构化索引 '{structured_es_utils.index}' 检索概览信息")
                    
                    # 存储所有概览文档
                    #overview_docs = []
                    
                    # 遍历所有指定的chunk_type
                    for ct in overview_chunk_types:
                        structured_docs = structured_es_utils.search_by_product_and_chunk_type(
                            product_name, ct
                        )
                        print(f"RetrieverNode: 从结构化索引检索到 {len(structured_docs)} 条 {ct} 结果")
                        if structured_docs:
                            #overview_docs.extend(structured_docs)
                            for i in structured_docs:
                                retrieved_docs.append(f"{ct}：{i['chunk_text']}")
                                #print(f"{ct}: {i['chunk_text']}")
                    
                    # # 如果找到概览文档，添加到检索结果中
                    # if overview_docs:
                    #     overview_docs_list = [{'content': doc['chunk_text']} for doc in overview_docs]
                    #     retrieved_docs.extend(overview_docs_list)
                    #     print(f"RetrieverNode: 合并后检索文档总数: {len(retrieved_docs)}")
                else:
                    # 非概览查询，使用优化的向量搜索策略
                    # 1. 生成k个候选答案
                    k = 3  # 默认为3个候选答案
                    candidate_answers = RetrieverNode.generate_candidate_answers(user_query, product_name, k, llm_client)
                    print(f"RetrieverNode: 生成了 {len(candidate_answers)} 个候选答案")
                    
                    if not candidate_answers:
                        # 如果没有生成候选答案，回退到原始方式
                        query_vector = llm_client.get_text_embedding(user_query)
                        print("RetrieverNode: 回退到原始向量搜索方式")
                        retrieved_texts = es_utils.search_by_vector_and_product(product_name, query_vector)
                        if retrieved_texts:
                            retrieved_docs = [{"content": text} for text in retrieved_texts]
                        else:
                            state.error = "未找到与该产品相关的保险条款"
                            print("RetrieverNode: 错误 - 未找到相关文档")
                            return state
                    else:
                        # 2. 将每个候选答案转换为向量并搜索文档
                        # 使用字典存储每个候选答案的检索结果和分数
                        answer_dicts = []
                        for i, answer in enumerate(candidate_answers):
                            answer_vector = llm_client.get_text_embedding(answer)
                            # 每个向量匹配10条结果
                            retrieved_texts = es_utils.search_by_vector_and_product(product_name, answer_vector, size=10)
                            print(f"RetrieverNode: 候选答案{i+1}检索到 {len(retrieved_texts)} 条结果")
                            
                            # 创建当前答案的检索结果字典，按位置赋值分数（第一个1分，第二个0.9分...）
                            answer_dict = {}
                            for idx, text in enumerate(retrieved_texts):
                                # 计算分数：1.0, 0.9, 0.8, ..., 0.1
                                score = max(0.1, 1.0 - idx * 0.1)
                                answer_dict[text] = score
                            
                            answer_dicts.append(answer_dict)
                        print("***********30个匹配answer_dicts****************")    
                        print(answer_dicts)

                        # 3. 从3个字典中取内容相似度高的交集5个
                        # 首先统计每个文档在多少个字典中出现
                        doc_counts = {}
                        all_docs = {}                 
                        for i, answer_dict in enumerate(answer_dicts):
                            for text, score in answer_dict.items():
                                if text not in doc_counts:
                                    doc_counts[text] = 0
                                doc_counts[text] += 1
                                
                                # 存储每个文档的最高分数
                                if text not in all_docs or score > all_docs[text]:
                                    all_docs[text] = score
                        
                        # 计算综合分数：出现次数越多，分数越高
                        # 优先选择在多个字典中出现的文档（交集）
                        # 然后按照文档分数排序
                        sorted_docs = sorted(all_docs.items(), key=lambda x: (doc_counts[x[0]], x[1]), reverse=True)
                        print("*********sorted_docs**************")
                        print(sorted_docs)
                        
                        # 选择前5个文档
                        top_docs = sorted_docs[:5]
                        retrieved_docs = [{"content": text} for text, score in top_docs]
                        
                        print(f"RetrieverNode: 处理后检索到 {len(retrieved_docs)} 条结果")
                        
                        if not retrieved_docs:
                            state.error = "未找到与该产品相关的保险条款"
                            print("RetrieverNode: 错误 - 未找到相关文档")
                            return state
                            
                    # 提取chunk_type类型并从新索引检索
                    chunk_type = RetrieverNode.extract_chunk_type(user_query)
                    print(f"RetrieverNode: 提取的chunk_type: {chunk_type}")
                    
                    if chunk_type:
                        # 使用新的ES工具实例，指定新索引
                        structured_es_utils = ESUtils(index="insurance_structured_chunk")
                        print(f"RetrieverNode: 开始从结构化索引 '{structured_es_utils.index}' 检索")
                        
                        # 根据产品名称和chunk_type检索
                        structured_docs = structured_es_utils.search_by_product_and_chunk_type(
                            product_name, chunk_type
                        )
                        print(f"RetrieverNode: 从结构化索引检索到 {len(structured_docs)} 条结果")
                        for i in structured_docs:
                            print(i['chunk_text'])
                        # 如果找到结构化文档，添加到检索结果中
                        if structured_docs:
                            structured_docs_list = [{'content': doc['chunk_text']} for doc in structured_docs]
                            retrieved_docs.extend(structured_docs_list)
                            print(f"RetrieverNode: 合并后检索文档总数: {len(retrieved_docs)}")
            
            # 更新状态
            state.extracted_data = {
                "query": user_query,
                "retrieved_docs": retrieved_docs,
                "product_name": product_name,
                "chunk_type": chunk_type
            }
            
            print("RetrieverNode: 检索完成")
            return state
        except Exception as e:
            error_msg = f"检索失败: {str(e)}"
            state.error = error_msg
            print(f"RetrieverNode: 错误 - {error_msg}")
            return state
    
    @staticmethod
    def extract_product_name(query: str) -> str:
        """使用大模型从查询中提取产品名称"""
        try:
            # 获取LLM客户端实例（单例模式）
            llm_client = RetrieverNode._get_llm_client()
            
            # 构建提示
            system_prompt = "你是一个保险产品名称提取专家，擅长从用户的问题中提取保险产品名称。"
            prompt = f"请从以下问题中提取保险产品名称，如果没有提到具体的保险产品，请返回'无'。\n\n问题：{query}\n\n保险产品名称："
            
            # 调用大模型生成回答
            result = llm_client.generate(prompt, system_prompt, max_tokens=50)
            #print('产品名称：',result)
            # 处理结果
            result = result.strip()
            if result == '无' or not result:
                return None
            return result
        except Exception as e:
            print(f"提取产品名称失败: {str(e)}")
            return None

    # 静态成员保存LLMClient实例，避免重复创建
    _llm_client = None
    
    @staticmethod
    def _get_llm_client():
        """获取或创建LLMClient实例"""
        if RetrieverNode._llm_client is None:
            RetrieverNode._llm_client = LLMClient()
        return RetrieverNode._llm_client
        
    @staticmethod
    def generate_candidate_answers(query: str, product_name: str, k: int = 3, llm_client: LLMClient = None) -> list:
        """根据用户问题和产品名称生成k个可能的答案
        
        参数:
            query: 用户查询
            product_name: 保险产品名称
            k: 生成的候选答案数量
            llm_client: LLM客户端实例
        
        返回:
            候选答案列表
        """
        try:
            if llm_client is None:
                llm_client = RetrieverNode._get_llm_client()
            
            # 构建提示
            system_prompt = "你是一个保险领域专家，擅长回答关于保险产品的问题。"
            prompt = f"用户询问关于{product_name}的问题：{query}\n请从不同角度生成{k}个可能的答案，每个答案用换行符分隔，不要添加序号或其他标记。"
            
            # 调用大模型生成回答
            result = llm_client.generate(prompt, system_prompt, max_tokens=1000)
            
            # 处理结果，分割成k个答案
            answers = result.strip().split('\n')
            # 过滤空字符串并取前k个
            answers = [ans.strip() for ans in answers if ans.strip()][:k]
            
            return answers
        except Exception as e:
            print(f"生成候选答案失败: {str(e)}")
            return []
            
    
    @staticmethod
    def extract_chunk_type(query: str) -> str:
        """使用大模型从查询中提取chunk_type类型"""
        try:
            # 获取LLM客户端实例（单例模式）
            llm_client = RetrieverNode._get_llm_client()
            
            # 定义chunk_type类型字典
            chunk_type_dict = {
                "1": "1）生效日期",
                "2": "2）适用人群（年龄、性别、地区）",
                "3": "3）保障责任范围",
                "4": "4）免责条款",
                "5": "5）等待期天数",
                "6": "6）续保规则",
                "7": "7）销售区域限制",
                "8": "8）各年龄段保费表",
                "9": "9）保障疾病/药品覆盖清单",
                "10": "10）赔付限额",
                "11": "11）年免赔额",
                "12": "12）赔付比例",
                "13": "13）犹豫期天数",
                "14": "14）保障区域",
                "15": "15）缴费方式（是否支持话费扣除）",
                "16": "16）保险期限",
                "17": "17）医院范围",
                "18": "18）健康管理服务",
                "19": "19）家庭费率",
                "20": "20）宽限期",
                "21": "21）所属保险公司",
                "22": "22）是否有职业限制，职业限制名单(《特殊职业类别表》)",
                "23": "23）可投保标的（车/建筑）",
                "24": "24）产品分类（医疗险、重疾险、意外险、寿险、车险、宠物险、防诈险、碎屏险、家财险）",
                "25": "25）健康告知要求",
                "26": "26）增值服务内容（如：绿通、垫付、特药服务）",
                "27": "27）保费"
            }
            
            # 构建提示，让模型只返回数字
            system_prompt = "你是一个保险条款类型识别专家，擅长根据用户问题判断其属于哪种保险条款类型。"
            chunk_type_list = [f"{key}：{value}" for key, value in chunk_type_dict.items()]
            prompt = f"以下是保险条款的类型列表：\n{chr(10).join(chunk_type_list)}\n\n问题：{query}\n\n请仅返回对应条款类型的数字编号（1-27），,只返回和问题最相关的一个数字，如果不属于任何类型，请返回'无'。\n\n数字编号："
            
            # 调用大模型生成回答
            result = llm_client.generate(prompt, system_prompt, max_tokens=10)
            print('chunk_type：',result)
            # 处理结果
            result = result.strip()
            if result == '无' or not result or result not in chunk_type_dict:
                return None
            return chunk_type_dict[result]
        except Exception as e:
            print(f"提取chunk_type失败: {str(e)}")
            return None