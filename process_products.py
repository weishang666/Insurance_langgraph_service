#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理每个产品的第一个问题
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime

def process_first_question_per_product():
    """处理每个产品的第一个问题"""
    csv_path = r"D:\BaiduNetdiskDownload\code\1022_90%\insurance_qa_pairs_20251022_233322.csv"
    api_url = "http://127.0.0.1:8000/insurance/question-inquiry"
    
    print("🎯 处理每个产品的第一个问题")
    print("=" * 50)
    
    # 加载数据
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"📂 加载成功，共 {len(df)} 条记录")
    
    # 获取每个产品的第一个问题
    first_questions = df.groupby('产品名称').first().reset_index()
    print(f"📊 共 {len(first_questions)} 个不同产品")
    
    results = []
    
    for idx, row in first_questions.iterrows():
        product_name = row['产品名称']
        question = row['问题']
        
        print(f"\n📝 处理产品 {idx + 1}/{len(first_questions)}:")
        print(f"   产品: {product_name}")
        print(f"   问题: {question}")
        
        # 拼接问题
        full_question = f"产品：{product_name}\n问题：{question}"
        
        # 调用API
        payload = {
            "user_id": f"product_user_{idx + 1}",
            "user_question": full_question,
            "stream": False
        }
        
        print("   🔄 调用API...")
        try:
            response = requests.post(api_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 成功: {result.get('data', '')[:100]}...")
                
                # 保存结果
                result_record = {
                    '产品序号': idx + 1,
                    '产品名称': product_name,
                    '问题': question,
                    'API状态码': result.get('code', ''),
                    'API消息': result.get('message', ''),
                    'API答案': result.get('data', ''),
                    '推荐产品数': len(result.get('product_list', [])),
                    '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                results.append(result_record)
            else:
                print(f"   ❌ 失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
        
        # 延迟
        time.sleep(3)
    
    # 保存结果
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv("products_first_questions.csv", index=False, encoding='utf-8-sig')
        print(f"\n💾 结果已保存: products_first_questions.csv")
        
        success_count = len(df_results[df_results['API状态码'] == 200])
        print(f"📊 成功: {success_count}/{len(results)} 个产品")
        
        # 显示产品列表
        print(f"\n📋 处理的产品列表:")
        for idx, row in df_results.iterrows():
            status = "✅" if row['API状态码'] == 200 else "❌"
            print(f"   {status} {row['产品名称']}")
    
    print("\n🎉 处理完成！")

if __name__ == "__main__":
    process_first_question_per_product()
