from typing import List
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# 修改导入方式，因为目录结构变了
try:
    from captcha_recognizer.slider import Slider
except ImportError:
    # 用于本地测试
    import sys
    sys.path.append(".")
    from captcha_recognizer.slider import Slider

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DetectionResult(BaseModel):
    box: List[int]  # [x1, y1, x2, y2]
    confidence: float
    message: str = None

@app.get("/")
def hello_captcha():
    return {"Hello": "Captcha"}

@app.post("/captcha")
async def captcha(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        # 将字节流转换为numpy数组
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return {"box": [], "confidence": 0, "message": "不支持的图片"}
        
        box, confidence = Slider().identify(source=image)
        # box元素 float转为int
        box = [int(x) for x in box]
        return {"box": box, "confidence": confidence}
    except Exception as e:
        return {"box": [], "confidence": 0, "message": f"处理出错: {str(e)}"}

# Vercel 需要这个处理函数
def handler(request: Request):
    # Vercel 会将请求转换为 ASGI 请求
    from fastapi.responses import JSONResponse
    import json
    
    if request.method == "GET":
        return JSONResponse(hello_captcha())
    elif request.method == "POST" and request.url.path == "/captcha":
        # 这里需要处理文件上传，但在 Vercel 中可能需要调整
        pass
    
    return JSONResponse({"error": "Not found"}, status_code=404)
