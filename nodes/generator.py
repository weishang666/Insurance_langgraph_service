from state import State

class GeneratorNode:
    # 静态成员保存LLMClient实例，避免重复创建
    _llm_client = None
    
    @staticmethod
    def _get_llm_client():
        """获取或创建LLMClient实例"""
        if GeneratorNode._llm_client is None:
            from llm_client import LLMClient
            GeneratorNode._llm_client = LLMClient()
        return GeneratorNode._llm_client
    @staticmethod
    def generate(state: State) -> State:
        """根据检索到的条款生成回答"""
        try:
            # 更新当前节点
            state.current_node = "generate"
            
            # 检查是否有检索到的文档
            if not state.extracted_data or not state.extracted_data.get("retrieved_docs"):
                state.messages.append({
                    "role": "assistant",
                    "content": "抱歉，没有找到相关的条款信息。"
                })
                return state
            print('generate_state:',state.product_data)
            # 优先使用改写后的问题
            if state.product_data and state.product_data.get("rewritten_question"):
                user_query = state.product_data["rewritten_question"]
            else:
                user_query = state.extracted_data["query"]
            retrieved_docs = state.extracted_data["retrieved_docs"]
            product_name = state.extracted_data.get("product_name")
            
            context = "\n".join([doc["content"] for doc in retrieved_docs])
            
            # 获取LLM客户端实例（单例模式）
            llm_client = GeneratorNode._get_llm_client()

            # 构建提示
            system_prompt = "你是一个保险领域专家，擅长解读保险相关内容并回答用户问题。"
            if product_name:
                prompt = f"请根据{product_name}的相关内容，回答用户问题：\n\n问题：{user_query}\n\n相关内容：{context}\n\n回答："
            else:
                prompt = f"请根据相关内容，回答用户问题：\n\n问题：{user_query}\n\n相关内容：{context}\n\n回答："
            answer = llm_client.generate(prompt, system_prompt)
            
            # 更新状态
            state.messages.append({
                "role": "assistant",
                "content": answer
            })
            
            return state
        except Exception as e:
            state.error = f"生成回答失败: {str(e)}"
            return state