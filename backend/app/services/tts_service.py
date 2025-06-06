import asyncio
import uuid
import tempfile
import os
import hashlib
import json
from typing import Optional, Dict, Any, List, AsyncGenerator
import logging
from datetime import datetime

from app.services.volcano_client import volcano_client
from app.services.cache_service import cache_service
from app.schemas.tts import TTSRequest, TTSResponse, VoiceInfo, VoiceCategory, VoiceListResponse
from app.core.config import settings
from app.utils.audio_utils import get_audio_duration, format_file_size

logger = logging.getLogger(__name__)


class TTSService:
    """TTS核心服务"""
    
    def __init__(self):
        self.volcano_client = volcano_client
        self.cache_service = cache_service
        self._voice_cache = None
        
    async def synthesize_text(
        self,
        request: TTSRequest,
        user_id: Optional[str] = None
    ) -> TTSResponse:
        """
        同步语音合成（带缓存优化）
        
        Args:
            request: TTS请求参数
            user_id: 用户ID（可选）
            
        Returns:
            TTS响应结果
        """
        try:
            # 生成缓存键
            cache_key = self.cache_service.generate_cache_key(
                "tts",
                text=request.text,
                voice_id=request.voice_id,
                speed=request.speed,
                volume=request.volume,
                pitch=request.pitch,
                format=request.format,
                emotion=request.emotion or "neutral"
            )
            
            # 检查缓存
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                # 生成新的请求ID，但保持其他数据
                cached_result["request_id"] = str(uuid.uuid4())
                cached_result["created_at"] = datetime.utcnow()
                
                # 重新构建file_path（缓存中不包含完整路径）
                filename = f"tts_{cached_result['request_id']}.{cached_result.get('format', 'mp3')}"
                cached_result["file_path"] = os.path.join(settings.AUDIO_FILES_PATH, filename)
                
                logger.info(f"缓存命中: {cache_key[:16]}... 跳过语音合成")
                return TTSResponse(**cached_result)
            
            # 生成请求ID和文件路径
            request_id = str(uuid.uuid4())
            # 确保format是字符串格式，不是枚举对象
            format_str = request.format.value if hasattr(request.format, 'value') else str(request.format)
            filename = f"tts_{request_id}.{format_str}"
            file_path = os.path.join(settings.AUDIO_FILES_PATH, filename)
            
            logger.info(f"开始语音合成: {request_id}, 文本长度: {len(request.text)}")
            
            # 调用火山引擎合成
            result = await self.volcano_client.synthesize_to_file(
                text=request.text,
                voice_type=request.voice_id,
                output_path=file_path,
                speed_ratio=request.speed,
                volume_ratio=request.volume,
                pitch_ratio=request.pitch,
                encoding=request.format,
                emotion=request.emotion
            )
            
            # 获取音频时长
            duration = None
            try:
                duration = await get_audio_duration(file_path)
            except Exception as e:
                logger.warning(f"获取音频时长失败: {str(e)}")
            
            # 生成文件URL
            file_url = f"/audio/{filename}"
            
            # 构建响应
            response = TTSResponse(
                request_id=request_id,
                text=request.text,
                voice_id=request.voice_id,
                file_path=file_path,
                file_url=file_url,
                file_size=result["file_size"],
                duration=duration,
                format=request.format,
                synthesis_time=result["synthesis_time"],
                created_at=datetime.utcnow(),
                status="success"
            )
            
            # 缓存结果（不包含敏感路径信息）
            cache_data = response.dict()
            cache_data.pop("file_path", None)  # 不缓存完整文件路径
            await self.cache_service.set(
                cache_key,
                cache_data,
                expire=settings.CACHE_EXPIRE_SECONDS
            )
            
            # 保存历史记录（如果有用户ID）
            if user_id:
                await self._save_history(user_id, request, response)
            
            logger.info(f"语音合成完成: {request_id}, 文件大小: {format_file_size(result['file_size'])}")
            return response
            
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}")
            raise Exception(f"语音合成失败: {str(e)}")
    
    async def synthesize_stream(self, request: TTSRequest):
        """
        流式语音合成
        
        Args:
            request: TTS请求参数
            
        Yields:
            音频数据块
        """
        try:
            logger.info(f"开始流式语音合成, 文本长度: {len(request.text)}")
            
            async for chunk in self.volcano_client.synthesize_stream(
                text=request.text,
                voice_type=request.voice_id,
                speed_ratio=request.speed,
                volume_ratio=request.volume,
                pitch_ratio=request.pitch,
                encoding=request.format,
                emotion=request.emotion
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"流式语音合成失败: {str(e)}")
            raise Exception(f"流式语音合成失败: {str(e)}")
    
    async def get_voice_list(self, category: Optional[str] = None) -> VoiceListResponse:
        """
        获取音色列表（基于voice_presets_complete.json）
        
        Args:
            category: 音色分类过滤
            
        Returns:
            音色列表响应
        """
        if self._voice_cache is None:
            await self._load_voice_data()
        
        # 如果指定了分类，过滤结果
        if category:
            categories = [cat for cat in self._voice_cache["categories"] if cat.name == category]
        else:
            categories = self._voice_cache["categories"]
        
        total_count = sum(len(cat.voices) for cat in categories)
        
        return VoiceListResponse(
            categories=categories,
            total_count=total_count,
            emotion_voices=self._voice_cache["emotion_voices"]
        )
    
    async def get_voice_info(self, voice_id: str) -> Optional[VoiceInfo]:
        """
        获取指定音色的详细信息
        
        Args:
            voice_id: 音色ID
            
        Returns:
            音色信息，如果不存在返回None
        """
        if self._voice_cache is None:
            await self._load_voice_data()
        
        for category in self._voice_cache["categories"]:
            for voice in category.voices:
                if voice.id == voice_id:
                    return voice
        
        return None
    
    async def get_voice_name(self, voice_id: str) -> Optional[str]:
        """
        获取音色的显示名称
        
        Args:
            voice_id: 音色ID
            
        Returns:
            音色的中文名称，如果不存在返回None
        """
        voice_info = await self.get_voice_info(voice_id)
        if voice_info:
            return voice_info.name
        return None
    
    async def test_voice_connection(self) -> bool:
        """测试火山引擎连接"""
        try:
            return await self.volcano_client.test_connection()
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            return False
    
    async def _load_voice_data(self):
        """从voice_presets_complete.json加载完整音色数据"""
        try:
            # 查找voice_presets_complete.json文件
            voice_config_path = None
            
            # 尝试几个可能的路径
            possible_paths = [
                os.path.join(os.getcwd(), "voice_presets_complete.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "voice_presets_complete.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "voice_presets_complete.json"),
                "voice_presets_complete.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    voice_config_path = path
                    break
            
            if not voice_config_path:
                logger.warning("未找到voice_presets_complete.json文件，使用默认音色数据")
                self._voice_cache = await self._get_fallback_voice_data()
                return
            
            # 加载JSON文件
            with open(voice_config_path, 'r', encoding='utf-8') as f:
                voice_data = json.load(f)
            
            logger.info(f"从 {voice_config_path} 加载音色数据")
            
            # 转换数据结构
            categories = []
            voice_categories = voice_data.get("voice_categories", {})
            voice_presets = voice_data.get("voice_presets", {})
            
            for category_name, category_info in voice_categories.items():
                voices = []
                
                # 获取该分类下的音色
                if category_name in voice_presets:
                    for voice_data_item in voice_presets[category_name]:
                        voice = VoiceInfo(
                            id=voice_data_item["id"],
                            name=voice_data_item["name"],
                            description=voice_data_item["description"],
                            category=voice_data_item["category"],
                            language=voice_data_item["language"],
                            tags=voice_data_item.get("tags", []),
                            emotions=voice_data_item.get("emotions")
                        )
                        voices.append(voice)
                
                category = VoiceCategory(
                    name=category_name,
                    description=category_info["description"],
                    icon=category_info["icon"],
                    color=category_info["color"],
                    special=category_info.get("special", False),
                    voices=voices
                )
                categories.append(category)
            
            # 获取情感音色列表
            emotion_config = voice_data.get("emotion_config", {})
            emotion_voices = emotion_config.get("emotion_voices", [])
            
            self._voice_cache = {
                "categories": categories,
                "emotion_voices": emotion_voices
            }
            
            total_voices = sum(len(cat.voices) for cat in categories)
            logger.info(f"音色数据加载完成，共 {len(categories)} 个分类，{total_voices} 个音色")
            
        except Exception as e:
            logger.error(f"加载音色数据失败: {str(e)}")
            # 使用默认数据
            self._voice_cache = await self._get_fallback_voice_data()
    
    async def _get_fallback_voice_data(self) -> Dict[str, Any]:
        """获取回退音色数据"""
        logger.warning("使用回退音色数据")
        return {
            "categories": [
                VoiceCategory(
                    name="通用音色",
                    description="基础音色",
                    icon="🎙️",
                    color="#4ECDC4",
                    special=False,
                    voices=[
                        VoiceInfo(
                            id=settings.DEFAULT_VOICE_ID,
                            name="默认女声",
                            description="默认女声音色",
                            category="通用",
                            language="zh-CN",
                            tags=["通用", "女声"]
                        )
                    ]
                )
            ],
            "emotion_voices": []
        }
    
    async def _save_history(
        self,
        user_id: str,
        request: TTSRequest,
        response: TTSResponse
    ):
        """保存历史记录"""
        # 这里应该保存到数据库
        # 暂时记录日志
        logger.info(
            f"保存历史记录: 用户={user_id}, 请求={response.request_id}, "
            f"文本长度={len(request.text)}, 音色={request.voice_id}"
        )
    
    def generate_cache_key(self, request: TTSRequest) -> str:
        """生成缓存键"""
        key_parts = [
            request.text,
            request.voice_id,
            str(request.speed),
            str(request.volume),
            str(request.pitch),
            request.format,
            request.emotion or "neutral"
        ]
        key_string = "|".join(key_parts)
        return f"tts:{hashlib.md5(key_string.encode()).hexdigest()}"


# 创建全局服务实例
tts_service = TTSService()