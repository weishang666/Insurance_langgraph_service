import pandas as pd
import time
import os
from openai import OpenAI

def process_all_excel():
    """处理所有Excel数据"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 设置DeepSeek API
    api_key = "sk-30d2ad2a63574699b0b848d8ee637107"
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    results = []
    batch_size = 10  # 每批处理10条
    
    for batch_start in range(0, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))
        batch_df = df.iloc[batch_start:batch_end]
        
        print(f"\n处理第{batch_start+1}-{batch_end}条记录...")
        
        batch_results = []
        for index, row in batch_df.iterrows():
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
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是一个专业的保险顾问，擅长回答各种保险产品相关问题。请提供准确、专业的回答。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800,
                    stream=False
                )
                
                answer = response.choices[0].message.content
                print(f"  ✅ 成功")
                
                # 构建结果记录
                result_record = {
                    '产品': product_name,
                    '问题': question,
                    'LLM答案': answer,
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 保留原有列
                if '正确答案' in df.columns:
                    result_record['正确答案'] = row['正确答案']
                if '是否准确' in df.columns:
                    result_record['是否准确'] = row['是否准确']
                
                batch_results.append(result_record)
                
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                error_record = {
                    '产品': product_name,
                    '问题': question,
                    'LLM答案': f"处理失败: {str(e)}",
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if '正确答案' in df.columns:
                    error_record['正确答案'] = row['正确答案']
                if '是否准确' in df.columns:
                    error_record['是否准确'] = row['是否准确']
                
                batch_results.append(error_record)
            
            time.sleep(0.3)  # 避免API限制
        
        # 保存当前批次结果
        batch_df_result = pd.DataFrame(batch_results)
        batch_output_file = f"batch_{batch_start+1}_{batch_end}_results.xlsx"
        batch_df_result.to_excel(batch_output_file, index=False)
        print(f"  批次结果已保存到: {batch_output_file}")
        
        results.extend(batch_results)
        
        # 打印当前批次统计
        batch_success = len([r for r in batch_results if '处理失败' not in r['LLM答案']])
        batch_total = len(batch_results)
        batch_rate = (batch_success / batch_total) * 100
        print(f"  当前批次成功率: {batch_rate:.1f}% ({batch_success}/{batch_total})")
    
    # 保存所有结果
    final_df = pd.DataFrame(results)
    output_file = "all_excel_results.xlsx"
    final_df.to_excel(output_file, index=False)
    
    print(f"\n所有处理完成！结果已保存到: {output_file}")
    
    # 总体统计
    success_count = len([r for r in results if '处理失败' not in r['LLM答案']])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"总体成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    return final_df

if __name__ == "__main__":
    process_all_excel()
