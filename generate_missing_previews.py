#!/usr/bin/env python3
"""
补充生成失败音色的试听音频脚本
增加延迟时间避免429频率限制错误
"""
import asyncio
import aiohttp
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# 配置
API_BASE_URL = "http://localhost:8000"
PREVIEW_TEXT = "我是您的专属声音，快来试试！"
PREVIEW_DIR = "audio_files/previews"
BATCH_SIZE = 1  # 每批只处理1个音色，减少频率
DELAY_BETWEEN_REQUESTS = 5  # 每个请求间延迟5秒

def load_failed_voices() -> List[str]:
    """从上次的生成报告中加载失败的音色ID"""
    report_file = Path(PREVIEW_DIR) / "generation_report.json"
    failed_voice_ids = []
    
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for result in data.get("results", []):
                if result.get("status") == "error":
                    failed_voice_ids.append(result["voice_id"])
    
    return failed_voice_ids

async def get_voice_info(voice_id: str) -> Dict[str, Any]:
    """根据voice_id获取音色信息"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/api/v1/voices/") as response:
            if response.status == 200:
                data = await response.json()
                for category in data["categories"]:
                    for voice in category["voices"]:
                        if voice["id"] == voice_id:
                            return {
                                "voice_id": voice["id"],
                                "name": voice["name"],
                                "category": voice["category"],
                                "description": voice["description"]
                            }
    return {"voice_id": voice_id, "name": "未知音色", "category": "未知", "description": ""}

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
        
        print(f"🎵 正在生成 {voice['name']} ({voice['category']})...")
        
        async with session.post(
            f"{API_BASE_URL}/api/v1/tts/synthesize",
            json=request_data,
            timeout=aiohttp.ClientTimeout(total=60)
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
                            
                            print(f"✅ {voice['name']} - {len(audio_data)} bytes")
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
            elif response.status == 429:
                # 如果还是429错误，增加更长的延迟
                print(f"⚠️  {voice['name']} 频率限制，等待更长时间...")
                await asyncio.sleep(10)
                raise Exception("频率限制，需要重试")
            else:
                error_text = await response.text()
                raise Exception(f"合成失败 {response.status}: {error_text}")
                
    except Exception as e:
        print(f"❌ {voice['name']} 失败: {str(e)}")
        return {"voice_id": voice_id, "status": "error", "error": str(e)}

async def generate_missing_previews():
    """生成缺失的音色试听音频"""
    print("🔄 开始补充生成失败的音色试听音频...")
    
    # 获取失败的音色ID列表
    failed_voice_ids = load_failed_voices()
    
    if not failed_voice_ids:
        print("🎉 没有失败的音色需要重新生成！")
        return
    
    print(f"📋 找到 {len(failed_voice_ids)} 个失败的音色需要重新生成")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for i, voice_id in enumerate(failed_voice_ids):
            print(f"\n📦 处理 {i+1}/{len(failed_voice_ids)}: {voice_id}")
            
            # 获取音色信息
            voice_info = await get_voice_info(voice_id)
            
            if not voice_info["name"] or voice_info["name"] == "未知音色":
                print(f"⚠️  无法找到音色信息: {voice_id}")
                results.append({"voice_id": voice_id, "status": "error", "error": "音色不存在"})
                continue
            
            # 生成试听音频
            result = await synthesize_preview(session, voice_info)
            results.append(result)
            
            # 每个请求后延迟
            if i < len(failed_voice_ids) - 1:
                print(f"⏸️  等待 {DELAY_BETWEEN_REQUESTS} 秒...")
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    
    # 统计结果
    success_count = sum(1 for r in results if r.get("status") == "success")
    exists_count = sum(1 for r in results if r.get("status") == "exists")
    error_count = sum(1 for r in results if r.get("status") == "error")
    
    print(f"\n📊 补充生成完成!")
    print(f"✅ 成功: {success_count}")
    print(f"⏭️  已存在: {exists_count}")
    print(f"❌ 失败: {error_count}")
    
    # 更新报告
    original_report_file = Path(PREVIEW_DIR) / "generation_report.json"
    if original_report_file.exists():
        with open(original_report_file, "r", encoding="utf-8") as f:
            original_data = json.load(f)
        
        # 更新原始结果
        for new_result in results:
            voice_id = new_result["voice_id"]
            # 找到并更新对应的结果
            for i, old_result in enumerate(original_data["results"]):
                if old_result["voice_id"] == voice_id:
                    original_data["results"][i] = new_result
                    break
        
        # 重新计算统计
        all_results = original_data["results"]
        original_data["success_count"] = sum(1 for r in all_results if r.get("status") == "success")
        original_data["exists_count"] = sum(1 for r in all_results if r.get("status") == "exists")
        original_data["error_count"] = sum(1 for r in all_results if r.get("status") == "error")
        original_data["last_updated"] = time.time()
        
        # 保存更新后的报告
        with open(original_report_file, "w", encoding="utf-8") as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 报告已更新: {original_report_file}")
        print(f"📁 总计音色: {len(all_results)}")
        print(f"✅ 总成功: {original_data['success_count']}")
        print(f"❌ 总失败: {original_data['error_count']}")

if __name__ == "__main__":
    asyncio.run(generate_missing_previews()) 