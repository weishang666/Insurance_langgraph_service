#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理保险问答CSV文件
支持demo模式和全量模式
"""

import pandas as pd
import requests
import json
import time
from tqdm import tqdm
import os
from datetime import datetime

class BatchQAProcessor:
    def __init__(self, csv_path, api_url="http://127.0.0.1:8000/insurance/question-inquiry"):
        self.csv_path = csv_path
        self.api_url = api_url
        self.results = []
        self.failed_count = 0
        self.success_count = 0
        
    def load_csv(self):
        """加载CSV文件"""
        print(f"📂 加载CSV文件: {self.csv_path}")
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            print(f"✅ 成功加载 {len(self.df)} 条记录")
            return True
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False
    
    def call_api_with_retry(self, product_name, question, user_id, max_retries=3):
        """带重试的API调用"""
        full_question = f"产品：{product_name}\n问题：{question}"
        payload = {
            "user_id": user_id,
            "user_question": full_question,
            "stream": False
        }
        
        for attempt in range(max_retries):
            try:
                print(f"   🔄 尝试 {attempt + 1}/{max_retries}...")
                response = requests.post(self.api_url, json=payload, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 200:
                        print(f"   ✅ 成功获取答案")
                        return result
                    else:
                        print(f"   ⚠️ API返回错误: {result.get('message', '')}")
                        return result
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏰ 请求超时 (尝试 {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"   ❌ 请求异常: {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"   ⏳ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        # 所有重试都失败
        return {
            "code": 500,
            "message": "所有重试都失败",
            "data": None,
            "product_list": []
        }
    
    def process_demo(self, num_samples=3):
        """处理demo数据"""
        print(f"\n🎯 开始Demo处理（前{num_samples}条）")
        print("=" * 60)
        
        demo_df = self.df.head(num_samples)
        self.results = []
        
        for idx, row in tqdm(demo_df.iterrows(), total=len(demo_df), desc="Demo处理"):
            product_name = row['产品名称']
            question = row['问题']
            
            print(f"\n📝 处理第 {idx + 1} 条:")
            print(f"   产品: {product_name}")
            print(f"   问题: {question}")
            
            # 调用API
            result = self.call_api_with_retry(product_name, question, f"demo_user_{idx + 1}")
            
            # 保存结果
            result_record = {
                '原始行号': idx + 1,
                '产品名称': product_name,
                '问题': question,
                'API状态码': result.get('code', ''),
                'API消息': result.get('message', ''),
                'API答案': result.get('data', ''),
                '推荐产品数': len(result.get('product_list', [])),
                '推荐产品': json.dumps(result.get('product_list', []), ensure_ascii=False),
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.results.append(result_record)
            
            if result.get('code') == 200:
                self.success_count += 1
                print(f"   ✅ 成功: {result.get('data', '')[:50]}...")
            else:
                self.failed_count += 1
                print(f"   ❌ 失败: {result.get('message', '')}")
            
            # 延迟
            time.sleep(2)
        
        # 保存结果
        self.save_results("demo_results.csv")
        self.print_summary()
    
    def process_batch(self, start_idx=0, batch_size=10):
        """处理批次数据"""
        end_idx = min(start_idx + batch_size, len(self.df))
        batch_df = self.df.iloc[start_idx:end_idx]
        
        print(f"\n📦 处理批次 {start_idx + 1}-{end_idx} (共{len(batch_df)}条)")
        
        for idx, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc=f"批次{start_idx//batch_size + 1}"):
            product_name = row['产品名称']
            question = row['问题']
            
            # 调用API
            result = self.call_api_with_retry(product_name, question, f"batch_user_{idx + 1}")
            
            # 保存结果
            result_record = {
                '原始行号': idx + 1,
                '产品名称': product_name,
                '问题': question,
                'API状态码': result.get('code', ''),
                'API消息': result.get('message', ''),
                'API答案': result.get('data', ''),
                '推荐产品数': len(result.get('product_list', [])),
                '推荐产品': json.dumps(result.get('product_list', []), ensure_ascii=False),
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.results.append(result_record)
            
            if result.get('code') == 200:
                self.success_count += 1
            else:
                self.failed_count += 1
            
            # 延迟
            time.sleep(1)
        
        # 保存批次结果
        batch_filename = f"batch_{start_idx//batch_size + 1}_results.csv"
        self.save_results(batch_filename)
        print(f"💾 批次结果已保存: {batch_filename}")
    
    def process_all(self, batch_size=10):
        """处理全量数据"""
        print(f"\n🚀 开始全量处理（共{len(self.df)}条，批次大小{batch_size}）")
        print("=" * 60)
        
        total_batches = (len(self.df) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            self.process_batch(start_idx, batch_size)
            
            print(f"📊 进度: {batch_idx + 1}/{total_batches} 批次完成")
            print(f"✅ 成功: {self.success_count}, ❌ 失败: {self.failed_count}")
            
            # 批次间延迟
            if batch_idx < total_batches - 1:
                print("⏳ 批次间休息5秒...")
                time.sleep(5)
        
        # 保存最终结果
        self.save_results("final_results.csv")
        self.print_summary()
    
    def save_results(self, filename):
        """保存结果"""
        if not self.results:
            print("⚠️ 没有结果需要保存")
            return
        
        df_results = pd.DataFrame(self.results)
        df_results.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 结果已保存: {filename}")
    
    def print_summary(self):
        """打印统计信息"""
        total = self.success_count + self.failed_count
        if total > 0:
            success_rate = self.success_count / total * 100
            print(f"\n📊 处理统计:")
            print(f"   总计: {total}")
            print(f"   成功: {self.success_count} ({success_rate:.1f}%)")
            print(f"   失败: {self.failed_count} ({100-success_rate:.1f}%)")

def main():
    """主函数"""
    csv_path = r"D:\BaiduNetdiskDownload\code\1022_90%\insurance_qa_pairs_20251022_233322.csv"
    
    processor = BatchQAProcessor(csv_path)
    
    if not processor.load_csv():
        return
    
    print("\n选择处理模式:")
    print("1. Demo模式 (处理前3条)")
    print("2. 小批量模式 (处理前20条)")
    print("3. 全量模式 (处理所有数据)")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        processor.process_demo(3)
    elif choice == "2":
        processor.process_demo(20)
    elif choice == "3":
        confirm = input("确认处理全量数据？这将需要很长时间 (y/n): ").strip().lower()
        if confirm == 'y':
            processor.process_all()
        else:
            print("已取消全量处理")
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
