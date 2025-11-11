import pandas as pd
import time
from llm_client import LLMClient

def simple_excel_processor():
    """简单的Excel处理器"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 初始化LLM客户端
    llm_client = LLMClient()
    
    # 处理前5条记录
    test_df = df.head(5)
    print(f"开始处理前{len(test_df)}条记录...")
    
    results = []
    
    for index, row in test_df.iterrows():
        product_name = row['产品']
        question = row['问题']
        
        print(f"\n处理第{index+1}条: {product_name}")
        print(f"问题: {question}")
        
        # 构建提示
        prompt = f"产品：{product_name}\n问题：{question}\n请回答："
        
        # 调用LLM
        answer = llm_client.generate(prompt, max_tokens=500, temperature=0.3)
        
        print(f"答案: {answer[:100]}...")
        
        results.append({
            '产品': product_name,
            '问题': question,
            'LLM答案': answer,
            '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        time.sleep(0.5)
    
    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_excel("simple_results.xlsx", index=False)
    
    print(f"\n处理完成！结果已保存到: simple_results.xlsx")
    return result_df

if __name__ == "__main__":
    simple_excel_processor()
