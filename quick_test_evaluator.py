import pandas as pd
import os
from llm_client import LLMClient
import time

class AnswerEvaluator:
    """答案准确性评估器"""
    
    def __init__(self):
        """初始化评估器"""
        self.llm_client = LLMClient()
        
    def evaluate_answer_accuracy(self, question: str, correct_answer: str, rag_answer: str) -> dict:
        """使用大模型评估RAG答案的准确性"""
        evaluation_prompt = f"""
请评估以下RAG系统生成的答案是否准确。

问题：{question}

正确答案：{correct_answer}

RAG系统生成的答案：{rag_answer}

请从以下几个维度进行评估：
1. 信息准确性：RAG答案中的关键信息是否与正确答案一致
2. 完整性：RAG答案是否包含了正确答案的主要要点
3. 相关性：RAG答案是否直接回答了问题

请给出最终判断：
- 如果RAG答案在信息准确性、完整性和相关性方面都表现良好，请回答"准确"
- 如果RAG答案存在明显错误、遗漏重要信息或偏离问题，请回答"不准确"
- 如果RAG答案部分正确但存在一些问题，请回答"部分准确"

请只回答"准确"、"不准确"或"部分准确"中的一个词。
"""

        try:
            result = self.llm_client.generate(
                prompt=evaluation_prompt,
                system_prompt="你是一个专业的答案评估专家，能够客观准确地评估答案质量。",
                max_tokens=50,
                temperature=0.1
            )
            
            result = result.strip().lower()
            if "准确" in result and "不准确" not in result and "部分准确" not in result:
                accuracy = "准确"
            elif "不准确" in result:
                accuracy = "不准确"
            elif "部分准确" in result:
                accuracy = "部分准确"
            else:
                accuracy = "无法判断"
                
            return {
                "accuracy": accuracy,
                "raw_result": result
            }
            
        except Exception as e:
            print(f"评估过程中出现错误: {e}")
            return {
                "accuracy": "评估失败",
                "raw_result": f"错误: {str(e)}"
            }

def quick_evaluate_sample():
    """快速评估样本数据"""
    evaluator = AnswerEvaluator()
    
    # 读取少量数据进行测试
    rag_df = pd.read_csv("batch_20_results.csv", nrows=5)
    correct_df = pd.read_csv(r"D:\BaiduNetdiskDownload\code\1022_90%\insurance_qa_pairs_20251022_233322.csv")
    
    print("=== 快速评估测试 ===")
    
    for index, rag_row in rag_df.iterrows():
        product_name = rag_row['产品名称']
        question = rag_row['问题']
        rag_answer = rag_row['API答案']
        
        # 查找对应的正确答案
        matching_rows = correct_df[
            (correct_df['产品名称'] == product_name) & 
            (correct_df['问题'] == question)
        ]
        
        if len(matching_rows) > 0:
            correct_answer = matching_rows.iloc[0]['答案']
            
            print(f"\n--- 测试 {index+1} ---")
            print(f"产品: {product_name}")
            print(f"问题: {question}")
            print(f"正确答案: {correct_answer[:100]}...")
            print(f"RAG答案: {rag_answer[:100]}...")
            
            # 评估
            evaluation = evaluator.evaluate_answer_accuracy(question, correct_answer, rag_answer)
            print(f"评估结果: {evaluation['accuracy']}")
            
            time.sleep(1)  # 避免API限制
        else:
            print(f"\n未找到对应答案: {product_name} - {question}")

if __name__ == "__main__":
    quick_evaluate_sample()
