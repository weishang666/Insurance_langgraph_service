import pandas as pd
import requests
import time
import os

def quick_test_rag():
    """快速测试RAG系统"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 只处理前3条记录进行测试
    test_df = df.head(3)
    
    print("\n开始测试前3条记录...")
    
    results = []
    api_url = "http://127.0.0.1:8000/insurance/question-inquiry"
    
    for index, row in test_df.iterrows():
        try:
            product_name = row['产品']
            question = row['问题']
            
            print(f"\n处理第{index+1}条: {product_name}")
            print(f"问题: {question}")
            
            # 构建完整问题
            full_question = f"产品：{product_name}\n问题：{question}"
            
            payload = {
                "user_id": "test_user",
                "user_question": full_question,
                "stream": False
            }
            
            # 查询RAG系统
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    answer = result.get('data', '')
                    print(f"✅ 成功获取答案: {answer[:100]}...")
                    
                    results.append({
                        '产品': product_name,
                        '问题': question,
                        'RAG答案': answer,
                        '查询状态': '成功',
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                else:
                    print(f"⚠️ API返回错误: {result.get('message', '')}")
                    results.append({
                        '产品': product_name,
                        '问题': question,
                        'RAG答案': '',
                        '查询状态': 'API错误',
                        '错误信息': result.get('message', ''),
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                results.append({
                    '产品': product_name,
                    '问题': question,
                    'RAG答案': '',
                    '查询状态': 'HTTP错误',
                    '错误信息': f"HTTP {response.status_code}",
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            time.sleep(1)  # 避免API限制
            
        except Exception as e:
            print(f"❌ 处理第{index+1}条时出错: {e}")
            results.append({
                '产品': row.get('产品', '未知'),
                '问题': row.get('问题', '未知'),
                'RAG答案': '',
                '查询状态': '处理失败',
                '错误信息': str(e),
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # 保存测试结果
    result_df = pd.DataFrame(results)
    result_df.to_excel("quick_test_rag_results.xlsx", index=False)
    
    print(f"\n测试完成！结果已保存到: quick_test_rag_results.xlsx")
    print(f"成功处理: {len([r for r in results if r['查询状态'] == '成功'])}条")
    print(f"失败处理: {len([r for r in results if r['查询状态'] != '成功'])}条")

if __name__ == "__main__":
    quick_test_rag()
