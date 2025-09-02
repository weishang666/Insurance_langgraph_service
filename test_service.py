import requests
import json
import time
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 服务URL
BASE_URL = "http://localhost:8000"
# 测试接口路径
TEST_ENDPOINT = f"{BASE_URL}/insurance/question-inquiry"

def check_service_availability(max_retries=10, delay=1):
    """
    检查服务是否可用
    
    参数:
        max_retries: 最大重试次数
        delay: 每次重试间隔(秒)
    
    返回:
        bool: 服务是否可用
    """
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=2)
            if response.status_code == 200:
                return True
        except Exception as e:
            if i == 0:
                logger.info(f"服务尚未启动，等待中... (错误: {str(e)})")
            elif i % 3 == 0:
                logger.info(f"服务仍未就绪，继续等待... (已尝试{i+1}/{max_retries}次)")
            time.sleep(delay)
    logger.error(f"服务在{max_retries}次尝试后仍未启动")
    return False

# 测试函数 - 非流式响应
def test_non_streaming():
    logger.info("=== 测试非流式响应 ===")
    payload = {
        "user_id": "test_user_001",
        "user_question": "什么是意外险？",
        "stream": False
    }
    
    try:
        response = requests.post(TEST_ENDPOINT, json=payload, timeout=30)
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"业务状态码: {result.get('code')}")
                logger.info(f"消息: {result.get('message')}")
                logger.info(f"回答: {result.get('data')}")
                logger.info(f"产品列表: {result.get('product_list')}")
                
                # 检查产品列表是否正确返回
                product_list = result.get('product_list')
                if product_list is None:
                    logger.warning("产品列表为None")
                elif len(product_list) == 0:
                    logger.warning("产品列表为空")
                else:
                    logger.info(f"产品数量: {len(product_list)}")
            except json.JSONDecodeError as e:
                logger.error(f"解析响应JSON失败: {str(e)}")
        else:
            logger.error(f"请求失败，状态码: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
    except Exception as e:
        logger.error(f"测试非流式响应时出错: {str(e)}")
        logger.error(traceback.format_exc())

# 测试函数 - 流式响应
def test_streaming():
    logger.info("\n=== 测试流式响应 ===")
    payload = {
        "user_id": "test_user_002",
        "user_question": "什么是健康险？",
        "stream": True
    }
    
    try:
        with requests.post(TEST_ENDPOINT, json=payload, stream=True, timeout=60) as response:
            logger.info(f"状态码: {response.status_code}")
            logger.info(f"响应头: {response.headers}")
            
            if response.status_code == 200:
                logger.info("开始接收流式响应...")
                full_answer = []
                product_list = None
                
                for line in response.iter_lines():
                    if line:
                        # 解码并处理SSE格式数据
                        line = line.decode('utf-8')
                        logger.info(f"接收到原始行: {line}")
                        
                        if line.startswith('data: '):
                            data = line[6:]  # 移除 'data: ' 前缀
                            if data == '[DONE]':
                                logger.info("流式响应结束")
                                break
                            try:
                                json_data = json.loads(data)
                                full_answer.append(json_data.get('data', ''))
                                
                                if product_list is None:
                                    product_list = json_data.get('product_list')
                                
                                logger.info(f"\n业务状态码: {json_data.get('code')}")
                                logger.info(f"消息: {json_data.get('message')}")
                                logger.info(f"回答: {json_data.get('data')}")
                                logger.info(f"产品列表: {json_data.get('product_list')}")
                                
                                # 检查产品列表是否正确返回
                                current_product_list = json_data.get('product_list')
                                if current_product_list is None:
                                    logger.warning("产品列表为None")
                                elif len(current_product_list) == 0:
                                    logger.warning("产品列表为空")
                                else:
                                    logger.info(f"产品数量: {len(current_product_list)}")
                            except json.JSONDecodeError as e:
                                logger.error(f"无法解析JSON数据: {str(e)}")
                                logger.error(f"原始数据: {data}")
                
                logger.info(f"\n完整回答: {' '.join(full_answer)}")
                logger.info(f"最终产品列表: {product_list}")
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
    except Exception as e:
        logger.error(f"测试流式响应时出错: {str(e)}")
        logger.error(traceback.format_exc())

# 测试函数 - 产品查询
def test_product_query():
    logger.info("\n=== 测试产品查询 ===")
    payload = {
        "user_id": "test_user_003",
        "user_question": "平安守护尊享成人意外险保什么？",
        "stream": False
    }
    
    try:
        response = requests.post(TEST_ENDPOINT, json=payload, timeout=30)
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"业务状态码: {result.get('code')}")
                logger.info(f"消息: {result.get('message')}")
                logger.info(f"回答: {result.get('data')}")
                logger.info(f"产品列表: {result.get('product_list')}")
                
                # 检查产品列表是否正确返回
                product_list = result.get('product_list')
                if product_list is None:
                    logger.warning("产品列表为None")
                elif len(product_list) == 0:
                    logger.warning("产品列表为空")
                else:
                    logger.info(f"产品数量: {len(product_list)}")
                    # 打印产品详情
                    for i, product in enumerate(product_list):
                        logger.info(f"产品 {i+1}: {product.get('name', '未知产品')}")
            except json.JSONDecodeError as e:
                logger.error(f"解析响应JSON失败: {str(e)}")
        else:
            logger.error(f"请求失败，状态码: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
    except Exception as e:
        logger.error(f"测试产品查询时出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("保险业务智能问答服务测试")
    logger.info(f"测试服务地址: {BASE_URL}")
    
    # 检查服务是否可用

    
    logger.info("服务已就绪，开始测试")
    # 执行测试
    #test_non_streaming()
    test_streaming()
    test_product_query()
    
    logger.info("\n测试完成")