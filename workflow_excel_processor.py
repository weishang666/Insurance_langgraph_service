import pandas as pd
import json
import time
from graph_builder import GraphBuilder
from state import State
from langgraph.checkpoint.memory import InMemorySaver

def load_product_index_mapping(json_path):
    """加载产品索引映射JSON文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_chunk_indexes_for_product(question_data, product_name, chunk_texts):
    """
    根据召回信息和产品名，找到对应的文档块索引
    
    参数:
        question_data: JSON文件中单个产品的问题数据
        product_name: 产品名称
        chunk_texts: 召回信息中的chunk文本列表
        
    返回:
        文档块索引列表
    """
    if not question_data or "results" not in question_data:
        return []
    
    chunk_indexes = []
    
    for result in question_data.get("results", []):
        result_index = result.get("result_index")
        chunk_id = result.get("chunk_id")
        chunk_text = result.get("chunk_text", "")
        
        # 检查这个chunk是否在召回信息中
        for retrieved_chunk in chunk_texts:
            if chunk_text in retrieved_chunk or retrieved_chunk in chunk_text:
                chunk_indexes.append(result_index)
                break
    
    return sorted(list(set(chunk_indexes)))  # 去重并排序

def process_excel_with_workflow():
    """使用workflow处理Excel文件并记录召回信息"""
    import os
    
    excel_path = r"D:\BaiduNetdiskDownload\code\1022_90%\insurance_qa_pairs_20251022_233322.csv"
    index_mapping_path = r"D:\BaiduNetdiskDownload\code\1022_90%\product_query_results_insurance_fixed_chunk_20251022_182016.json"
    
    print("正在加载数据文件...")
    
    # 读取Excel文件
    df = pd.read_csv(excel_path)
    print(f"Excel文件加载完成，共{len(df)}条记录")
    
    # 加载产品索引映射
    with open(index_mapping_path, 'r', encoding='utf-8') as f:
        index_mapping = json.load(f)
    
    print(f"索引映射文件加载完成，共{index_mapping.get('total_products', 0)}个产品")
    
    # 创建内存保存器
    memory = InMemorySaver()
    
    # 创建工作流
    workflow = GraphBuilder.build(memory=memory)
    
    print("\n开始处理问题...")
    
    results = []
    session_id = "batch_processing_session"
    
    for index, row in df.iterrows():
        product_name = row['产品名称']
        question = row['问题']
        
        print(f"\n处理第{index+1}条: {product_name}")
        print(f"问题: {question}")
        question=f"产品：{product_name}	问题：{question}"
        try:
            # 创建新的会话状态
            current_state = State(
                messages=[{"role": "user", "content": question}],
                current_step="start",
                extracted_data={}
            )
            
            # 初始化product_data
            current_state.product_data = {"product_name": product_name}
            
            # 调用工作流
            result_state_dict = workflow.invoke(
                current_state.model_dump(),
                config={"configurable": {"thread_id": f"{session_id}_{index}"}}
            )
            
            # 转换为State对象
            current_state = State(**result_state_dict)
            
            # 获取答案
            answer = ""
            if current_state.messages:
                # 找到最后一个助手的回复
                for msg in reversed(current_state.messages):
                    if msg.get("role") == "assistant":
                        answer = msg.get("content", "")
                        break
            
            # 获取召回信息
            retrieved_docs = []
            chunk_indexes = []
            
            if current_state.extracted_data and 'retrieved_docs' in current_state.extracted_data:
                retrieved_docs = current_state.extracted_data['retrieved_docs']
                
                # 获取chunk文本列表
                chunk_texts = []
                if isinstance(retrieved_docs, list):
                    for doc in retrieved_docs:
                        if isinstance(doc, dict):
                            chunk_text = doc.get('content', '') or doc.get('chunkText', '')
                            if chunk_text:
                                chunk_texts.append(chunk_text)
                
                # 获取产品映射
                products_data = index_mapping.get('products', {})
                product_data = products_data.get(product_name, {})
                
                # 获取文档块索引
                chunk_indexes = get_chunk_indexes_for_product(
                    product_data, 
                    product_name, 
                    chunk_texts
                )
            
            print(f"✅ 成功获取答案")
            print(f"召回文档块数: {len(retrieved_docs)}")
            print(f"文档块索引: {', '.join(map(str, chunk_indexes))}")
            
            # 构建结果记录
            result_record = {
                '产品': product_name,
                '问题': question,
                '答案': answer,
                '召回信息': str(retrieved_docs) if retrieved_docs else '',
                '召回文档块索引': ', '.join(map(str, chunk_indexes)) if chunk_indexes else ''
            }
            
            results.append(result_record)
            
            # 添加延迟避免API限制
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ 处理第{index+1}条时出错: {e}")
            import traceback
            traceback.print_exc()
            
            error_record = {
                '产品': product_name,
                '问题': question,
                '答案': '',
                '召回信息': '',
                '召回文档块索引': ''
            }
            results.append(error_record)
    
    # 保存结果
    result_df = pd.DataFrame(results)
    output_file = "workflow_results_with_retrieval.csv"
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n所有处理完成！结果已保存到: {output_file}")
    
    # 统计信息
    success_count = len([r for r in results if r['答案']])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    return result_df

if __name__ == "__main__":
    process_excel_with_workflow()
