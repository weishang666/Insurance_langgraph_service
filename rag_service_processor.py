import pandas as pd
import requests
import time
import os

def process_excel_with_rag_service():
    """使用RAG服务处理Excel文件"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # RAG服务API地址
    api_url = "http://127.0.0.1:8000/insurance/question-inquiry"
    
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
            
            # 构建完整问题
            full_question = f"产品：{product_name}\n问题：{question}"
            
            payload = {
                "user_id": f"batch_user_{index}",
                "user_question": full_question,
                "stream": False
            }
            
            try:
                # 调用RAG服务
                response = requests.post(api_url, json=payload, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 200:
                        answer = result.get('data', '')
                        product_list = result.get('product_list', [])
                        
                        print(f"  ✅ 成功获取答案")
                        
                        # 构建结果记录
                        result_record = {
                            '产品': product_name,
                            '问题': question,
                            'RAG答案': answer,
                            '推荐产品数': len(product_list),
                            '推荐产品': ', '.join(product_list),
                            '查询状态': '成功',
                            '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 保留原有列
                        if '正确答案' in df.columns:
                            result_record['正确答案'] = row['正确答案']
                        if '是否准确' in df.columns:
                            result_record['是否准确'] = row['是否准确']
                        
                        batch_results.append(result_record)
                        
                    else:
                        print(f"  ⚠️ API返回错误: {result.get('message', '')}")
                        error_record = {
                            '产品': product_name,
                            '问题': question,
                            'RAG答案': '',
                            '推荐产品数': 0,
                            '推荐产品': '',
                            '查询状态': 'API错误',
                            '错误信息': result.get('message', ''),
                            '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        if '正确答案' in df.columns:
                            error_record['正确答案'] = row['正确答案']
                        if '是否准确' in df.columns:
                            error_record['是否准确'] = row['是否准确']
                        
                        batch_results.append(error_record)
                        
                else:
                    print(f"  ❌ HTTP错误: {response.status_code}")
                    error_record = {
                        '产品': product_name,
                        '问题': question,
                        'RAG答案': '',
                        '推荐产品数': 0,
                        '推荐产品': '',
                        '查询状态': 'HTTP错误',
                        '错误信息': f"HTTP {response.status_code}",
                        '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if '正确答案' in df.columns:
                        error_record['正确答案'] = row['正确答案']
                    if '是否准确' in df.columns:
                        error_record['是否准确'] = row['是否准确']
                    
                    batch_results.append(error_record)
                    
            except requests.exceptions.Timeout:
                print(f"  ⏰ 请求超时")
                error_record = {
                    '产品': product_name,
                    '问题': question,
                    'RAG答案': '',
                    '推荐产品数': 0,
                    '推荐产品': '',
                    '查询状态': '超时',
                    '错误信息': '请求超时',
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if '正确答案' in df.columns:
                    error_record['正确答案'] = row['正确答案']
                if '是否准确' in df.columns:
                    error_record['是否准确'] = row['是否准确']
                
                batch_results.append(error_record)
                
            except Exception as e:
                print(f"  ❌ 异常: {e}")
                error_record = {
                    '产品': product_name,
                    '问题': question,
                    'RAG答案': '',
                    '推荐产品数': 0,
                    '推荐产品': '',
                    '查询状态': '异常',
                    '错误信息': str(e),
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if '正确答案' in df.columns:
                    error_record['正确答案'] = row['正确答案']
                if '是否准确' in df.columns:
                    error_record['是否准确'] = row['是否准确']
                
                batch_results.append(error_record)
            
            time.sleep(0.5)  # 避免API限制
        
        # 保存当前批次结果
        batch_df_result = pd.DataFrame(batch_results)
        batch_output_file = f"rag_batch_{batch_start+1}_{batch_end}_results.xlsx"
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
    output_file = "rag_excel_results.xlsx"
    final_df.to_excel(output_file, index=False)
    
    print(f"\n所有处理完成！结果已保存到: {output_file}")
    
    # 总体统计
    success_count = len([r for r in results if r['查询状态'] == '成功'])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"总体成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    # 按产品统计
    print("\n按产品统计:")
    product_stats = final_df.groupby('产品')['查询状态'].value_counts().unstack(fill_value=0)
    print(product_stats)
    
    return final_df

def quick_test_rag():
    """快速测试RAG服务"""
    excel_path = r"C:\Users\Admin\Desktop\测评1023.xlsx"
    
    print("正在读取Excel文件...")
    df = pd.read_excel(excel_path)
    print(f"文件读取完成，共{len(df)}条记录")
    
    # 只处理前3条记录进行测试
    test_df = df.head(3)
    
    print(f"\n开始测试前{len(test_df)}条记录...")
    
    api_url = "http://127.0.0.1:8000/insurance/question-inquiry"
    results = []
    
    for index, row in test_df.iterrows():
        product_name = row['产品']
        question = row['问题']
        
        print(f"\n处理第{index+1}条: {product_name}")
        print(f"问题: {question}")
        
        # 构建完整问题
        full_question = f"产品：{product_name}\n问题：{question}"
        
        payload = {
            "user_id": f"test_user_{index}",
            "user_question": full_question,
            "stream": False
        }
        
        try:
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
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
                results.append({
                    '产品': product_name,
                    '问题': question,
                    'RAG答案': '',
                    '推荐产品数': 0,
                    '推荐产品': '',
                    '查询状态': 'HTTP错误',
                    '错误信息': f"HTTP {response.status_code}",
                    '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            time.sleep(1)  # 避免API限制
            
        except Exception as e:
            print(f"❌ 处理第{index+1}条时出错: {e}")
            results.append({
                '产品': product_name,
                '问题': question,
                'RAG答案': '',
                '推荐产品数': 0,
                '推荐产品': '',
                '查询状态': '处理失败',
                '错误信息': str(e),
                '处理时间': time.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # 保存测试结果
    result_df = pd.DataFrame(results)
    result_df.to_excel("rag_test_results.xlsx", index=False)
    
    print(f"\n测试完成！结果已保存到: rag_test_results.xlsx")
    print(f"成功处理: {len([r for r in results if r['查询状态'] == '成功'])}条")
    print(f"失败处理: {len([r for r in results if r['查询状态'] != '成功'])}条")
    
    return result_df

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test_rag()
    else:
        process_excel_with_rag_service()
