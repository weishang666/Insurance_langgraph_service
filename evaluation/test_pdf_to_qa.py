import os
from pdf_to_qa import PDFToQAGenerator


def find_first_pdf_in_directory(directory):
    """递归遍历目录，找到第一个PDF文件"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                return os.path.join(root, file)
    return None



def test_product_folder(product_folder_path=None):
    """测试处理产品文件夹下的PDF文件
    如果未提供product_folder_path，则处理所有产品文件夹
    如果提供了product_folder_path，则仅处理指定的产品文件夹
    """
    # 初始化问答生成器
    qa_generator = PDFToQAGenerator()

    # 设置根目录和输出目录
    pdf_root_folder = "D:/data/内部"
    output_root_dir = "d:/BaiduNetdiskDownload/code/langgraph/new/insurance_agent_backendv2/test/output"

    if not os.path.exists(pdf_root_folder):
        print(f"错误: 目录 {pdf_root_folder} 不存在")
        return False

    # 确定要处理的产品文件夹列表
    product_folders = []
    if product_folder_path is None:
        # 处理所有产品文件夹
        print("未提供产品文件夹路径，将处理所有产品文件夹")
        for item in os.listdir(pdf_root_folder):
            item_path = os.path.join(pdf_root_folder, item)
            if os.path.isdir(item_path):
                product_folders.append(item_path)
    else:
        # 仅处理指定的产品文件夹
        if not os.path.exists(product_folder_path):
            print(f"错误: 产品文件夹 {product_folder_path} 不存在")
            return False
        product_folders.append(product_folder_path)

    if not product_folders:
        print(f"错误: 未找到产品文件夹")
        return False

    total_success_count = 0
    print(f"找到 {len(product_folders)} 个产品文件夹，开始处理...")

    # 遍历所有要处理的产品文件夹
    for product_folder_path in product_folders:
        # 提取产品名称
        product_name = os.path.basename(product_folder_path)
        print(f"\n处理产品: {product_name}")

        # 创建输出目录（按产品名称组织）
        product_output_dir = os.path.join(output_root_dir, product_name)
        os.makedirs(product_output_dir, exist_ok=True)

        # 直接处理产品文件夹中的PDF文件
        success_count = 0
        for file_name in os.listdir(product_folder_path):
            file_path = os.path.join(product_folder_path, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith('.pdf'):
                if qa_generator.process_single_pdf(file_path, product_output_dir, product_name):
                    success_count += 1
        print(f"产品 {product_name} 成功处理了 {success_count} 个PDF文件")
        total_success_count += success_count

    print(f"\n所有产品处理完成，共成功处理 {total_success_count} 个PDF文件")
    print(f"测试产品文件夹结果: {'成功' if total_success_count > 0 else '失败'}")
    return total_success_count > 0



if __name__ == "__main__":
    # 运行测试 - 测试所有产品文件夹
    print("开始测试所有产品文件夹...")
    test_product_folder()

    # 可选：也可以测试单个产品文件夹
    # print("\n开始测试单个产品文件夹...")
    # test_product_folder()

    # 可选：也可以测试单个PDF文件
    # print("\n开始测试单个PDF文件...")
    # test_single_pdf()

    print("\n测试完成，请查看输出目录中的问答对文件。")