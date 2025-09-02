import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 应用配置
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Elasticsearch 配置
ES_HOST = os.getenv("ES_HOST", "10.176.27.142")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_USERNAME = os.getenv("ES_USERNAME", "tenant")
ES_PASSWORD = os.getenv("ES_PASSWORD", "Root@10086")
ES_INDEX = os.getenv("ES_INDEX", "insurance_clauses")

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# LLM 配置
#LLM_APP_CODE = os.getenv("LLM_APP_CODE", "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI1MmQ2YzRiMmExMjQ0YzFkODA5OGNhMzRkNmFkMzViMCIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDkwNjQyMzM0Nn0.EfZvwlWvDw1DgfGAbk51zOlFzOk4wN6CiXhsfvegv9bu1EoeA6WDSmw6vziLFl37ooUjuLxThSsS58cchFvutGz5aBdAN9Lyg91JkuPpOGE7KrYwC6Ha0Bp8YJu1HpKbuvOVmECYvdgtKwVEG66bE30fN2Fiy0jhaC7RqSmDAEdAcrJUq6fxrjqlym-1jwb1ZgunXbaFuPyNPFAK_uGvh03id8oSJpDGZZbWEPKktAsKeJz8EZX8KfS9OdugDXPEeFFmGjs8_9nqiVIPV3JPaUaWITumgZzY_SVtDUxTDiBIxg5DajxNAEapJk43h-vwmIAWAy7b97LPHVVucCynrg")
LLM_APP_CODE = os.getenv("LLM_APP_CODE", "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJmOTQxOWExM2Q4MGE0NTQ0OGFlZTQ1OTE1MDE0N2JkZiIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDkwODEzNDcwOX0.JvMVMA18bMIV3umzOSGLquQkOH-419_ym2Ks5BjgJ4yEmpascwkEXHvSQ9rn3mW5hF7IttKu8Ftmzr8OZjqHBBq1QQRw4t65kFzz81B5tFvHNRghxd_uTjrE4AuOeNrdFx1nySePicaJ2wDJ6yoSUtWxpxjo9JCzlqFoR-Q1U_vBphGixq1Ut8vt-a5jSTPFwFleAWKsshJMFHFcmwKhtprm4gVB0b4Vyc5VU4uMyDRMxkzVrQF0gUZB20pDVyDFQZFMbOPXEzP9LHwzO_8T8o95YGQv_PUrUP24K4YXw5m4zbB7q2j7pGWMsqt-RMptpTxocPC0SAu4FLq0TcLW3w")
LLM_API_URL = os.getenv("LLM_API_URL", "https://jiutian.10086.cn/kunlun/ingress/api-safe/h3t-dfac2f/f402206d636147ba8fb057c25fbe6839/ai-9b16840714814c28bec4ac53a5d07fbf/service-75c01af105c947058f8c5634725f4d6b/v1/chat/completions")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://jiutian.10086.cn/kunlun/ingress/api/h3t-dfac2f/f402206d636147ba8fb057c25fbe6839/ai-fb42caa919074bcf9aa08e213c06d5f9/service-a36a9c6ffefa40c0b063b1e5562c0057/v1/embeddings")
EMBEDDING_APP_CODE = os.getenv("EMBEDDING_APP_CODE", "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJmOTQxOWExM2Q4MGE0NTQ0OGFlZTQ1OTE1MDE0N2JkZiIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDkwODEzNDcwOX0.JvMVMA18bMIV3umzOSGLquQkOH-419_ym2Ks5BjgJ4yEmpascwkEXHvSQ9rn3mW5hF7IttKu8Ftmzr8OZjqHBBq1QQRw4t65kFzz81B5tFvHNRghxd_uTjrE4AuOeNrdFx1nySePicaJ2wDJ6yoSUtWxpxjo9JCzlqFoR-Q1U_vBphGixq1Ut8vt-a5jSTPFwFleAWKsshJMFHFcmwKhtprm4gVB0b4Vyc5VU4uMyDRMxkzVrQF0gUZB20pDVyDFQZFMbOPXEzP9LHwzO_8T8o95YGQv_PUrUP24K4YXw5m4zbB7q2j7pGWMsqt-RMptpTxocPC0SAu4FLq0TcLW3w")

# 应用配置
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")