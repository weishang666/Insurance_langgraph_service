import sys
import os
# 将项目根目录添加到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from es_utils import ESUtils


def test_get_all_product_names():
    """测试获取所有产品名称的功能"""
    print("开始测试获取所有产品名称...")
    try:
        # 初始化ESUtils
        index_name = "insurance_fixed_chunk"
        print(f"使用索引: {index_name}")
        es_utils = ESUtils(index=index_name)
        
        # 调用新方法获取所有产品名称
        product_names = es_utils.get_all_product_names()
        
        # 打印结果
        if product_names:
            print(f"成功获取产品名称列表，共 {len(product_names)} 个产品:")
            for i, product_name in enumerate(product_names, 1):
                print(f"{i}. {product_name}")
        else:
            print("未获取到任何产品名称")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    test_get_all_product_names()