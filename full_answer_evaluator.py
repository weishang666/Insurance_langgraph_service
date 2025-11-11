import pandas as pd
import os
from llm_client import LLMClient
import time
from typing import List, Dict

class FullAnswerEvaluator:
    """完整的答案准确性评估器"""
    
    def __init__(self):
        """初始化评估器"""
        self.llm_client = LLMClient()
        
    def evaluate_answer_accuracy(self, question: str, correct_answer: str, rag_answer: str) -> str:
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
                return "准确"
            elif "不准确" in result:
                return "不准确"
            elif "部分准确" in result:
                return "部分准确"
            else:
                return "无法判断"
                
        except Exception as e:
            print(f"评估过程中出现错误: {e}")
            return "评估失败"
    
    def batch_evaluate_all(self, rag_file: str, correct_file: str, output_file: str, batch_size: int = 50):
        """批量评估所有数据"""
        print("正在加载数据文件...")
        
        # 加载RAG结果
        rag_df = pd.read_csv(rag_file)
        print(f"RAG结果文件加载完成，共{len(rag_df)}条记录")
        
        # 加载正确答案
        correct_df = pd.read_csv(correct_file)
        print(f"正确答案文件加载完成，共{len(correct_df)}条记录")
        
        # 创建评估结果列表
        all_results = []
        
        print(f"开始批量评估，每批处理{batch_size}条记录...")
        
        # 分批处理
        for batch_start in range(0, len(rag_df), batch_size):
            batch_end = min(batch_start + batch_size, len(rag_df))
            batch_df = rag_df.iloc[batch_start:batch_end]
            
            print(f"\n处理第{batch_start+1}-{batch_end}条记录...")
            
            batch_results = []
            for index, rag_row in batch_df.iterrows():
                try:
                    product_name = rag_row['产品名称']
                    question = rag_row['问题']
                    rag_answer = rag_row['API答案']
                    
                    # 在正确答案中查找对应的问题
                    matching_rows = correct_df[
                        (correct_df['产品名称'] == product_name) & 
                        (correct_df['问题'] == question)
                    ]
                    
                    if len(matching_rows) > 0:
                        correct_answer = matching_rows.iloc[0]['答案']
                        
                        print(f"  评估: {product_name} - {question[:30]}...")
                        
                        # 评估答案准确性
                        accuracy = self.evaluate_answer_accuracy(question, correct_answer, rag_answer)
                        
                        batch_results.append({
                            '产品': product_name,
                            '问题': question,
                            '正确答案': correct_answer,
                            'RAG答案': rag_answer,
                            '是否准确': accuracy
                        })
                        
                    else:
                        print(f"  未找到对应答案: {product_name} - {question[:30]}")
                        batch_results.append({
                            '产品': product_name,
                            '问题': question,
                            '正确答案': "未找到",
                            'RAG答案': rag_answer,
                            '是否准确': "无法评估"
                        })
                    
                    # 添加延迟避免API限制
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"  处理第{index+1}条记录时出错: {e}")
                    batch_results.append({
                        '产品': rag_row.get('产品名称', '未知'),
                        '问题': rag_row.get('问题', '未知'),
                        '正确答案': "处理失败",
                        'RAG答案': rag_row.get('API答案', '未知'),
                        '是否准确': "评估失败"
                    })
            
            # 保存当前批次结果
            batch_df_result = pd.DataFrame(batch_results)
            batch_output_file = f"batch_{batch_start+1}_{batch_end}_evaluation_results.csv"
            batch_df_result.to_csv(batch_output_file, index=False, encoding='utf-8-sig')
            print(f"  批次结果已保存到: {batch_output_file}")
            
            all_results.extend(batch_results)
            
            # 打印当前批次统计
            batch_accuracy_counts = batch_df_result['是否准确'].value_counts()
            print(f"  当前批次准确性分布:")
            for accuracy, count in batch_accuracy_counts.items():
                percentage = (count / len(batch_df_result)) * 100
                print(f"    {accuracy}: {count}条 ({percentage:.1f}%)")
        
        # 保存所有结果
        final_df = pd.DataFrame(all_results)
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n所有评估完成！共处理{len(all_results)}条记录")
        print(f"最终结果已保存到: {output_file}")
        
        # 打印总体统计信息
        self.print_final_statistics(final_df)
        
        return final_df
    
    def print_final_statistics(self, df: pd.DataFrame):
        """打印最终统计信息"""
        print("\n=== 最终评估统计信息 ===")
        print(f"总评估数量: {len(df)}")
        
        accuracy_counts = df['是否准确'].value_counts()
        print("\n总体准确性分布:")
        for accuracy, count in accuracy_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {accuracy}: {count}条 ({percentage:.1f}%)")
        
        # 按产品统计
        print("\n按产品统计:")
        product_stats = df.groupby('产品')['是否准确'].value_counts().unstack(fill_value=0)
        print(product_stats)
        
        # 计算准确率（准确 + 部分准确）
        accurate_count = accuracy_counts.get('准确', 0) + accuracy_counts.get('部分准确', 0)
        accuracy_rate = (accurate_count / len(df)) * 100
        print(f"\n总体准确率（准确+部分准确）: {accuracy_rate:.1f}%")

def main():
    """主函数"""
    evaluator = FullAnswerEvaluator()
    
    # 文件路径
    rag_results_file = "batch_20_results.csv"
    correct_answers_file = r"D:\BaiduNetdiskDownload\code\1022_90%\insurance_qa_pairs_20251022_233322.csv"
    output_file = "final_answer_evaluation_results.csv"
    
    # 检查文件是否存在
    if not os.path.exists(rag_results_file):
        print(f"错误: RAG结果文件不存在: {rag_results_file}")
        return
    
    if not os.path.exists(correct_answers_file):
        print(f"错误: 正确答案文件不存在: {correct_answers_file}")
        return
    
    # 执行批量评估
    try:
        result_df = evaluator.batch_evaluate_all(rag_results_file, correct_answers_file, output_file, batch_size=20)
        print(f"\n评估完成！结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"批量评估过程中出现错误: {e}")

if __name__ == "__main__":
    main()
