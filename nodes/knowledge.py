from state import State
from es_utils import ESUtils

class KnowledgeNode:
    # 静态成员保存LLMClient实例，避免重复创建
    _llm_client = None
    
    @staticmethod
    def _get_llm_client():
        """获取或创建LLMClient实例"""
        if KnowledgeNode._llm_client is None:
            from llm_client import LLMClient
            KnowledgeNode._llm_client = LLMClient()
        return KnowledgeNode._llm_client

    @staticmethod
    def extract_keywords(user_query):
        """从用户查询中提取保险关键词"""
        # 获取LLM客户端实例
        llm_client = KnowledgeNode._get_llm_client()
        
        # 构建提取关键词的提示
        prompt = f"从以下保险相关问题中提取3-5个最核心的关键词，用逗号分隔：{user_query}"
        system_prompt = "你是一个保险领域关键词提取专家。"
        
        # 调用大模型提取关键词
        keywords_str = llm_client.generate(prompt, system_prompt)
        
        # 处理结果，去除空格并转换为列表
        keywords = [keyword.strip() for keyword in keywords_str.split(',')]
        return keywords


    @staticmethod
    def answer(state: State) -> State:
        """回答保险通用知识问题"""
        try:
            # 更新当前节点
            state.current_node = "knowledge"

            # 优先使用改写后的问题
            if state.product_data and state.product_data.get("rewritten_question"):
                user_query = state.product_data["rewritten_question"]
            else:
                # 获取最后一个用户查询
                user_query = state.messages[-1]["content"] if state.messages and state.messages[-1]["role"] == "user" else ""

            # 初始化ES工具
            es_utils = ESUtils()
            
            # 提取关键词
            keywords = KnowledgeNode.extract_keywords(user_query)
            print('****keywords******',keywords)
            # 获取关键词定义
            keyword_definitions = []
            for keyword in keywords:
                definitions = es_utils.get_term_definition(keyword)
                if definitions:
                    for definition in definitions:
                        keyword_definitions.append(f"{keyword}：{definition}")
            
            # 获取LLM客户端实例（单例模式）
            llm_client = KnowledgeNode._get_llm_client()

            # 构建提示
            system_prompt = "你是一个保险知识专家，擅长解答各类保险通用知识问题。"
            
            print('keyword_definitions',keyword_definitions)
            # 构建包含关键词定义的提示
            if keyword_definitions:
                definitions_text = "\n\n以下是相关保险术语的定义：\n" + "\n".join(keyword_definitions)
                prompt = f"请回答以下问题：\n\n问题：{user_query}{definitions_text}\n\n回答："
                print('***prompt*******',prompt)
            else:
                prompt = f"请回答以下问题：\n\n问题：{user_query}\n\n回答："

            # 调用大模型生成回答
            answer = llm_client.generate(prompt, system_prompt)
            #print(answer)
            # 更新状态
            state.messages.append({
                "role": "assistant",
                "content": answer
            })

            return state
        except Exception as e:
            state.error = f"保险知识解答失败: {str(e)}"
            state.messages.append({
                "role": "assistant",
                "content": f"很抱歉，处理您的问题时出现错误: {str(e)}\n请尝试重新表述您的问题。"
            })
            return state