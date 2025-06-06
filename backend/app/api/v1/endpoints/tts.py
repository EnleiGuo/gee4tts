from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, File, UploadFile, Request
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import logging
from datetime import datetime
import uuid

from app.schemas.tts import (
    TTSRequest, TTSResponse, TTSStreamRequest, VoiceListResponse,
    BatchTTSRequest, BatchTTSResponse, SuccessResponse
)
from app.services.tts_service import tts_service
from app.utils.audio_utils import format_file_size
from app.core.database import get_db
from app.core.auth import get_current_user_optional, check_request_rate_limit
from app.models.user import User
from app.models.tts_history import TTSHistory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/synthesize", response_model=TTSResponse, summary="同步语音合成")
async def synthesize_text(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    rate_limit_check = Depends(check_request_rate_limit),
    db: Session = Depends(get_db)
):
    """
    同步语音合成接口
    
    - **text**: 要合成的文本（最大1000字符）
    - **voice_id**: 音色ID，可通过 /voices 接口获取
    - **speed**: 语速倍率 (0.5-2.0)，默认1.0
    - **volume**: 音量倍率 (0.1-2.0)，默认1.0
    - **pitch**: 音调倍率 (0.5-2.0)，默认1.0
    - **format**: 音频格式，支持 mp3/wav/pcm
    - **emotion**: 情感类型（仅部分音色支持）
    - **bitrate**: 比特率(kbps)，默认128
    - **sample_rate**: 采样率(Hz)，默认24000
    
    返回合成结果信息，包含文件路径和下载链接
    """
    try:
        user_id = current_user.id if current_user else None
        logger.info(f"收到语音合成请求: 用户={user_id or '匿名'}, 文本长度={len(request.text)}, 音色={request.voice_id}")
        
        # 创建历史记录
        request_id = str(uuid.uuid4())
        history = TTSHistory(
            request_id=request_id,
            user_id=user_id,
            text=request.text,
            text_length=len(request.text),
            voice_id=request.voice_id,
            speed=request.speed,
            volume=request.volume,
            pitch=request.pitch,
            format=request.format,
            emotion=request.emotion,
            ip_address=getattr(http_request.client, 'host', None),
            user_agent=http_request.headers.get("user-agent")
        )
        
        db.add(history)
        db.commit()
        db.refresh(history)
        
        # 标记开始处理
        history.mark_started()
        db.commit()
        
        # 执行语音合成
        response = await tts_service.synthesize_text(request, str(user_id) if user_id else None)
        
        # 更新历史记录
        file_info = {
            "file_path": response.file_path,
            "file_url": response.file_url,
            "file_size": response.file_size,
            "audio_duration": response.duration
        }
        history.mark_completed(file_info)
        
        # 计算消耗
        cost = history.calculate_cost()
        
        # 更新用户统计
        if current_user:
            current_user.increment_usage(len(request.text), response.duration)
        
        # 提交所有更改到数据库
        db.commit()
        
        # 添加后台任务
        background_tasks.add_task(log_synthesis_stats, request, response, current_user)
        
        logger.info(f"语音合成成功: {response.request_id}, 消耗积分: {cost}")
        return response
        
    except Exception as e:
        # 标记失败
        if 'history' in locals():
            history.mark_failed(str(e))
            db.commit()
        
        logger.error(f"语音合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.post("/synthesize/stream", summary="流式语音合成")
async def synthesize_stream(
    request: TTSStreamRequest,
    user_id: Optional[str] = None
):
    """
    流式语音合成接口
    
    返回实时音频流，适合：
    - 大段文本合成
    - 需要低延迟的场景
    - 实时播放需求
    
    响应为音频流，可直接播放或保存
    """
    try:
        logger.info(f"收到流式合成请求: 文本长度={len(request.text)}, 音色={request.voice_id}")
        
        async def generate_audio():
            async for chunk in tts_service.synthesize_stream(request):
                yield chunk
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_stream_{timestamp}.{request.format}"
        
        return StreamingResponse(
            generate_audio(),
            media_type=f"audio/{request.format}",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Synthesis-Info": f"text_length={len(request.text)};voice={request.voice_id}"
            }
        )
        
    except Exception as e:
        logger.error(f"流式语音合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"流式语音合成失败: {str(e)}")


# 继续剩余的接口...

# 后台任务函数
async def log_synthesis_stats(request: TTSRequest, response: TTSResponse):
    """记录合成统计信息"""
    try:
        stats = {
            "request_id": response.request_id,
            "text_length": len(request.text),
            "voice_id": request.voice_id,
            "file_size": response.file_size,
            "duration": response.duration,
            "synthesis_time": response.synthesis_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"合成统计: {stats}")
        
    except Exception as e:
        logger.error(f"记录统计失败: {str(e)}")