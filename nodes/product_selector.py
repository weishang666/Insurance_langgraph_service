from state import State

class ProductSelectorNode:
    @staticmethod
    def select(state: State) -> State:
        """展示匹配到的多个产品，让用户选择具体产品"""
        try:
            # 更新当前节点
            state.current_node = "product_select"
            
            # 检查是否有匹配的产品
            # if not state.extracted_data or not state.extracted_data.get("matched_products"):
            #     state.error = "没有找到匹配的产品列表"
            #     state.next_node = "knowledge"
            #     return state
            print('************')
            matched_products = state.product_data["matched_products"]
            print("matched_products",matched_products)
            # 生成产品选择提示
            product_list = "\n".join([f"{i+1}. {product}" for i, product in enumerate(matched_products)])
            prompt = f"帮你查到{len(matched_products)}款产品，你想了解哪款产品，请点击下方产品选择：\n{product_list}\n\n请回复产品编号(1-{len(matched_products)})或产品名称。"
            
            # 添加到消息历史
            state.messages.append({
                "role": "assistant",
                "content": prompt
            })
            
            # 设置下一个节点为结束节点
            state.next_node = "end"
            
            print(f"ProductSelectorNode: 已展示{len(matched_products)}个产品供选择")
            return state
        except Exception as e:
            error_msg = f"产品选择失败: {str(e)}"
            state.error = error_msg
            print(f"ProductSelectorNode: 错误 - {error_msg}")
            state.next_node = "knowledge"
            return state