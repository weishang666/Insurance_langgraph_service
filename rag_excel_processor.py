import pandas as pd
import requests
import time
import os
from typing import Dict, List, Any
import random
class RAGQueryProcessor:
    """RAG系统查询处理器"""
    
    def __init__(self, api_url="http://127.0.0.1:8000/insurance/question-inquiry"):
        """
        初始化RAG查询处理器
        
        参数:
            api_url: RAG系统API地址
        """
        self.api_url = api_url
        
    def query_rag_system(self, product_name: str, question: str, user_id: str = "batch_user") -> Dict[str, Any]:
        """
        查询RAG系统获取答案
        
        参数:
            product_name: 产品名称
            question: 问题
            user_id: 用户ID
            
        返回:
            包含答案的字典
        """
        # 构建完整问题
        full_question = f"产品：{product_name}\n问题：{question}"
        user_id=str(random.randint(1000, 9999))
        payload = {
            "user_id": user_id,
            "user_question": full_question,
            "stream": False
        }
        
        try:
            print(f"正在查询: {product_name} - {question[:30]}...")
            
            response = requests.post(self.api_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    print(f"✅ 成功获取答案")
                    return {
                        "status": "success",
                        "answer": result.get('data', ''),
                        "product_list": result.get('product_list', []),
                        "raw_response": result
                    }
                else:
                    print(f"⚠️ API返回错误: {result.get('message', '')}")
                    return {
                        "status": "api_error",
                        "answer": "",
                        "product_list": [],
                        "error_message": result.get('message', ''),
                        "raw_response": result
                    }
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return {
                    "status": "http_error",
                    "answer": "",
                    "product_list": [],
                    "error_message": f"HTTP {response.status_code}",
                    "raw_response": None
                }
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时")
            return {
                "status": "timeout",
                "answer": "",
                "product_list": [],
                "error_message": "请求超时",
                "raw_response": None
            }
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return {
                "status": "exception",
                "answer": "",
                "product_list": [],
                "error_message": str(e),
                "raw_response": None
            }
    
    def process_excel_file(self, excel_path: str, output_path: str = None, batch_size: int = 10):
        """
        处理Excel文件中的问题
        
        参数:
            excel_path: Excel文件路径
            output_path: 输出文件路径
            batch_size: 批处理大小
        """
        print(f"正在读取Excel文件: {excel_path}")
        
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        print(f"文件读取完成，共{len(df)}条记录")
        print(f"列名: {df.columns.tolist()}")
        
        # 检查必要的列
        required_columns = ['产品', '问题']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"错误: 缺少必要的列: {missing_columns}")
            return None
        
        # 创建结果列表
        results = []
        
        print(f"开始处理，每批处理{batch_size}条记录...")
        
        # 分批处理
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size, len(df))
            batch_df = df.iloc[batch_start:batch_end]
            
            print(f"\n处理第{batch_start+1}-{batch_end}条记录...")
            
            batch_results = []
            for index, row in batch_df.iterrows():
                try:
                    product_name = row['产品']
                    question = row['问题']
                    
                    # 查询RAG系统
                    result = self.query_rag_system(product_name, question)
                    
                    # 构建结果记录
                    result_record = {
                        '产品': product_name,
                        '问题': question,
                        'RAG答案': result.get('answer', ''),
                        '查询状态': result.get('status', ''),
                        '错误信息': result.get('error_message', ''),
                        '推荐产品数': len(result.get('product_list', [])),
                        '推荐产品': ', '.join(result.get('product_list', [])),
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 如果原文件有正确答案列，保留它
                    if '正确答案' in df.columns:
                        result_record['正确答案'] = row['正确答案']
                    
                    # 如果原文件有是否准确列，保留它
                    if '是否准确' in df.columns:
                        result_record['是否准确'] = row['是否准确']
                    
                    batch_results.append(result_record)
                    
                    # 添加延迟避免API限制
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"处理第{index+1}条记录时出错: {e}")
                    error_record = {
                        '产品': row.get('产品', '未知'),
                        '问题': row.get('问题', '未知'),
                        'RAG答案': '',
                        '查询状态': '处理失败',
                        '错误信息': str(e),
                        '推荐产品数': 0,
                        '推荐产品': '',
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if '正确答案' in df.columns:
                        error_record['正确答案'] = row.get('正确答案', '')
                    if '是否准确' in df.columns:
                        error_record['是否准确'] = row.get('是否准确', '')
                    
                    batch_results.append(error_record)
            
            # 保存当前批次结果
            batch_df_result = pd.DataFrame(batch_results)
            batch_output_file = f"batch_{batch_start+1}_{batch_end}_rag_results_new_new.xlsx"
            batch_df_result.to_excel(batch_output_file, index=False)
            print(f"批次结果已保存到: {batch_output_file}")
            
            results.extend(batch_results)
            
            # 打印当前批次统计
            batch_status_counts = batch_df_result['查询状态'].value_counts()
            print(f"当前批次状态分布:")
            for status, count in batch_status_counts.items():
                percentage = (count / len(batch_df_result)) * 100
                print(f"  {status}: {count}条 ({percentage:.1f}%)")
        
        # 保存所有结果
        final_df = pd.DataFrame(results)
        
        if output_path is None:
            output_path = "rag_query_results.xlsx"
        
        final_df.to_excel(output_path, index=False)
        
        print(f"\n所有处理完成！共处理{len(results)}条记录")
        print(f"最终结果已保存到: {output_path}")
        
        # 打印总体统计信息
        self.print_final_statistics(final_df)
        
        return final_df
    
    def print_final_statistics(self, df: pd.DataFrame):
        """打印最终统计信息"""
        print("\n=== 最终处理统计信息 ===")
        print(f"总处理数量: {len(df)}")
        
        status_counts = df['查询状态'].value_counts()
        print("\n查询状态分布:")
        for status, count in status_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {status}: {count}条 ({percentage:.1f}%)")
        
        # 按产品统计
        print("\n按产品统计:")
        product_stats = df.groupby('产品')['查询状态'].value_counts().unstack(fill_value=0)
        print(product_stats)
        
        # 计算成功率
        success_count = status_counts.get('success', 0)
        success_rate = (success_count / len(df)) * 100
        print(f"\n查询成功率: {success_rate:.1f}%")

def main():
    """主函数"""
    processor = RAGQueryProcessor()
    
    # Excel文件路径
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    output_path = "rag_query_results_测评1023.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"错误: Excel文件不存在: {excel_path}")
        return
    
    # 执行处理
    try:
        result_df = processor.process_excel_file(excel_path, output_path, batch_size=5)
        print(f"\n处理完成！结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    main()
