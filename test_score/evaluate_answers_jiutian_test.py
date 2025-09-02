import pandas as pd
import time
from tqdm import tqdm
from llm_client import LLMClient

# 评分标准提示词
EVALUATION_PROMPT = """
你需要验证实际结果是否符合预期结果。预期结果可是真实的结果，也可以是预期的规则。
如果实际结果与预期结果相似度达到90%，就可以认为实际结果符合预期。
另外，符合以下要求也算符合预期：
1. 相似度判断未达到90%，但关键数据一致.
2. 相似度判断未达到90%，无关键数据判断时，符合保险条款，无误导内容.
3. 相似度判断未达到90%，属于未正面回答用户问题的，有引导用户进一步补充问题，符合保险条款，无误导内容.
4. 若涉及查看保单问题，实际结果是"点击下方按钮，即可为您查看保单列表及相关信息"，可以判断为符合预期.
5、若涉及退保问题,实际结果是“您好!我们为您安排了专业客户顾问,点击下方按钮添加,即可享受1对1贴心服务!”,可以判断为符合预期.

请根据以上标准，对以下问题和答案进行评估：
问题: {question}
答案: {answer}

请给出评分(0-100分，100分为完全符合，0分为完全不符合)，并简要说明评分理由。
评分结果格式: 评分: [分数]，理由: [理由]
"""

def evaluate_answers():
    # 配置参数
    input_file = r"D:\pythonSorft\china_mobile\test_file\score01.xlsx"
    output_file = r"D:\pythonSorft\china_mobile\test_file\evaluation_results01.xlsx"

    # 读取Excel文件
    try:
        df = pd.read_excel(input_file)
        print(f"成功读取Excel文件，共{len(df)}条记录")
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return

    # 检查必要的列是否存在
    required_columns = ['问题', '模型答案']  # 假设'标注'列是参考答案
    for col in required_columns:
        if col not in df.columns:
            print(f"Excel文件缺少必要的列: {col}")
            return

    # 添加评分和理由列
    df['评分'] = ""
    df['评分理由'] = ""

    # 初始化DeepSeek大模型客户端
    try:
        llm_client = LLMClient(model_name="deepseek14")
        print("DeepSeek大模型客户端初始化成功")
    except Exception as e:
        print(f"DeepSeek大模型客户端初始化失败: {str(e)}")
        return

    # 使用tqdm创建进度条
    for index, row in tqdm(df.iterrows(), total=len(df), desc="评估进度"):
        try:
            question = row['问题']
            answer = row['模型答案']

            # 构建评估提示
            prompt = EVALUATION_PROMPT.format(question=question, answer=answer)

            # 调用大模型进行评估
            result = llm_client.generate(
                prompt=prompt,
                system_prompt="你是一名保险行业的评估专家，负责评估保险问题的回答是否符合要求。",
                max_tokens=500,
                temperature=0.3
            )

            # 解析评分结果
            if result:
                # 提取评分和理由
                score = ""
                reason = ""
                if "评分: " in result:
                    score_part = result.split("评分: ")[1].split("，理由: ")[0]
                    score = score_part.strip()
                if "理由: " in result:
                    reason_part = result.split("理由: ")[1]
                    reason = reason_part.strip()

                df.at[index, '评分'] = score
                df.at[index, '评分理由'] = reason
                print(f'已完成第{index+1}个评估，评分: {score}')
            else:
                df.at[index, '评分'] = "评估失败"
                df.at[index, '评分理由'] = "模型未返回结果"

            # 避免请求过于频繁
            time.sleep(1)

        except Exception as e:
            df.at[index, '评分'] = "评估出错"
            df.at[index, '评分理由'] = str(e)
            # 打印错误详情
            tqdm.write(f"第{index + 1}条记录评估出错: {str(e)}")

    # 所有评估完成后，一次性保存结果到Excel文件
    try:
        df.to_excel(output_file, index=False)
        print(f"所有评估结果已保存到{output_file}")
    except Exception as e:
        print(f"保存Excel文件异常: {e}")

if __name__ == "__main__":
    evaluate_answers()