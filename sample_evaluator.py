import pandas as pd
import os
from llm_client import LLMClient
import time

def evaluate_sample_data():
    """评估样本数据"""
    print("正在初始化评估器...")
    llm_client = LLMClient()
    
    print("正在加载数据文件...")
    # 读取前10条数据进行测试
    rag_df = pd.read_csv("batch_20_results.csv", nrows=10)
    correct_df = pd.read_csv(r"D:\BaiduNetdiskDownload\code\1022_90%\insurance_qa_pairs_20251022_233322.csv")
    
    print(f"RAG结果: {len(rag_df)}条")
    print(f"正确答案: {len(correct_df)}条")
    
    results = []
    
    for index, rag_row in rag_df.iterrows():
        try:
            product_name = rag_row['产品名称']
            question = rag_row['问题']
            rag_answer = rag_row['API答案']
            
            print(f"\n处理第{index+1}条: {product_name}")
            
            # 查找对应的正确答案
            matching_rows = correct_df[
                (correct_df['产品名称'] == product_name) & 
                (correct_df['问题'] == question)
            ]
            
            if len(matching_rows) > 0:
                correct_answer = matching_rows.iloc[0]['答案']
                
                # 构建评估提示
                evaluation_prompt = f"""
请评估以下RAG系统生成的答案是否准确。

问题：{question}

正确答案：{correct_answer}

RAG系统生成的答案：{rag_answer}

请只回答"准确"、"不准确"或"部分准确"中的一个词。
"""
                
                # 调用大模型评估
                result = llm_client.generate(
                    prompt=evaluation_prompt,
                    system_prompt="你是一个专业的答案评估专家。",
                    max_tokens=20,
                    temperature=0.1
                )
                
                accuracy = result.strip()
                if "准确" in accuracy and "不准确" not in accuracy and "部分准确" not in accuracy:
                    accuracy = "准确"
                elif "不准确" in accuracy:
                    accuracy = "不准确"
                elif "部分准确" in accuracy:
                    accuracy = "部分准确"
                else:
                    accuracy = "无法判断"
                
                print(f"评估结果: {accuracy}")
                
                results.append({
                    '产品': product_name,
                    '问题': question,
                    '正确答案': correct_answer,
                    'RAG答案': rag_answer,
                    '是否准确': accuracy
                })
                
            else:
                print("未找到对应答案")
                results.append({
                    '产品': product_name,
                    '问题': question,
                    '正确答案': "未找到",
                    'RAG答案': rag_answer,
                    '是否准确': "无法评估"
                })
            
            time.sleep(1)  # 避免API限制
            
        except Exception as e:
            print(f"处理第{index+1}条时出错: {e}")
            results.append({
                '产品': rag_row.get('产品名称', '未知'),
                '问题': rag_row.get('问题', '未知'),
                '正确答案': "处理失败",
                'RAG答案': rag_row.get('API答案', '未知'),
                '是否准确': "评估失败"
            })
    
    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_csv("sample_evaluation_results.csv", index=False, encoding='utf-8-sig')
    
    print(f"\n评估完成！共处理{len(results)}条记录")
    print("结果已保存到: sample_evaluation_results.csv")
    
    # 统计信息
    accuracy_counts = result_df['是否准确'].value_counts()
    print("\n准确性分布:")
    for accuracy, count in accuracy_counts.items():
        percentage = (count / len(result_df)) * 100
        print(f"  {accuracy}: {count}条 ({percentage:.1f}%)")

if __name__ == "__main__":
    evaluate_sample_data()
