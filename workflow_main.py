import sys
from graph_builder import GraphBuilder
from state import State
from langgraph.checkpoint.memory import InMemorySaver

# 创建内存保存器
memory = InMemorySaver()

# 创建工作流，并绑定内存
workflow = GraphBuilder.build(memory=memory)

# 会话 ID
SESSION_ID = "test_memory_session1"

def main():
    print("保险问答助手（invoke 版，带短期记忆）")
    print("输入 '退出' 结束对话")

    current_state = State(
        messages=[],
        current_step="start",
        extracted_data={}
    )

    while True:
        user_input = input("用户: ")
        if user_input.lower() == '退出':
            print("再见！")
            break

        # 更新本地的消息历史
        current_state.messages.append({"role": "user", "content": user_input})

        # 调用工作流，传入当前状态，并指定 thread_id
        result_state_dict = workflow.invoke(
            current_state.model_dump(),
            config={"configurable": {"thread_id": SESSION_ID}}
        )

        # 打印 invoke 结果
        # print("invoke 结果:")
        # print(result_state_dict)

        # 转成 State 对象
        current_state = State(**result_state_dict)

        # 输出助手最新回复
        last_message = current_state.messages[-1]
        if last_message["role"] == "assistant":
            print(f"助手: {last_message['content']}")

        # 如果有提取到产品名
        if "product_name" in current_state.extracted_data:
            print(f"提取的产品名称: {current_state.extracted_data['product_name']}")

if __name__ == "__main__":
    main()
