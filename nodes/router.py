from tkinter.constants import E
from langgraph.graph.state import NoneType
from langgraph.store.base import Result
from state import State
from typing import Dict
from langgraph.graph import END
import re


class RouterNode:
    # 静态成员保存LLMClient实例，避免重复创建
    _llm_client = None
    
    @staticmethod
    def _get_llm_client():
        """获取或创建LLMClient实例"""
        if RouterNode._llm_client is None:
            from llm_client import LLMClient
            RouterNode._llm_client = LLMClient()
        return RouterNode._llm_client
    
    @staticmethod
    def _get_greeting_reply(content: str) -> str:
        """生成寒暄回复"""
        llm_client = RouterNode._get_llm_client()
        system_prompt = "你是一个友好的保险助手，擅长用自然、亲切的语言回应用户的寒暄。"
        prompt = f"用户说：{content}\n请用友好、自然的语言回复，保持简短："
        reply = llm_client.generate(prompt, system_prompt, max_tokens=50)
        return reply.strip()
    
    
    @staticmethod
    def route(state: State) -> State:
        """根据用户问题类型决定路由方向"""
        try:
            # 更新当前节点
            state.current_node = "router"
            
            # 检查是否有产品匹配数据需要处理
            # 获取LLM客户端实例（单例模式）
            llm_client = RouterNode._get_llm_client()
            if state.product_data:
                state.product_data["matched_products"]=[]
            else:
                state.product_data={}
                state.product_data["matched_products"]=[]
            #print('state.product_data:',state.product_data)
            
            print('router_state:',state.product_data)

            # 构建提示
            system_prompt = "你是一个保险问题分类专家，擅长判断用户的问题类型。"
            
            # 优先使用改写后的问题
            if state.product_data and state.product_data.get("rewritten_question"):
                user_question = state.product_data["rewritten_question"]
                prompt = f"请判断以下用户问题的类型：\n\n{user_question}\n\n类型选项：\n1. 非保险问题（与保险无关的实质性问题，如“天气如何”“股票走势”）\n2. 包含具体保险产品名称的条款解读问题（如“平安福的重疾赔付次数是多少？”）\n3.保险通用知识问题（不涉及具体产品，如“重疾险和医疗险的区别是什么？”）\n4. 寒暄或友好互动（如“你好”“谢谢”“再见”“辛苦了”等无实质信息的互动）\n\n请只返回选项数字(1/2/3/4)："
            else:
                # 使用原始问题
                user_question = state.messages[-1]["content"]
                prompt = f"请判断以下用户问题的类型：\n\n{user_question}\n\n类型选项：\n1. 非保险问题（与保险无关的实质性问题，如“天气如何”“股票走势”）\n2. 包含具体保险产品名称的条款解读问题（如“平安福的重疾赔付次数是多少？”）\n3.保险通用知识问题（不涉及具体产品，如“重疾险和医疗险的区别是什么？”）\n4. 寒暄或友好互动（如“你好”“谢谢”“再见”“辛苦了”等无实质信息的互动）\n\n请只返回选项数字(1/2/3/4)："
            print("prompt",prompt)
            # 调用大模型生成回答
            result = llm_client.generate(prompt, system_prompt, max_tokens=10)
            #print(result)
            # 处理结果
            result = result.strip()
            print('router_result:',result)

            if result == '2':
                state.next_node = "product_match"
            elif result == '3':
                state.next_node = "knowledge"
            elif result == '4':
                # 寒暄类→直接生成友好回复，不进入其他节点
                state.messages.append({
                    "role": "assistant",
                    "content": RouterNode._get_greeting_reply(state.messages[-1]["content"])
                })
                state.next_node = END
            else:
                # 非保险问题，直接返回无法回答
                state.messages.append({
                    "role": "assistant",
                    "content": "抱歉呀，我主要专注于保险相关问题的解答~ 如果你有关于保险产品、条款或基础知识的疑问，我会尽力帮你解答哦！"
                })
                state.next_node = END
        except Exception as e:
            print(e)
            state.error = f"路由处理失败: {str(e)}"
            state.messages.append({
                "role": "assistant",
                "content": "不好意思，刚才处理你的问题时出现了一点小差错，可以再问一次吗？"
            })
            state.next_node = END
        return state