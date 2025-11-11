import pandas as pd
import time
import os
from openai import OpenAI

def quick_excel_test():
    """快速Excel测试"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 设置DeepSeek API
    api_key = "sk-30d2ad2a63574699b0b848d8ee637107"
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # 只处理第1条记录
    row = df.iloc[0]
    product_name = row['产品']
    question = row['问题']
    
    print(f"\n处理: {product_name}")
    print(f"问题: {question}")
    
    # 构建提示
    prompt = f"产品：{product_name}\n问题：{question}\n请回答："
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是保险专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        print(f"✅ 答案: {answer}")
        
        # 保存结果
        result = pd.DataFrame([{
            '产品': product_name,
            '问题': question,
            'LLM答案': answer,
            '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
        }])
        
        result.to_excel("quick_test_result.xlsx", index=False)
        print("结果已保存到: quick_test_result.xlsx")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    quick_excel_test()
