from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import time

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.5


def compress_num_list(num_list):
    # Compress continuous numbers into ranges    
    if not num_list:
        return ""
    
    start = num_list[0]
    end = num_list[0]

    builder = []
    
    for num in num_list[1:]:
        if num == end + 1:
            end = num
        else:
            if start == end:
                builder.append(str(start))
            else:
                builder.append(f"{start}-{end}")
            start = num
            end = num
    
    if start == end:
        builder.append(str(start))
    else:
        builder.append(f"{start}-{end}")
    
    return ", ".join(builder)

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list is empty")
    
    # 获取最后一条用户消息
    last_message = request.messages[-1].content
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="Last message is not from user")
    lines = last_message.split("\n")
    translated_lines = []

    # 遍历并打印每条消息的 role 和压缩行号
    for message in request.messages:
        msg_line_numbers = []
        for line in message.content.split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if parts and parts[0].isdigit():
                msg_line_numbers.append(int(parts[0]))
        
        compressed = compress_num_list(msg_line_numbers)
        print(f"Role: {message.role}, Lines: {compressed}")
    print("-" * 20)

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 预期格式: line_number|character|text
        parts = line.split("|")
        if len(parts) != 3:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": {
                        "message": f"Invalid line format: '{line}'. Expected 'line_number|character|text'",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": None
                    }
                }
            )
            
        line_num, character, text = parts
        # 返回格式: line_number|character|[line_number] text
        translated_lines.append(f"{line_num}|{character}|[{line_num}] {text}")

    response_content = "\n".join(translated_lines)
    
    # 模拟 OpenAI 响应结构
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
