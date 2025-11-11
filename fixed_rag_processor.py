import pandas as pd
import requests
import time
import os

def test_rag_api():
    """测试RAG API的请求格式"""
    api_url = "http://127.0.0.1:8000/insurance/question-inquiry"
    
    # 测试不同的请求格式
    test_cases = [
        {
            "name": "简单问题",
            "payload": {
                "user_id": "test_user",
                "user_question": "平安守护尊享成人意外险的最高投保年龄是多少？",
                "stream": False
            }
        },
        {
            "name": "带产品的问题",
            "payload": {
                "user_id": "test_user",
                "user_question": "产品：平安守护尊享成人意外险\n问题：该产品的最高投保年龄是多少？",
                "stream": False
            }
        },
        {
            "name": "最短问题",
            "payload": {
                "user_id": "test_user",
                "user_question": "你好",
                "stream": False
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试 {i+1}: {test_case['name']}")
        print(f"请求内容: {test_case['payload']['user_question']}")
        
        try:
            response = requests.post(api_url, json=test_case['payload'], timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应: {result}")
            else:
                print(f"错误响应: {response.text}")
                
        except Exception as e:
            print(f"请求异常: {e}")
        
        time.sleep(1)

def process_excel_with_fixed_api():
    """使用修复后的API处理Excel文件"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # RAG服务API地址
    api_url = "http://127.0.0.1:8000/insurance/question-inquiry"
    
    # 只处理前3条记录进行测试
    test_df = df.head(3)
    print(f"\n开始测试前{len(test_df)}条记录...")
    
    results = []
    
    for index, row in test_df.iterrows():
        product_name = row['产品']
        question = row['问题']
        
        print(f"\n处理第{index+1}条: {product_name}")
        print(f"问题: {question}")
        
        # 构建问题 - 确保不超过2000字符
        full_question = f"产品：{product_name}\n问题：{question}"
        
        # 检查长度
        if len(full_question) > 2000:
            full_question = question  # 如果太长，只使用问题部分
        
        payload = {
            "user_id": f"batch_user_{index}",
            "user_question": full_question,
            "stream": False
        }
        
        print(f"请求长度: {len(full_question)} 字符")
        
        try:
            # 调用RAG服务
            response = requests.post(api_url, json=payload, timeout=60)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"API响应代码: {result.get('code')}")
                
                if result.get('code') == 200:
                    answer = result.get('data', '')
                    product_list = result.get('product_list', [])
                    
                    print(f"✅ 成功获取答案: {answer[:100]}...")
                    print(f"推荐产品: {product_list}")
                    
                    results.append({
                        '产品': product_name,
                        '问题': question,
                        'RAG答案': answer,
                        '推荐产品数': len(product_list),
                        '推荐产品': ', '.join(product_list),
                        '查询状态': '成功',
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                else:
                    print(f"⚠️ API返回错误: {result.get('message', '')}")
                    results.append({
                        '产品': product_name,
                        '问题': question,
                        'RAG答案': '',
                        '推荐产品数': 0,
                        '推荐产品': '',
                        '查询状态': 'API错误',
                        '错误信息': result.get('message', ''),
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误详情: {response.text}")
                results.append({
                    '产品': product_name,
                    '问题': question,
                    'RAG答案': '',
                    '推荐产品数': 0,
                    '推荐产品': '',
                    '查询状态': 'HTTP错误',
                    '错误信息': f"HTTP {response.status_code}: {response.text}",
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时")
            results.append({
                '产品': product_name,
                '问题': question,
                'RAG答案': '',
                '推荐产品数': 0,
                '推荐产品': '',
                '查询状态': '超时',
                '错误信息': '请求超时',
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            print(f"❌ 异常: {e}")
            results.append({
                '产品': product_name,
                '问题': question,
                'RAG答案': '',
                '推荐产品数': 0,
                '推荐产品': '',
                '查询状态': '异常',
                '错误信息': str(e),
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        time.sleep(1)  # 避免API限制
    
    # 保存测试结果
    result_df = pd.DataFrame(results)
    result_df.to_excel("fixed_rag_test_results.xlsx", index=False)
    
    print(f"\n测试完成！结果已保存到: fixed_rag_test_results.xlsx")
    print(f"成功处理: {len([r for r in results if r['查询状态'] == '成功'])}条")
    print(f"失败处理: {len([r for r in results if r['查询状态'] != '成功'])}条")
    
    return result_df

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_rag_api()
    else:
        process_excel_with_fixed_api()
