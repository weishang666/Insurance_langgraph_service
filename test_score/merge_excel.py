import pandas as pd

# 1. 读取数据
df1 = pd.read_excel( r"D:\pythonSorft\china_mobile\test_file\re_test\deepseek_evaluation_results_all.xlsx")
df2 = pd.read_excel( r"D:\pythonSorft\china_mobile\test_file\re_test\re_testout_all.xlsx")

print("更新前 df1 的行数:", len(df1))

# 2. 设置索引为 'ID'
df1_upd = df1.set_index('序号')
df2_upd = df2.set_index('序号')

# 3. 使用 update 方法 (df1_upd 会被 df2_upd 更新)
# 注意：update 是 in-place 操作，会直接修改 df1_upd
df1_upd.update(df2_upd)

# 4. 重置索引
df1_updated = df1_upd.reset_index()

# 6. 计算评分的平均数
# 假设评分列的名称为'评分'，如果实际列名不同，请修改这里
if '评分' in df1_updated.columns:
    # 确保评分列包含数值型数据
    df1_updated['评分'] = pd.to_numeric(df1_updated['评分'], errors='coerce')
    average_score = df1_updated['评分'].mean()
    if pd.notna(average_score):
        print(f"合并后表格中评分的平均数: {average_score:.2f}")
    else:
        print("评分列中没有有效的数值数据，无法计算平均值")
else:
    print("未找到'评分'列，请检查列名是否正确")


# 5. 保存结果
df1_updated.to_excel(r"D:\pythonSorft\china_mobile\test_file\re_test\deepseek_evaluation_results_all_new.xlsx", index=False)

print("更新后 df1 的行数:", len(df1_updated))


print("更新完成！")