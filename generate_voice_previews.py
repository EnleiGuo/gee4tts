#!/usr/bin/env python3
"""
音色试听音频批量生成脚本
为所有音色生成标准试听音频：我是您的专属声音，快来试试！
"""
import asyncio
import aiohttp
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any

# 配置
API_BASE_URL = "http://localhost:8000"
PREVIEW_TEXT = "我是您的专属声音，快来试试！"
PREVIEW_DIR = "audio_files/previews"
BATCH_SIZE = 5  # 每批处理的音色数量
DELAY_BETWEEN_BATCHES = 2  # 批次间延迟秒数

def ensure_preview_dir():
    """确保预览音频目录存在"""
    Path(PREVIEW_DIR).mkdir(parents=True, exist_ok=True)
    print(f"预览音频目录: {PREVIEW_DIR}")

async def get_all_voices() -> List[Dict[str, Any]]:
    """获取所有音色信息"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/api/v1/voices/") as response:
            if response.status == 200:
                data = await response.json()
                voices = []
                for category in data["categories"]:
                    for voice in category["voices"]:
                        voices.append({
                            "voice_id": voice["id"],
                            "name": voice["name"],
                            "category": voice["category"],
                            "description": voice["description"]
                        })
                print(f"获取到 {len(voices)} 个音色")
                return voices
            else:
                raise Exception(f"获取音色失败: {response.status}")

async def synthesize_preview(session: aiohttp.ClientSession, voice: Dict[str, Any]) -> Dict[str, Any]:
    """为单个音色生成试听音频"""
    voice_id = voice["voice_id"]
    preview_file = Path(PREVIEW_DIR) / f"{voice_id}.mp3"
    
    # 如果文件已存在，跳过
    if preview_file.exists():
        print(f"⏭️  跳过 {voice['name']} (文件已存在)")
        return {"voice_id": voice_id, "status": "exists", "file": str(preview_file)}
    
    try:
        # 调用TTS合成接口
        request_data = {
            "text": PREVIEW_TEXT,
            "voice_id": voice_id,
            "format": "mp3",
            "sample_rate": 24000,
            "speed": 1.0,
            "volume": 1.0
        }
        
        async with session.post(
            f"{API_BASE_URL}/api/v1/tts/synthesize",
            json=request_data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                result = await response.json()
                
                # 下载音频文件
                if result.get("file_url"):
                    audio_url = f"{API_BASE_URL}{result['file_url']}"
                    async with session.get(audio_url) as audio_response:
                        if audio_response.status == 200:
                            audio_data = await audio_response.read()
                            
                            # 保存到预览目录
                            with open(preview_file, "wb") as f:
                                f.write(audio_data)
                            
                            print(f"✅ {voice['name']} ({voice['category']}) - {len(audio_data)} bytes")
                            return {
                                "voice_id": voice_id,
                                "status": "success",
                                "file": str(preview_file),
                                "size": len(audio_data),
                                "duration": result.get("duration", 0)
                            }
                        else:
                            raise Exception(f"下载音频失败: {audio_response.status}")
                else:
                    raise Exception("响应中没有音频URL")
            else:
                error_text = await response.text()
                raise Exception(f"合成失败 {response.status}: {error_text}")
                
    except Exception as e:
        print(f"❌ {voice['name']} 失败: {str(e)}")
        return {"voice_id": voice_id, "status": "error", "error": str(e)}

async def generate_all_previews():
    """批量生成所有音色的试听音频"""
    print("🎵 开始生成音色试听音频...")
    ensure_preview_dir()
    
    # 获取所有音色
    voices = await get_all_voices()
    
    results = []
    total_batches = (len(voices) + BATCH_SIZE - 1) // BATCH_SIZE
    
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(voices), BATCH_SIZE):
            batch = voices[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            
            print(f"\n📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 个音色)")
            
            # 并行处理当前批次
            tasks = [synthesize_preview(session, voice) for voice in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"❌ 批次处理异常: {result}")
                else:
                    results.append(result)
            
            # 批次间延迟
            if i + BATCH_SIZE < len(voices):
                print(f"⏸️  等待 {DELAY_BETWEEN_BATCHES} 秒...")
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)
    
    # 统计结果
    success_count = sum(1 for r in results if r.get("status") == "success")
    exists_count = sum(1 for r in results if r.get("status") == "exists")
    error_count = sum(1 for r in results if r.get("status") == "error")
    
    print(f"\n📊 生成完成!")
    print(f"✅ 成功: {success_count}")
    print(f"⏭️  已存在: {exists_count}")
    print(f"❌ 失败: {error_count}")
    print(f"📁 预览文件目录: {PREVIEW_DIR}")
    
    # 保存结果报告
    report_file = Path(PREVIEW_DIR) / "generation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "total_voices": len(voices),
            "success_count": success_count,
            "exists_count": exists_count,
            "error_count": error_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📄 详细报告已保存: {report_file}")

if __name__ == "__main__":
    asyncio.run(generate_all_previews()) 