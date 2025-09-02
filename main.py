import os
import sys
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, AsyncGenerator
from graph_builder import GraphBuilder
from state import State
from langgraph.checkpoint.memory import InMemorySaver
from config import APP_HOST, APP_PORT
import asyncio

workspace_dir = os.path.dirname(os.path.abspath(__file__))
if workspace_dir not in sys.path:
    sys.path.append(workspace_dir)

app = FastAPI(title="保险业务-智能问答")

# 创建默认的内存检查点保存器
default_memory = InMemorySaver()

# 使用默认内存初始化工作流
workflow = GraphBuilder.build(memory=default_memory)

# 提供一个函数用于更新工作流的memory
def update_workflow_memory(new_memory):
    global workflow
    workflow = GraphBuilder.build(memory=new_memory)

# 会话管理 - 保存每个用户的状态
sessions = {}

class InsuranceServiceRequest(BaseModel):
    user_id: str = Field(..., description="用户ID，唯一标识用户，不能为空")
    user_question: str = Field(..., min_length=1, max_length=2000, description="用户的保险相关提问，长度限制1-2000字符")
    stream: bool = Field(True, description="响应方式控制：true=流式响应（逐步返回结果），false=非流式响应（一次性返回完整结果）")

class BaseResponse(BaseModel):
    code: int  # 状态码：200=成功，500=错误
    message: str  # 状态描述信息
    data: Optional[str] = None  # 业务数据（智能体回答内容）
    product_list: Optional[list] = None  # 相关保险产品列表

# ---------------------------- 辅助函数 ----------------------------
def create_response_data(code: int, message: str, data: Optional[str] = None, product_list: Optional[list] = None) -> dict:
    """
    统一创建响应数据结构的辅助函数
    确保流式和非流式响应使用相同的数据格式，便于客户端统一解析

    参数:
        code: 状态码
        message: 状态描述
        data: 回答内容（可为None）
        product_list: 相关产品列表（可为None）

    返回:
        标准化的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "product_list": product_list
    }

def create_stream_data(code: int, message: str, data: Optional[str] = None, product_list: Optional[list] = None) -> str:
    """
    创建符合SSE（Server-Sent Events）格式的流式响应字符串
    SSE格式要求每条数据以"data: "开头，以"\n\n"结尾

    参数:
        同create_response_data

    返回:
        符合SSE格式的字符串
    """
    # 复用基础响应结构，转换为JSON字符串后包装成SSE格式
    response_data = create_response_data(code, message, data, product_list)
    return f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

# ---------------------------- 响应处理逻辑 ----------------------------
async def generate_stream(request: InsuranceServiceRequest) -> AsyncGenerator[str, None]:
    """
    流式响应生成器（异步生成器）
    用于逐步产生响应数据，实现"边处理边返回"的效果

    参数:
        request: 客户端请求数据（包含用户ID、问题、stream参数）

    返回:
        异步生成器，逐个产生SSE格式的响应数据块
    """
    try:
        # 使用用户ID作为会话ID
        session_id = request.user_id
        # 获取或初始化该会话的State
        current_state = sessions.get(session_id)
        if current_state is None:
            current_state = State(messages=[], current_step="start", extracted_data={})
            # 初始化product_data字段（如果不存在）
            if not hasattr(current_state, 'product_data'):
                current_state.product_data = {"matched_products": []}
            sessions[session_id] = current_state

        # 添加用户输入
        current_state.messages.append({"role": "user", "content": request.user_question})

        # 调用工作流获取结果
        try:
            result = workflow.invoke(
                current_state.model_dump(),
                config={"configurable": {"thread_id": session_id}}
            )
            
            # 更新状态
            current_state = State(**result)
            sessions[session_id] = current_state
            
            # 提取智能体的完整回答
            agent_answer = result['messages'][-1]['content'] if result.get('messages') else '抱歉，无法获取回答'
            # 从state.product_data["matched_products"]获取产品列表
            product_list = []
            if hasattr(current_state, 'product_data') and current_state.product_data is not None and isinstance(current_state.product_data, dict):
                product_list = current_state.product_data.get("matched_products", [])

            # 模拟流式输出
            sentences = agent_answer.split('。')
            for i, sentence in enumerate(sentences):
                if not sentence: continue
                if i < len(sentences) - 1:
                    sentence += '。'

                yield create_stream_data(
                    200,
                    "处理中" if i < len(sentences) - 1 else "处理完成",
                    sentence,
                    product_list
                )
                await asyncio.sleep(0.3)
        except Exception as e:
            # 捕获异常并返回错误信息
            error_msg = f"系统处理失败：{str(e)}"
            yield create_stream_data(500, error_msg, None, None)

        # 发送流式结束标志，通知客户端所有数据已发送完毕
        yield "data: [DONE]\n\n"

    except Exception as e:
        # 捕获异常并返回错误信息
        yield create_stream_data(500, f"系统处理失败：{str(e)}", None, None)
        # 发送结束标志
        yield "data: [DONE]\n\n"

async def get_full_response(request: InsuranceServiceRequest) -> BaseResponse:
    """
    非流式响应处理函数
    用于一次性返回完整结果（适用于不需要实时展示的场景）

    参数:
        request: 客户端请求数据

    返回:
        BaseResponse对象，包含完整回答和产品列表
    """
    try:
        # 使用用户ID作为会话ID
        session_id = request.user_id
        # 获取或初始化该会话的State
        current_state = sessions.get(session_id)
        if current_state is None:
            current_state = State(messages=[], current_step="start", extracted_data={})
            # 初始化product_data字段（如果不存在）
            if not hasattr(current_state, 'product_data'):
                current_state.product_data = {"matched_products": []}
            sessions[session_id] = current_state

        # 添加用户输入
        current_state.messages.append({"role": "user", "content": request.user_question})

        # 调用工作流获取完整结果
        result = workflow.invoke(
            current_state.model_dump(),
            config={"configurable": {"thread_id": session_id}}
        )
        print('result:',result)
        # 更新状态
        current_state = State(**result)
        sessions[session_id] = current_state

        # 提取智能体回答
        agent_answer = result['messages'][-1]['content']
        # 从state.product_data["matched_products"]获取产品列表
        product_list = []
        if hasattr(current_state, 'product_data') and current_state.product_data is not None:
            product_list = current_state.product_data.get("matched_products", [])

        # 返回标准化的成功响应
        return BaseResponse(
            code=200,
            message="处理完成",
            data=agent_answer,
            product_list=product_list
        )
    except Exception as e:
        # 捕获异常并返回错误响应
        return BaseResponse(
            code=500,
            message=f"系统处理失败：{str(e)}",
            data=None,
            product_list=None
        )

@app.post("/insurance/question-inquiry", summary="处理保险用户提问并返回智能体回答（支持流式/非流式控制）")
async def insurance_intelligent_service(request: InsuranceServiceRequest):
    """
    保险业务智能问答接口

    根据请求参数stream的值，动态返回流式响应或非流式响应：
    - stream=True：返回text/event-stream类型的流式响应，逐步输出回答
    - stream=False：返回application/json类型的完整响应，一次性输出结果
    """
    # 根据stream参数决定响应类型
    if request.stream:
        return StreamingResponse(
            generate_stream(request),  # 绑定流式生成器
            media_type="text/event-stream"  # SSE格式对应的MIME类型
        )
    else:
        # 返回非流式JSON响应
        return await get_full_response(request)


import uvicorn

if __name__ == "__main__":
    print(f"Starting server on {APP_HOST}:{APP_PORT}...")
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)
