from state import State
from nodes.knowledge import KnowledgeNode

# 创建一个测试状态对象
state = State()
state.messages = [{
    "role": "user",
    "content": "请问第三者在保险中是什么意思"
}]

# 测试关键词提取功能
test_query = "请问第三者在保险中是什么意思"
keywords = KnowledgeNode.extract_keywords(test_query)
print(f"提取的关键词: {keywords}")

# 测试回答功能，包含关键词定义
updated_state = KnowledgeNode.answer(state)

# 打印结果
print(f"用户查询: {state.messages[-1]['content']}")
print(f"生成的回答: {updated_state.messages[-1]['content']}")