from langgraph.graph import StateGraph as Graph, END
from langgraph.checkpoint.memory import InMemorySaver
from state import State
from nodes import RetrieverNode, GeneratorNode, RouterNode, KnowledgeNode, ProductMatcherNode, ProductSelectorNode, IntentRewriterNode

class GraphBuilder:
    @staticmethod
    def build(memory=None):
        workflow = Graph(State)
        
        # 添加意图改写节点
        workflow.add_node("intent_rewriter", IntentRewriterNode.rewrite)
        
        # 添加路由节点
        workflow.add_node("router", RouterNode.route)
        
        # 添加产品匹配节点
        workflow.add_node("product_match", ProductMatcherNode.match)
        
        # 添加产品选择节点
        workflow.add_node("product_select", ProductSelectorNode.select)
        
        # 添加检索节点
        workflow.add_node("retrieve", RetrieverNode.retrieve)
        
        # 添加生成节点
        workflow.add_node("generate", GeneratorNode.generate)

        # 添加保险通用知识节点
        workflow.add_node("knowledge", KnowledgeNode.answer)
        
        # 设置条件边（关键修改）
        workflow.add_conditional_edges(
            source="router",  # 从 router 节点出发
            path=lambda state: state.next_node,  # 从state对象中提取next_node属性作为下一个节点名
            path_map={"product_match": "product_match", "retrieve": "retrieve", "knowledge": "knowledge", "product_select": "product_select", END: END}
        )
        
        # 添加产品匹配节点到其他节点的条件边
        workflow.add_conditional_edges(
            source="product_match",
            path=lambda state: state.next_node,
            path_map={"retrieve": "retrieve", "product_select": "product_select", "knowledge": "knowledge", END: END}
        )
        
        # 设置起始节点
        workflow.set_entry_point("intent_rewriter")
        # 添加意图改写节点到其他节点的条件边
        workflow.add_conditional_edges(
            source="intent_rewriter",
            path=lambda state: state.next_node,
            path_map={"router": "router", END: END}
        )
        # 添加检索节点到生成节点的条件边
        workflow.add_conditional_edges(
            source="retrieve",
            path=lambda state: END if state.error else "generate",
            path_map={"generate": "generate", END: END}
        )
        workflow.add_edge("generate", END)  # 生成节点 → 结束
        workflow.add_edge("knowledge", END)  # 知识节点 → 结束
        # 产品选择节点 → 路由节点
        
        # 使用外部提供的memory或创建默认的
        if memory is None:
            memory = InMemorySaver()
        
        return workflow.compile(checkpointer=memory)