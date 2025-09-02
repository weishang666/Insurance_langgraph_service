from state import State
from typing import Dict
from llm_client import LLMClient

class IntentRewriterNode:
    # 静态成员保存LLMClient实例，避免重复创建
    _llm_client = None
    
    @staticmethod
    def _get_llm_client():
        """获取或创建LLMClient实例"""
        if IntentRewriterNode._llm_client is None:
            IntentRewriterNode._llm_client = LLMClient()
        return IntentRewriterNode._llm_client
    
    @staticmethod
    def rewrite(state: State) -> State:
        """意图改写节点
        判断是否是第一次提问，如果不是，则改写用户的问题
        """
        try:
            # 更新当前节点
            state.current_node = "intent_rewriter"
            
            # 判断是否是第一次提问
            # 假设第一条消息是用户输入的问题
            print('intent_rewriter_state:',state.messages)
            if len(state.messages) <= 1:
                # 第一次提问，直接进入router节点
                state.next_node = "router"
                return state
            
            # 不是第一次提问，获取完整对话历史
            conversation_history = []
            for msg in state.messages:
                role = "用户" if msg["role"] == "user" else "助手"
                conversation_history.append(f"{role}：{msg['content']}")
            conversation_text = "\n".join(conversation_history)
            
            # 获取最后一个用户问题
            last_user_question = None
            for msg in reversed(state.messages):
                if msg["role"] == "user":
                    last_user_question = msg["content"]
                    break
            
            # 获取LLM客户端实例
            llm_client = IntentRewriterNode._get_llm_client()
            
            # 构建提示
            system_prompt = "你是一个保险领域的问题改写专家，擅长分析保险对话上下文，理解保险术语和产品类型，并改写用户的问题，使其更清晰地表达保险需求和意图。"
            prompt = f"请分析以下保险对话上下文，特别关注最后一个用户的保险问题，然后改写该问题，使其更清晰地表达用户的保险产品需求和真实意图。\n\n对话上下文：\n{conversation_text}\n\n请只返回改写后的保险问题，不要添加任何解释或说明："
            
            # 调用大模型生成回答
            rewritten_question = llm_client.generate(prompt, system_prompt, max_tokens=200)
            rewritten_question = rewritten_question.strip()
            print('rewritten_question:',rewritten_question)
            # 保存改写后的问题到state
            if not state.product_data:
                state.product_data = {}
            state.product_data["rewritten_question"] = rewritten_question
            print(f"IntentRewriterNode: 改写后的问题: {rewritten_question}")
            
            # 进入router节点
            state.next_node = "router"
        except Exception as e:
            state.error = f"意图改写处理失败: {str(e)}"
            state.messages.append({
                "role": "assistant",
                "content": "不好意思，刚才处理你的问题时出现了一点小差错，可以再问一次吗？"
            })
            state.next_node = "router"
        print('***************************************************')
        return state