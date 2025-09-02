from state import State
from es_utils import ESUtils
from llm_client import LLMClient

class ProductMatcherNode:
    # 静态成员保存LLMClient实例，避免重复创建
    _llm_client = None
    
    @staticmethod
    def _get_llm_client():
        """获取或创建LLMClient实例"""
        if ProductMatcherNode._llm_client is None:
            ProductMatcherNode._llm_client = LLMClient()
        return ProductMatcherNode._llm_client
    
    @staticmethod
    def match(state: State) -> State:
        """提取用户查询中的产品名称并进行模糊匹配"""
        try:
            # 更新当前节点
            state.current_node = "product_match"
            
            # 优先使用改写后的问题
            print('product_match_state:',state.product_data)
            if state.product_data and state.product_data.get("rewritten_question"):
                user_query = state.product_data["rewritten_question"]
                print(f"ProductMatcherNode: 使用改写后的查询: {user_query}")
            else:
                # 获取用户查询
                user_query = state.messages[-1]["content"]
                print(f"ProductMatcherNode: 收到查询: {user_query}")
            
            # 初始化ES工具
            es_utils = ESUtils()
            
            # 获取LLM客户端实例（单例模式）
            llm_client = ProductMatcherNode._get_llm_client()
            
            # 直接使用用户查询进行产品匹配
            product_name=ProductMatcherNode.extract_product_name(user_query)
            print('匹配出的产品名称：',product_name)
            matched_products = es_utils.search_fuzzy_product_names(product_name, top_k=5)
            print(f"ProductMatcherNode: 模糊匹配到 {len(matched_products)} 个产品")
            print('match_state:',state.product_data)
            # 根据匹配数量决定下一个节点
            if len(matched_products) == 1:
                # 只有一个匹配结果，直接进入retrieve节点
                state.next_node = "retrieve"
                # 设置产品名称，以便retrieve节点使用
                state.product_data["product_name"] = matched_products[0]
            elif len(matched_products) > 1:
                    # 初始化product_data字段（如果不存在）
                if state.product_data is None:
                    state.product_data = {}
                
                # 存储匹配结果到state.product_data
                state.product_data["matched_products"] = matched_products
                state.product_data["query"] = user_query
                # 多个匹配结果，进入产品选择节点
                state.next_node = "product_select"
            else:
                # 没有匹配结果，进入knowledge节点
                state.error = f"未找到与查询相关的保险产品"
                state.next_node = "knowledge"
            
            print(f"ProductMatcherNode: 下一个节点: {state.next_node}")
            return state
        except Exception as e:
            error_msg = f"产品匹配失败: {str(e)}"
            state.error = error_msg
            print(f"ProductMatcherNode: 错误 - {error_msg}")
            state.next_node = "knowledge"
            return state
    
    @staticmethod
    def extract_product_name(query: str) -> str:
        """使用大模型从查询中提取产品名称"""
        try:
            # 获取LLM客户端实例（单例模式）
            llm_client = ProductMatcherNode._get_llm_client()
            
            # 构建提示
            system_prompt = "你是一个保险产品名称提取专家，擅长从用户的问题中提取保险产品名称。"
            prompt = f"请从以下问题中提取保险产品名称，如果没有提到具体的保险产品，请返回'无'。\n\n例如：我想了解移小保康乐保医疗保险的具体保障内容和适用范围。\n答案：移小保康乐保医疗保险\n\n问题：{query}\n\n保险产品名称："
            
            # 调用大模型生成回答
            result = llm_client.generate(prompt, system_prompt, max_tokens=50)
            print('产品名称：',result)
            # 处理结果
            result = result.strip()
            if result == '无' or not result:
                return None
            return result
        except Exception as e:
            print(f"提取产品名称失败: {str(e)}")
            return None