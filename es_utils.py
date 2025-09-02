import requests
from requests.auth import HTTPBasicAuth
import json
import random
from config import ES_HOST, ES_PORT, ES_USERNAME, ES_PASSWORD, ES_INDEX
import Levenshtein 
class ESUtils:
    def __init__(self, index=None):
        # 初始化requests连接参数
        self.base_url = f"http://{ES_HOST}:{ES_PORT}"
        self.auth = HTTPBasicAuth(ES_USERNAME, ES_PASSWORD)
        self.headers = {"Content-Type": "application/json"}
        self.index = index or ES_INDEX

    def get_document(self, doc_id):
        """获取文档

        参数:
            doc_id: 文档ID

        返回:
            成功返回文档内容 (字典)，失败返回 None
        """
        try:
            url = f"{self.base_url}/{self.index}/_doc/{doc_id}"
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()["_source"]
            else:
                print(f"获取失败，状态码: {response.status_code}")
                print(response.text)
                return None

        except Exception as e:
            print(f"查询异常: {e}")
            return None

    def search(self, query, size=5):
        """搜索相关文档"""
        try:
            url = f"{self.base_url}/{self.index}/_search"
            query_body = {
                "query": {
                    "match": {
                        "content": query
                    }
                },
                "size": size
            }
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )
            if response.status_code == 200:
                result = response.json()
                return [hit["_source"] for hit in result["hits"]["hits"]]
            else:
                print(f"搜索失败，状态码: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"ES搜索错误: {e}")
            return []

    def index_document(self, document_id=None, content=None, metadata=None, document=None):
        """索引文档

        参数:
            document_id: 文档ID (可选，自动生成时为None)
            content: 文档内容 (可选，与document参数二选一)
            metadata: 文档元数据 (可选)
            document: 完整文档内容 (可选，与content参数二选一)

        返回:
            成功返回 (True, 文档ID)，失败返回 (False, None)
        """
        try:
            # 构建URL
            url = f"{self.base_url}/{self.index}/_doc"
            if document_id:
                url += f"/{document_id}"

            # 准备文档内容
            if document:
                doc = document
            else:
                doc = {
                    "content": content,
                    "metadata": metadata or {}
                }

            # 发送请求
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(doc)
            )

            # 处理响应
            if response.status_code in (200, 201):
                result = response.json()
                doc_id = result['_id']
                print(f"文档 {doc_id} 已成功索引到 {self.index}")
                return True, doc_id
            else:
                print(f"索引失败，状态码: {response.status_code}")
                print(response.text)
                return False, None

        except Exception as e:
            print(f"ES索引错误: {e}")
            return False, None

    def create_index(self, mapping=None):
        """创建索引"""
        try:
            # 检查索引是否存在
            url = f"{self.base_url}/{self.index}"
            response = requests.head(url, auth=self.auth)
            if response.status_code == 200:
                return True

            # 创建索引
            create_url = f"{self.base_url}/{self.index}"
            mappings = mapping or {
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text"
                        },
                        "metadata": {
                            "type": "object"
                        },
                        "product_name": {
                            "type": "keyword"
                        },
                        "insurance_name": {
                            "type": "text"
                        },
                        "chunk_type": {
                            "type": "keyword"
                        },
                        "chunk_id": {
                            "type": "integer"
                        }
                    }
                }
            }
            response = requests.put(
                create_url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(mappings)
            )
            if response.status_code == 200:
                return True
            else:
                print(f"创建索引失败，状态码: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"ES创建索引错误: {e}")
            return False

    def search_by_product_name(self, product_name, size=10, exact_match=True):
        """根据产品名称搜索文档

        参数:
            product_name: 产品名称
            size: 返回结果数量
            exact_match: 是否精确匹配 (默认为 True)

        返回:
            成功返回搜索结果列表，失败返回空列表
        """
        try:
            url = f"{self.base_url}/{self.index}/_search"
            if exact_match:
                # 使用 term 查询进行精确匹配
                query_body = {
                    "query": {
                        "term": {
                            "product_name.keyword": product_name
                        }
                    },
                    "size": size
                }
            else:
                # 使用 match 查询进行模糊匹配
                query_body = {
                    "query": {
                        "match": {
                            "product_name": product_name
                        }
                    },
                    "size": size
                }
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )
            if response.status_code == 200:
                result = response.json()
                return [hit["_source"] for hit in result["hits"]["hits"]]
            else:
                print(f"按产品名称搜索失败，状态码: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"ES按产品名称搜索错误: {e}")
            return []

    def search_by_vector_and_product(self, product_name, vector, size=5):
        """根据产品名称(模糊匹配)和向量搜索最相似的文档

        参数:
            product_name: 产品名称
            vector: 向量数组
            size: 返回结果数量 (默认为 5)

        返回:
            成功返回相似度最高的文档chunk_text列表，失败返回空列表
        """
        try:
            url = f"{self.base_url}/{self.index}/_search"
            # 构建查询体，结合产品名称模糊匹配和向量相似度排序
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "product_name": product_name
                                }
                            },
                            {
                                "script_score": {
                                    "query": {
                                        "match_all": {}
                                    },
                                    "script": {
                                        "source": "cosineSimilarity(params.query_vector, 'chunk_vector') + 1.0",
                                        "params": {
                                            "query_vector": vector
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": size
            }
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )
            if response.status_code == 200:
                result = response.json()
                # 提取chunk_text字段
                return [hit["_source"].get("chunk_text", "") for hit in result["hits"]["hits"]]
            else:
                print(f"按向量和产品名称搜索失败，状态码: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"ES按向量和产品名称搜索错误: {e}")
            return []

    def search_by_product_and_chunk_type(self, product_name, chunk_type, size=5, deduplicate=True):
        """根据产品名称和chunk_type搜索文档

        参数:
            product_name: 产品名称
            chunk_type: 条款类型
            size: 返回结果数量 (默认为 5)
            deduplicate: 是否对结果去重 (默认为 True)

        返回:
            成功返回搜索结果列表(去重后)，失败返回空列表
        """
        try:
            url = f"{self.base_url}/{self.index}/_search"
            # 构建查询体，结合产品名称和chunk_type精确匹配
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "product_name": product_name
                                }
                            },
                            {
                                "term": {
                                    "chunk_type": chunk_type
                                }
                            }
                        ]
                    }
                },
                "sort": [
                    {"_score": {"order": "desc"}}
                ],
                "size": size * 2  # 获取更多结果用于去重
            }
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )
            if response.status_code == 200:
                result = response.json()
                hits = result["hits"]["hits"]
                
                # 提取结果并可选去重
                if deduplicate:
                    # 优化的去重逻辑：基于内容关键词和长度
                    unique_hits = []
                    seen_keywords = set()
                    min_length_diff = 0.2  # 长度差异阈值
                    
                    def get_keywords(content):
                        """提取内容关键词"""
                        # 转为小写并去除特殊字符
                        content = content.lower()
                        for char in ',.!?;:\'"()[]{}\/<>*|=+-_~`@#$%^&':
                            content = content.replace(char, ' ')
                        # 提取关键词（取前10个词）
                        words = [word for word in content.split() if len(word) > 1]
                        return set(words[:10])  # 返回前10个词作为关键词
                    
                    for hit in hits:
                        current_content = hit["_source"].get("chunk_text", "")
                        current_keywords = get_keywords(current_content)
                        current_length = len(current_content)
                        
                        # 检查是否与已添加的内容相似
                        is_similar = False
                        for i, existing_hit in enumerate(unique_hits):
                            existing_content = existing_hit["_source"].get("chunk_text", "")
                            existing_keywords = seen_keywords
                            existing_length = len(existing_content)
                            
                            # 检查关键词相似度
                            keyword_intersection = current_keywords & existing_keywords
                            keyword_similarity = len(keyword_intersection) / len(current_keywords | existing_keywords) if (current_keywords | existing_keywords) else 0
                            
                            # 检查长度差异
                            length_diff = abs(current_length - existing_length) / max(current_length, existing_length, 1)
                            
                            # 如果关键词相似度高且长度差异小，则认为相似
                            if keyword_similarity > 0.6 and length_diff < min_length_diff:
                                is_similar = True
                                break
                        
                        if not is_similar:
                            unique_hits.append(hit)
                            seen_keywords.update(current_keywords)
                            # 如果已经达到所需数量，退出循环
                            if len(unique_hits) >= size:
                                break
                    
                    # 确保按分数排序
                    unique_hits.sort(key=lambda x: x["_score"], reverse=True)
                else:
                    unique_hits = hits[:size]
                
                return [hit["_source"] for hit in unique_hits]
            else:
                print(f"按产品名称和chunk_type搜索失败，状态码: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"ES按产品名称和chunk_type搜索错误: {e}")
            return []

            
    def search_by_product(self, product_name, size=15, deduplicate=True):
        """根据产品名称搜索文档

        参数:
            product_name: 产品名称
            size: 返回结果数量 (默认为 5)
            deduplicate: 是否对结果去重 (默认为 True)

        返回:
            成功返回搜索结果列表(去重后)，失败返回空列表
        """
        try:
            url = f"{self.base_url}/{self.index}/_search"
            # 构建查询体，仅匹配产品名称
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "product_name": product_name
                                }
                            }
                        ]
                    }
                },
                "sort": [
                    {"_score": {"order": "desc"}}
                ],
                "size": size * 2  # 获取更多结果用于去重
            }
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )
            if response.status_code == 200:
                result = response.json()
                hits = result["hits"]["hits"]
                
                # 提取结果并可选去重
                if deduplicate:
                    # 优化的去重逻辑：基于内容关键词和长度
                    unique_hits = []
                    seen_keywords = set()
                    min_length_diff = 0.2  # 长度差异阈值
                    
                    def get_keywords(content):
                        """提取内容关键词"""
                        # 转为小写并去除特殊字符
                        content = content.lower()
                        for char in ',.!?;:\'"()[]{}\/<>*|=+-_~`@#$%^&':
                            content = content.replace(char, ' ')
                        # 提取关键词（取前10个词）
                        words = [word for word in content.split() if len(word) > 1]
                        return set(words[:10])  # 返回前10个词作为关键词
                    
                    for hit in hits:
                        current_content = hit["_source"].get("chunk_text", "")
                        current_keywords = get_keywords(current_content)
                        current_length = len(current_content)
                        
                        # 检查是否与已添加的内容相似
                        is_similar = False
                        for existing_hit in unique_hits:
                            existing_content = existing_hit["_source"].get("chunk_text", "")
                            existing_keywords = get_keywords(existing_content)
                            existing_length = len(existing_content)
                            
                            # 计算关键词交集比例
                            common_keywords = current_keywords.intersection(existing_keywords)
                            max_keywords = max(len(current_keywords), len(existing_keywords), 1)
                            keyword_similarity = len(common_keywords) / max_keywords
                            
                            # 计算长度差异比例
                            length_diff = abs(current_length - existing_length) / max(current_length, existing_length, 1)
                            
                            # 如果关键词相似度高且长度差异小，则认为相似
                            if keyword_similarity > 0.5 and length_diff < min_length_diff:
                                is_similar = True
                                break
                        
                        if not is_similar:
                            unique_hits.append(hit)
                            # 添加关键词到已见集合
                            seen_keywords.update(current_keywords)
                            
                            # 如果已达到所需结果数量，则停止
                            if len(unique_hits) >= size:
                                break
                    
                    # 提取结果文本
                    results = [hit["_source"]["chunk_text"] for hit in unique_hits[:size]]
                else:
                    # 不去重，直接提取结果
                    results = [hit["_source"]["chunk_text"] for hit in hits[:size]]
                
                return results
            else:
                print(f"搜索失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            print(f"搜索发生异常: {e}")
            return []

    def get_all_product_names(self):
        """检索所有的产品名称

        返回:
            成功返回产品名称列表，失败返回空列表
        """
        try:
            url = f"{self.base_url}/{self.index}/_search"
            print(f"正在检索索引 {self.index} 中的所有产品名称...")
            
            # 构建查询体，使用聚合功能获取所有唯一的product_name
            query_body = {
                "size": 0,  # 不返回具体文档
                "query": {
                    "match_all": {}
                },
                "aggs": {
                    "unique_products": {
                        "terms": {
                            "field": "product_name",  # 使用keyword字段确保精确聚合
                            "size": 10000,  # 设置足够大的值以获取所有产品
                            "order": {
                                "_count": "desc"
                            }
                        }
                    }
                }
            }
            
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 提取聚合结果中的产品名称
                if "aggregations" in result and "unique_products" in result["aggregations"]:
                    product_names = [bucket["key"] for bucket in result["aggregations"]["unique_products"]["buckets"]]
                    print(f"成功获取 {len(product_names)} 个产品名称")
                    return product_names
                else:
                    print("聚合结果格式不正确，未找到产品名称")
                    return []
            else:
                print(f"检索所有产品名称失败，状态码: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"ES检索所有产品名称错误: {e}")
            return []
    
    def get_term_definition(self, input_string):
        """根据输入字符串匹配term_keyword，返回对应的term_definition

        参数:
            input_string: 输入的字符串

        返回:
            成功返回匹配的term_definition字典列表，失败返回空列表
        """
        try:
            # 设置索引为insurance_term
            original_index = self.index
            self.index = "insurance_term"

            # 构建查询体，匹配输入字符串中的term_keyword
            url = f"{self.base_url}/{self.index}/_search"
            query_body = {
                "query": {
                    "match": {
                        "term_keyword": input_string
                    }
                },
                "size": 10  # 获取最多10个匹配结果
            }

            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(query_body)
            )

            # 恢复原始索引
            self.index = original_index

            if response.status_code == 200:
                result = response.json()
                hits = result["hits"]["hits"]

                # 提取匹配结果
                term_definitions = []
                for hit in hits:
                    source = hit["_source"]
                    term_definitions.append(
                        source["term_definition"]
                    )

                return term_definitions
            else:
                print(f"搜索条款失败，状态码: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"获取条款定义错误: {e}")
            # 确保恢复原始索引
            self.index = original_index
            return []


    def search_fuzzy_product_names(self, mention, top_k=10):
        try:
            # 第一步：从ES获取去重后的所有产品名称
            url = f"{self.base_url}/{self.index}/_search"
            dedup_query = {
                "size": 0,
                "aggs": {
                    "unique_products": {
                        "terms": {
                            "field": "product_name",
                            "size": 10000  # 调整为实际可能的最大产品数量
                        }
                    }
                }
            }
            
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(dedup_query)
            )
            
            if response.status_code != 200:
                print(f"获取去重产品失败，状态码: {response.status_code}")
                return []
            
            # 提取去重后的产品名称列表
            result = response.json()
            unique_products = [
                bucket["key"] 
                for bucket in result["aggregations"]["unique_products"]["buckets"]
            ]
            
            if not unique_products:
                return []
            
            # 第二步：先检查是否有完全匹配的产品
            for i in [mention,''.join(mention.split('保险')[:-1]),''.join(mention.split('险')[:-1])]:
                exact_match = next((p for p in unique_products if p == i), None)
                if exact_match:
                    # 存在完全匹配，直接返回包含该结果的列表
                    return [exact_match]
                
            # 第三步：无完全匹配时，计算相似度并返回top_k
            product_similarities = []
            for product in unique_products:
                distance = Levenshtein.distance(mention, product)
                max_len = max(len(mention), len(product))
                similarity = 1 - (distance / max_len) if max_len > 0 else 0
                product_similarities.append((product, similarity))
            
            # 按相似度降序排序，取top_k
            product_similarities.sort(key=lambda x: x[1], reverse=True)
            top_matches = [p[0] for p in product_similarities[:top_k]]
            
            return top_matches
            
        except Exception as e:
            print(f"模糊匹配错误: {e}")
            return []



if __name__ == "__main__":
    # 测试代码
    try:
        # 初始化ES工具，可以指定索引名称
        index_name = "insurance_fixed_chunk"  # 可以替换为配置中的ES_INDEX
        es_utils = ESUtils(index=index_name)
        print(f"成功连接到Elasticsearch: {ES_HOST}:{ES_PORT}")
        print(f"使用索引: {es_utils.index}")
        
        # 确保索引存在
        if es_utils.create_index():
            print("索引已准备就绪")
        else:
            print("创建索引失败")
            exit(1)
        
        
        # 测试按产品名称精确搜索
        product_name = "中国人保金医保3号百万医疗险"
        print(f"\n精确搜索产品: {product_name}")
        exact_results = es_utils.search_by_product_name(product_name, exact_match=True)
        
        if exact_results:
            print(f"找到 {len(exact_results)} 条精确匹配结果:")
            for i, result in enumerate(exact_results[:5]):
                print(f"\n结果 {i+1}:")
                print(f"  文档ID: {result.get('chunk_id')}")
                print(f"  产品名称: {result.get('product_name')}")
                print(f"  保险名称: {result.get('insurance_name')}")
                print(f"  条款类型: {result.get('chunk_type')}")
                print(f"  条款内容: {result.get('chunk_text', '')[:100]}...")
        else:
            print("没有找到精确匹配结果")

        # 测试按产品名称模糊搜索
        print(f"\n模糊搜索产品: {product_name}")
        fuzzy_results = es_utils.search_by_product_name(product_name, exact_match=False)
        
        if fuzzy_results:
            print(f"找到 {len(fuzzy_results)} 条模糊匹配结果:")
            for i, result in enumerate(fuzzy_results[:5]):
                print(f"\n结果 {i+1}:")
                print(f"  文档ID: {result.get('chunk_id')}")
                print(f"  产品名称: {result.get('product_name')}")
                print(f"  保险名称: {result.get('insurance_name')}")
                print(f"  条款类型: {result.get('chunk_type')}")
                print(f"  条款内容: {result.get('chunk_text', '')[:100]}...")
        else:
            print("没有找到模糊匹配结果")
            
        # 测试按产品名称和向量搜索
        print(f"\n按产品名称和向量搜索: {product_name}")
        # 示例向量，实际应用中应该是通过模型生成的向量
        # 生成1024维随机向量，值范围在-0.1到0.1之间
        user_query = "移小保安欣保2.0长期医疗的条款"
        from llm_client import LLMClient
        llm_client = LLMClient()
        sample_vector = llm_client.get_text_embedding(user_query) 
        vector_results = es_utils.search_by_vector_and_product(product_name, sample_vector, size=5)
        
        if vector_results:
            print(f"找到 {len(vector_results)} 条向量匹配结果:")
            for i, result in enumerate(vector_results):
                print(f"\n结果 {i+1}:")
                print(f"  文本内容: {result[:100]}...")
        else:
            print("没有找到向量匹配结果")
    
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()