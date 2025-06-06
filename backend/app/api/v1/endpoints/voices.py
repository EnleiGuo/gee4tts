from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.schemas.tts import VoiceListResponse, VoiceInfo
from app.services.tts_service import tts_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=VoiceListResponse, summary="获取音色列表")
async def get_voice_list(
    category: Optional[str] = Query(None, description="音色分类过滤"),
    language: Optional[str] = Query(None, description="语言过滤"),
    emotion_support: Optional[bool] = Query(None, description="是否支持情感"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取可用音色列表
    
    - **category**: 音色分类，如：多情感音色、通用场景、趣味口音等
    - **language**: 语言过滤，如：zh-CN、en-US等
    - **emotion_support**: 是否只显示支持情感的音色
    - **search**: 搜索关键词，模糊匹配音色名称和描述
    
    返回分类化的音色列表，包含音色详细信息
    """
    try:
        logger.info(f"获取音色列表: category={category}, language={language}")
        
        # 获取基础音色列表
        voice_list = await tts_service.get_voice_list(category)
        
        # 应用过滤条件
        if language or emotion_support is not None or search:
            filtered_categories = []
            
            for cat in voice_list.categories:
                filtered_voices = []
                
                for voice in cat.voices:
                    # 语言过滤
                    if language and language not in voice.language:
                        continue
                    
                    # 情感支持过滤
                    if emotion_support is not None:
                        has_emotion = voice.emotions is not None and len(voice.emotions) > 0
                        if emotion_support and not has_emotion:
                            continue
                        if not emotion_support and has_emotion:
                            continue
                    
                    # 搜索过滤
                    if search:
                        search_text = search.lower()
                        if (search_text not in voice.name.lower() and 
                            search_text not in voice.description.lower() and
                            search_text not in ' '.join(voice.tags).lower()):
                            continue
                    
                    filtered_voices.append(voice)
                
                if filtered_voices:
                    cat.voices = filtered_voices
                    filtered_categories.append(cat)
            
            voice_list.categories = filtered_categories
            voice_list.total_count = sum(len(cat.voices) for cat in filtered_categories)
        
        logger.info(f"返回音色列表: {voice_list.total_count}个音色，{len(voice_list.categories)}个分类")
        return voice_list
        
    except Exception as e:
        logger.error(f"获取音色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取音色列表失败: {str(e)}")


@router.get("/{voice_id}", response_model=VoiceInfo, summary="获取音色详情")
async def get_voice_info(voice_id: str):
    """
    获取指定音色的详细信息
    
    - **voice_id**: 音色ID
    
    返回音色的完整信息，包括支持的情感、语言、标签等
    """
    try:
        logger.info(f"获取音色详情: {voice_id}")
        
        voice_info = await tts_service.get_voice_info(voice_id)
        
        if not voice_info:
            raise HTTPException(status_code=404, detail=f"音色不存在: {voice_id}")
        
        return voice_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音色详情失败: {voice_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取音色详情失败: {str(e)}")


@router.get("/statistics", summary="获取音色库统计信息")
async def get_voice_statistics():
    """
    获取音色库的详细统计信息
    
    返回音色分类、数量、支持的语言和情感等统计数据
    """
    try:
        logger.info("获取音色库统计信息")
        
        voice_list = await tts_service.get_voice_list()
        
        # 统计基础信息
        total_voices = voice_list.total_count
        total_categories = len(voice_list.categories)
        emotion_voice_count = len(voice_list.emotion_voices)
        
        return {
            "summary": {
                "total_voices": total_voices,
                "total_categories": total_categories,
                "emotion_voices": emotion_voice_count,
                "supported_languages": 4,  # 中英日西
                "supported_emotions": 9
            },
            "metadata": {
                "version": "2.0.0",
                "last_updated": "2024-06-04",
                "source": "voice_presets_complete.json"
            }
        }
        
    except Exception as e:
        logger.error(f"获取音色库统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取音色库统计失败: {str(e)}")