import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from es_utils import ESUtils


def test_search_fuzzy_product_names():
    """测试产品名称模糊匹配功能"""
    try:
        # 初始化ES工具
        index_name = "insurance_fixed_chunk"
        es_utils = ESUtils(index=index_name)
        print(f"成功连接到Elasticsearch，使用索引: {es_utils.index}")
        
        # 测试模糊匹配
        test_keywords = ["平安", "医保", "重疾", "寿险", "意外",'移小保',"移小保安欣保2.0长期医疗"]
        
        for keyword in test_keywords:
            print(f"\n测试关键词: '{keyword}'")
            product_names = es_utils.search_fuzzy_product_names(keyword, top_k=5)
            if product_names:
                for i, name in enumerate(product_names, 1):
                    print(f"  {i}. {name}")
            else:
                print("未找到模糊匹配的产品名称")
        
        # 测试容错错别字
        print(f"\n测试错别字容错: '平按' 和 '平案'")
        for typo in ["平按", "平案"]:
            print(f"\n测试错别字: '{typo}'")
            product_names = es_utils.search_fuzzy_product_names(typo, top_k=5)
            
            if product_names:
                print(f"找到 {len(product_names)} 个模糊匹配的产品名称:")
                for i, name in enumerate(product_names, 1):
                    print(f"  {i}. {name}")
            else:
                print("未找到模糊匹配的产品名称")
        
    except Exception as e:
        print(f"测试发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_search_fuzzy_product_names()