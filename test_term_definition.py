from es_utils import ESUtils

def test_term_definition():
    # 初始化ESUtils实例
    es_utils = ESUtils(index='insurance_term')
    
    # 测试用例1: 测试精确匹配
    test_string1 = "第三者"
    result1 = es_utils.get_term_definition(test_string1)
    print(f"测试 '第三者':")
    for item in result1:
        print(f"定义: {item}")
        
        print("---")
    
    # 测试用例2: 测试模糊匹配
    test_string2 = "人身"
    result2 = es_utils.get_term_definition(test_string2)
    print(f"测试 '人身':")
    for item in result2:
        print(f"定义: {item}")
        
    
    # 测试用例3: 测试不存在的关键词
    test_string3 = "不存在的关键词"
    result3 = es_utils.get_term_definition(test_string3)
    print(f"测试 '不存在的关键词':")
    print(f"结果数量: {len(result3)}")

if __name__ == "__main__":
    test_term_definition()