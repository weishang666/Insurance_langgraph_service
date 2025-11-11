import pandas as pd
import time
import os
from llm_client import LLMClient

def process_excel_with_llm():
    """使用LLM直接处理Excel文件中的问题"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 初始化LLM客户端
    print("正在初始化LLM客户端...")
    llm_client = LLMClient()
    
    # 只处理前10条记录进行测试
    test_df = df.head(10)
    
    print(f"\n开始处理前{len(test_df)}条记录...")
    
    results = []
    
    for index, row in test_df.iterrows():
        try:
            product_name = row['产品']
            question = row['问题']
            
            print(f"\n处理第{index+1}条: {product_name}")
            print(f"问题: {question}")
            
            # 构建提示
            prompt = f"""
请回答以下关于保险产品的问题：

产品名称：{product_name}
问题：{question}

请提供准确、详细的回答。
"""
            
            system_prompt = "你是一个专业的保险顾问，擅长回答各种保险产品相关问题。请提供准确、专业的回答。"
            
            # 调用LLM生成答案
            answer = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            print(f"✅ 成功生成答案: {answer[:100]}...")
            
            # 构建结果记录
            result_record = {
                '产品': product_name,
                '问题': question,
                'LLM答案': answer,
                '查询状态': '成功',
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 如果原文件有正确答案列，保留它
            if '正确答案' in df.columns:
                result_record['正确答案'] = row['正确答案']
            
            # 如果原文件有是否准确列，保留它
            if '是否准确' in df.columns:
                result_record['是否准确'] = row['是否准确']
            
            results.append(result_record)
            
            time.sleep(0.5)  # 避免API限制
            
        except Exception as e:
            print(f"❌ 处理第{index+1}条时出错: {e}")
            error_record = {
                '产品': row.get('产品', '未知'),
                '问题': row.get('问题', '未知'),
                'LLM答案': '',
                '查询状态': '处理失败',
                '错误信息': str(e),
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if '正确答案' in df.columns:
                error_record['正确答案'] = row.get('正确答案', '')
            if '是否准确' in df.columns:
                error_record['是否准确'] = row.get('是否准确', '')
            
            results.append(error_record)
    
    # 保存结果
    result_df = pd.DataFrame(results)
    output_file = "llm_excel_results.xlsx"
    result_df.to_excel(output_file, index=False)
    
    print(f"\n处理完成！结果已保存到: {output_file}")
    
    # 统计信息
    success_count = len([r for r in results if r['查询状态'] == '成功'])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"成功处理: {success_count}条")
    print(f"失败处理: {total_count - success_count}条")
    print(f"成功率: {success_rate:.1f}%")
    
    return result_df

def process_all_excel_with_llm():
    """处理所有Excel数据"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 初始化LLM客户端
    print("正在初始化LLM客户端...")
    llm_client = LLMClient()
    
    print(f"\n开始处理所有{len(df)}条记录...")
    
    results = []
    batch_size = 20  # 每批处理20条
    
    for batch_start in range(0, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))
        batch_df = df.iloc[batch_start:batch_end]
        
        print(f"\n处理第{batch_start+1}-{batch_end}条记录...")
        
        batch_results = []
        for index, row in batch_df.iterrows():
            try:
                product_name = row['产品']
                question = row['问题']
                
                print(f"  处理: {product_name} - {question[:30]}...")
                
                # 构建提示
                prompt = f"""
请回答以下关于保险产品的问题：

产品名称：{product_name}
问题：{question}

请提供准确、详细的回答。
"""
                
                system_prompt = "你是一个专业的保险顾问，擅长回答各种保险产品相关问题。请提供准确、专业的回答。"
                
                # 调用LLM生成答案
                answer = llm_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=1000,
                    temperature=0.3
                )
                
                # 构建结果记录
                result_record = {
                    '产品': product_name,
                    '问题': question,
                    'LLM答案': answer,
                    '查询状态': '成功',
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 保留原有列
                if '正确答案' in df.columns:
                    result_record['正确答案'] = row['正确答案']
                if '是否准确' in df.columns:
                    result_record['是否准确'] = row['是否准确']
                
                batch_results.append(result_record)
                
                time.sleep(0.3)  # 避免API限制
                
            except Exception as e:
                print(f"  处理第{index+1}条时出错: {e}")
                error_record = {
                    '产品': row.get('产品', '未知'),
                    '问题': row.get('问题', '未知'),
                    'LLM答案': '',
                    '查询状态': '处理失败',
                    '错误信息': str(e),
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if '正确答案' in df.columns:
                    error_record['正确答案'] = row.get('正确答案', '')
                if '是否准确' in df.columns:
                    error_record['是否准确'] = row.get('是否准确', '')
                
                batch_results.append(error_record)
        
        # 保存当前批次结果
        batch_df_result = pd.DataFrame(batch_results)
        batch_output_file = f"batch_{batch_start+1}_{batch_end}_llm_results.xlsx"
        batch_df_result.to_excel(batch_output_file, index=False)
        print(f"  批次结果已保存到: {batch_output_file}")
        
        results.extend(batch_results)
        
        # 打印当前批次统计
        batch_success = len([r for r in batch_results if r['查询状态'] == '成功'])
        batch_total = len(batch_results)
        batch_rate = (batch_success / batch_total) * 100
        print(f"  当前批次成功率: {batch_rate:.1f}% ({batch_success}/{batch_total})")
    
    # 保存所有结果
    final_df = pd.DataFrame(results)
    output_file = "all_llm_excel_results.xlsx"
    final_df.to_excel(output_file, index=False)
    
    print(f"\n所有处理完成！结果已保存到: {output_file}")
    
    # 总体统计
    success_count = len([r for r in results if r['查询状态'] == '成功'])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"总体成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    return final_df

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        process_all_excel_with_llm()
    else:
        process_excel_with_llm()
