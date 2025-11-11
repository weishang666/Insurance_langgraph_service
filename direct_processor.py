import pandas as pd
import time
import os

# 直接使用DeepSeek API
import os
from openai import OpenAI

def process_excel_directly():
    """直接处理Excel文件"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 设置DeepSeek API
    api_key = "sk-30d2ad2a63574699b0b848d8ee637107"
    os.environ['DEEPSEEK_API_KEY'] = api_key
    
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )
    
    # 处理前3条记录进行测试
    test_df = df.head(3)
    print(f"开始处理前{len(test_df)}条记录...")
    
    results = []
    
    for index, row in test_df.iterrows():
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
        
        try:
            # 调用DeepSeek API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的保险顾问，擅长回答各种保险产品相关问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                stream=False
            )
            
            answer = response.choices[0].message.content
            print(f"✅ 成功生成答案: {answer[:100]}...")
            
            results.append({
                '产品': product_name,
                '问题': question,
                'LLM答案': answer,
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            results.append({
                '产品': product_name,
                '问题': question,
                'LLM答案': f"处理失败: {str(e)}",
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        time.sleep(0.5)  # 避免API限制
    
    # 保存结果
    result_df = pd.DataFrame(results)
    output_file = "direct_excel_results.xlsx"
    result_df.to_excel(output_file, index=False)
    
    print(f"\n处理完成！结果已保存到: {output_file}")
    return result_df

if __name__ == "__main__":
    process_excel_directly()
