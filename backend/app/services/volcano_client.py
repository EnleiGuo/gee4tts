import asyncio
import websockets
import json
import gzip
import uuid
import ssl
import tempfile
import os
from typing import AsyncGenerator, Optional, Dict, Any, List
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class VolcanoTTSClient:
    """火山引擎TTS客户端（基于您原有代码改进）"""
    
    def __init__(self, app_id: str = None, access_token: str = None, cluster: str = None):
        self.app_id = app_id or settings.VOLCANO_APP_ID
        self.access_token = access_token or settings.VOLCANO_ACCESS_TOKEN
        self.cluster = cluster or settings.VOLCANO_CLUSTER
        self.host = settings.VOLCANO_HOST
        self.api_url = f"wss://{self.host}/api/v1/tts/ws_binary"
        
        # 协议头（来自您的原代码）
        self.default_header = bytearray(b'\x11\x10\x11\x00')
        
        # 消息类型映射
        self.MESSAGE_TYPES = {
            11: "audio-only server response", 
            12: "frontend server response", 
            15: "error message from server"
        }
        
        # 支持情感的音色列表（动态加载）
        self.emotion_voices = self._load_emotion_voices()
    
    def _load_emotion_voices(self) -> List[str]:
        """从voice_presets_complete.json加载支持情感的音色列表"""
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
                logger.warning("未找到voice_presets_complete.json文件，使用默认情感音色列表")
                return self._get_default_emotion_voices()
            
            # 加载JSON文件
            with open(voice_config_path, 'r', encoding='utf-8') as f:
                voice_data = json.load(f)
            
            # 获取支持情感的音色列表
            emotion_config = voice_data.get("emotion_config", {})
            emotion_voices = emotion_config.get("emotion_voices", [])
            
            if emotion_voices:
                logger.info(f"从配置文件加载了 {len(emotion_voices)} 个支持情感的音色")
                return emotion_voices
            else:
                logger.warning("配置文件中未找到情感音色配置，使用默认列表")
                return self._get_default_emotion_voices()
                
        except Exception as e:
            logger.error(f"加载情感音色配置失败: {str(e)}，使用默认列表")
            return self._get_default_emotion_voices()
    
    def _get_default_emotion_voices(self) -> List[str]:
        """获取默认的支持情感的音色列表"""
        return [
            "zh_male_beijingxiaoye_emo_v2_mars_bigtts",
            "zh_female_roumeinvyou_emo_v2_mars_bigtts",
            "zh_male_yangguangqingnian_emo_v2_mars_bigtts",
            "zh_female_meilinvyou_emo_v2_mars_bigtts",
            "zh_female_shuangkuaisisi_emo_v2_mars_bigtts"
        ]
    
    async def synthesize_to_file(
        self,
        text: str,
        voice_type: str,
        output_path: str,
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
        encoding: str = "mp3",
        emotion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合成语音并保存到文件（来自您的原代码逻辑）
        
        Args:
            text: 要合成的文本
            voice_type: 音色类型
            output_path: 输出文件路径
            speed_ratio: 语速比例
            volume_ratio: 音量比例
            pitch_ratio: 音调比例
            encoding: 编码格式
            emotion: 情感类型
            
        Returns:
            包含合成结果信息的字典
        """
        request_id = str(uuid.uuid4())
        
        # 构建JSON请求（基于您的原代码）
        request_json = {
            "app": {
                "appid": self.app_id,
                "token": self.access_token,
                "cluster": self.cluster
            },
            "user": {
                "uid": str(uuid.uuid4())
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": encoding.value if hasattr(encoding, 'value') else str(encoding),
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
            },
            "request": {
                "reqid": request_id,
                "text": text,
                "text_type": "plain",
                "operation": "submit"
            }
        }
        
        # 添加情感参数（如果支持）
        if emotion and self.supports_emotion(voice_type):
            request_json["request"]["emotion"] = emotion
            logger.info(f"为音色 {voice_type} 设置情感: {emotion}")
        
        try:
            audio_data = bytearray()
            start_time = datetime.utcnow()
            
            async for chunk in self._synthesize_stream(request_json):
                audio_data.extend(chunk)
            
            # 保存文件
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "request_id": request_id,
                "file_path": output_path,
                "file_size": len(audio_data),
                "synthesis_time": duration,
                "created_at": start_time.isoformat(),
                "status": "success"
            }
            
            logger.info(f"语音合成完成: {request_id}, 文件大小: {len(audio_data)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}")
            raise Exception(f"语音合成失败: {str(e)}")
    
    async def synthesize_stream(
        self,
        text: str,
        voice_type: str,
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
        encoding: str = "mp3",
        emotion: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        流式语音合成
        
        Args:
            text: 要合成的文本
            voice_type: 音色类型
            speed_ratio: 语速比例
            volume_ratio: 音量比例
            pitch_ratio: 音调比例
            encoding: 编码格式
            emotion: 情感类型
            
        Yields:
            音频数据块
        """
        request_json = {
            "app": {
                "appid": self.app_id,
                "token": self.access_token,
                "cluster": self.cluster
            },
            "user": {
                "uid": str(uuid.uuid4())
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": encoding.value if hasattr(encoding, 'value') else str(encoding),
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "submit"
            }
        }
        
        # 添加情感参数（如果支持）
        if emotion and self.supports_emotion(voice_type):
            request_json["request"]["emotion"] = emotion
            logger.info(f"流式合成为音色 {voice_type} 设置情感: {emotion}")
        
        async for chunk in self._synthesize_stream(request_json):
            yield chunk
    
    async def _synthesize_stream(self, request_json: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
        """内部流式合成方法（基于您的原WebSocket代码）"""
        
        # 构建请求数据（来自您的原代码）
        payload_bytes = str.encode(json.dumps(request_json))
        payload_bytes = gzip.compress(payload_bytes)
        full_client_request = bytearray(self.default_header)
        full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))
        full_client_request.extend(payload_bytes)
        
        # SSL配置
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 请求头
        headers = {"Authorization": f"Bearer; {self.access_token}"}
        
        try:
            async with websockets.connect(
                self.api_url,
                additional_headers=headers,
                ping_interval=None,
                ssl=ssl_context,
                close_timeout=settings.SYNTHESIS_TIMEOUT
            ) as websocket:
                
                # 发送请求
                await websocket.send(full_client_request)
                
                # 接收响应
                while True:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=settings.SYNTHESIS_TIMEOUT
                        )
                        
                        done, audio_chunk = self._parse_response(response)
                        
                        if audio_chunk:
                            yield audio_chunk
                        
                        if done:
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error("WebSocket接收超时")
                        break
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket连接关闭")
                        break
                        
        except Exception as e:
            logger.error(f"WebSocket连接失败: {str(e)}")
            raise
    
    def _parse_response(self, response: bytes) -> tuple[bool, Optional[bytes]]:
        """解析响应数据（与GUI代码逻辑一致）"""
        try:
            if len(response) < 4:
                return False, None
            
            # 解析协议头
            protocol_version = response[0] >> 4
            header_size = response[0] & 0x0f
            message_type = response[1] >> 4
            message_type_specific_flags = response[1] & 0x0f
            serialization_method = response[2] >> 4
            message_compression = response[2] & 0x0f
            reserved = response[3]
            
            header_length = header_size * 4
            payload = response[header_length:]
            
            logger.info(
                f"Protocol: {protocol_version}, Header: {header_size}, "
                f"Type: {message_type}, Flags: {message_type_specific_flags}"
            )
            
            if message_type == 0xb:  # audio-only server response
                if message_type_specific_flags == 0:
                    return False, None
                
                sequence_number = int.from_bytes(payload[:4], "big", signed=True)
                payload_size = int.from_bytes(payload[4:8], "big", signed=False)
                audio_data = payload[8:]
                
                logger.info(f"序列号: {sequence_number}, 数据大小: {payload_size}")
                
                # 与GUI代码完全一致的逻辑：
                # 序列号小于0表示这是最后一个包，返回(True, audio_data)
                return sequence_number < 0, audio_data
            
            elif message_type == 0xf:  # error message
                code = int.from_bytes(payload[:4], "big", signed=False)
                msg_size = int.from_bytes(payload[4:8], "big", signed=False)
                error_msg = payload[8:]
                
                if message_compression == 1:
                    error_msg = gzip.decompress(error_msg)
                
                error_msg = str(error_msg, "utf-8")
                logger.error(f"TTS API错误 {code}: {error_msg}")
                raise Exception(f"TTS API错误 {code}: {error_msg}")
            
            elif message_type == 0xc:  # frontend server response
                msg_size = int.from_bytes(payload[:4], "big", signed=False)
                payload = payload[4:]
                if message_compression == 1:
                    payload = gzip.decompress(payload)
                logger.info(f"前端消息: {payload}")
            
            return False, None
            
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            test_result = await self.synthesize_to_file(
                text="测试连接",
                voice_type=settings.DEFAULT_VOICE_ID,
                output_path=tempfile.mktemp(suffix=".mp3")
            )
            
            # 清理测试文件
            if os.path.exists(test_result["file_path"]):
                os.unlink(test_result["file_path"])
            
            logger.info("火山引擎TTS连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"火山引擎TTS连接测试失败: {str(e)}")
            return False
    
    def supports_emotion(self, voice_type: str) -> bool:
        """检查音色是否支持情感"""
        return voice_type in self.emotion_voices
    
    def reload_emotion_voices(self):
        """重新加载支持情感的音色列表"""
        self.emotion_voices = self._load_emotion_voices()
        logger.info(f"重新加载了 {len(self.emotion_voices)} 个支持情感的音色")


# 创建全局客户端实例
volcano_client = VolcanoTTSClient()