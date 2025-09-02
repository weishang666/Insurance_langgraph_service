import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import State
from graph_builder import GraphBuilder
from nodes.product_matcher import ProductMatcherNode
from nodes.product_selector import ProductSelectorNode

async def test_product_matcher_single_result():
    """测试产品匹配节点（单个结果）"""
    print("\n===== 测试产品匹配节点（单个结果）=====")
    # 创建初始状态
    state = State(
        messages=[{
            "role": "user",
            "content": "平安福的保障责任有哪些？"
        }]
    )
    
    # 创建产品匹配节点并执行
    result_state = ProductMatcherNode.match(state)
    
    # 打印结果
    print(f"提取的产品关键词: {result_state.extracted_data.get('product_name_keyword')}")
    print(f"匹配的产品列表: {result_state.extracted_data.get('matched_products')}")
    print(f"下一个节点: {result_state.next_node}")
    
    return result_state

async def test_product_matcher_multiple_results():
    """测试产品匹配节点（多个结果）"""
    print("\n===== 测试产品匹配节点（多个结果）=====")
    # 创建初始状态
    state = State(
        messages=[{
            "role": "user",
            "content": "平安的保险产品有哪些？"
        }]
    )
    
    # 创建产品匹配节点并执行
    result_state = ProductMatcherNode.match(state)
    
    # 打印结果
    print(f"提取的产品关键词: {result_state.extracted_data.get('product_name_keyword')}")
    print(f"匹配的产品列表: {result_state.extracted_data.get('matched_products')}")
    print(f"下一个节点: {result_state.next_node}")
    
    # 如果有多个匹配结果，测试产品选择节点
    if result_state.next_node == "product_select":
        print("\n===== 测试产品选择节点=====")
        # 添加助手消息（产品列表）
        assistant_message = {
            "role": "assistant",
            "content": f"帮你查到{len(result_state.extracted_data['matched_products'])}款产品，你想了解哪款产品，请点击下方产品选择：\n" + \
                       "\n".join([f"{i+1}. {product}" for i, product in enumerate(result_state.extracted_data['matched_products'])]) + \
                       "\n\n请回复产品编号(1-{len(result_state.extracted_data['matched_products'])})或产品名称。"
        }
        result_state.messages.append(assistant_message)
        
        # 添加用户选择
        user_choice = {
            "role": "user",
            "content": "1"
        }
        result_state.messages.append(user_choice)
        
        # 执行产品选择节点
        result_state = ProductSelectorNode.select(result_state)
        print(f"选择后的下一个节点: {result_state.next_node}")
    
    return result_state

async def test_full_workflow():
    """测试完整工作流"""
    print("\n===== 测试完整工作流=====")
    # 构建工作流
    app = GraphBuilder.build()
    
    # 初始化对话
    config = {"configurable": {"thread_id": "test-thread-1"}}
    
    # 第一次输入：询问保险产品
    input_message = {"messages": [{"role": "user", "content": "平安福的保障责任有哪些？"}]}
    result = await app.ainvoke(input_message, config)
    print(f"第一轮对话结果: {result}")
    
    # 如果有多个产品匹配，进行选择
    if result['next_node'] == 'product_select':
        # 第二轮输入：选择产品
        input_message = {"messages": [{"role": "user", "content": "1"}]}
        result = await app.ainvoke(input_message, config)
        print(f"第二轮对话结果: {result}")
    
    return result

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_product_matcher_single_result())
    asyncio.run(test_product_matcher_multiple_results())
    # 可选：运行完整工作流测试
    # asyncio.run(test_full_workflow())