import pandas as pd
import requests
import time
from tqdm import tqdm

def process_insurance_questions():
 # 配置参数---http://10.176.27.166:8000/      http://localhost:8000
    BASE_URL = "http://10.176.27.166:8001"
    TEST_ENDPOINT = f"{BASE_URL}/insurance/question-inquiry"
    input_file = r"D:\pythonSorft\china_mobile\test_file\re_test\re_question2.xlsx"
    output_file = r"D:\pythonSorft\china_mobile\test_file\re_test\re_testout2-test.xlsx"
 # 读取Excel文件
    try:  #742      160    245
        df = pd.read_excel(input_file,nrows=2)
        print(f"成功读取Excel文件，共{len(df)}条记录")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
    # 检查必要的列是否存在
    required_columns = ['序号', '保险产品', '问题', '标注', '参考原文']
    for col in required_columns:
        if col not in df.columns:
            print(f"Excel文件缺少必要的列: {col}")
            return
    
    #添加模型答案列
    df['模型答案'] = ""
    #使用tqdm创建进度条
    for index, row in tqdm(df.iterrows(), total=len(df), desc="处理进度"):
        try:
            # 拼接保险产品和问题
            combined_question = f"保险产品：{row['保险产品']} ，问题：{row['问题']}"
             # 构建请求 payload
            payload = {
                "user_id": f"test_user_{index + 100}", # 使用不同的用户ID
                "user_question": combined_question,
                "stream": False
                }
            # 发送请求
            response = requests.post(
                TEST_ENDPOINT,
                json=payload,
                timeout=100
                )

            # 检查响应状态
            max_retries = 3  # 设置最大重试次数
            retry_count = 0
            answer = ''

            while retry_count < max_retries and (not answer or answer.strip() == ''):
                if response.status_code == 200:
                    result = response.json()
                    # 提取模型答案
                    answer = result.get('data', '无返回结果')
                    #print("***answer****", answer)

                    # 检查答案是否为空
                    if not answer or answer.strip() == '':
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f'答案为空，准备第{retry_count}次重试...')
                            time.sleep(2)  # 重试前等待3秒
                            # 重新发送请求
                            response = requests.post(
                                TEST_ENDPOINT,
                                json=payload,
                                timeout=100
                            )
                        else:
                            print('已达到最大重试次数，使用空答案')
                            df.at[index, '模型答案'] = '无返回结果(重试多次后仍为空)'
                    else:
                        df.at[index, '模型答案'] = answer
                        print(f'已经产出第{index}个，答案是{answer}')
                else:
                    df.at[index, '模型答案'] = f"请求失败，状态码: {response.status_code}"
                    break  # 请求失败不重试

            #避免请求过于频繁
            time.sleep(2)

        except Exception as e:
            df.at[index, '模型答案'] = f"处理出错: {str(e)}"
            # 打印错误详情（不中断进度条）
            tqdm.write(f"第{index + 1}条记录处理出错: {str(e)}")
    #保存结果到新的Excel文件
    try:
        df.to_excel(output_file, index=False)
    except Exception as e:
        print(f"查询异常: {e}")

if __name__ == "__main__":
    process_insurance_questions()