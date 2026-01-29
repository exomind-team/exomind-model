"""
MOSS Cloud ASR Client
=====================

MOSS 云端语音识别引擎实现。

调用 MOSS Studio API 进行语音转写。
"""

import base64
import requests
from .base import ASRClient


class MossClient(ASRClient):
    """MOSS 云端 ASR 引擎"""
    
    API_ENDPOINT = "https://studio.mosi.cn/v1/audio/transcriptions"
    
    def __init__(self, api_key: str, model: str = "moss-transcribe-diarize"):
        """
        初始化 MOSS 客户端
        
        Args:
            api_key: MOSS API Key
            model: 模型名称（默认 moss-transcribe-diarize）
        """
        self._api_key = api_key
        self._model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @property
    def name(self) -> str:
        return "MOSS Cloud API"
    
    @property
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    def transcribe(self, audio_path: str) -> str:
        """
        转写音频文件
        
        Args:
            audio_path: 音频文件路径 (WAV)
            
        Returns:
            识别后的文本
        """
        # 读取音频并转为 Base64
        with open(audio_path, 'rb') as f:
            audio_content = f.read()
        
        b64_str = base64.b64encode(audio_content).decode('utf-8')
        audio_data = f"data:audio/wav;base64,{b64_str}"
        
        payload = {
            "model": self._model,
            "audio_data": audio_data,
            "sampling_params": {
                "max_new_tokens": 1024,
                "temperature": 0.0
            },
            "meta_info": True
        }
        
        response = requests.post(
            self.API_ENDPOINT,
            json=payload,
            headers=self._headers,
            timeout=600
        )
        response.raise_for_status()
        
        result = response.json()
        asr_result = result.get('asr_transcription_result', {})

        # MOSS moss-transcribe-diarize 模型返回带说话人标签的文本
        # 格式: [spk0]: 说话内容 [spk1]: 说话内容
        if 'segments' in asr_result:
            # 带说话人分离的分段结果
            text_parts = []
            for seg in asr_result.get('segments', []):
                speaker = seg.get('speaker', 'spk0')
                content = seg.get('text', '')
                if content:
                    text_parts.append(f"[{speaker}]: {content}")
            if text_parts:
                return ' '.join(text_parts)

        # 降级到纯文本
        return asr_result.get('full_text', '')
    
    def transcribe_audio_data(self, audio_data) -> str:
        """
        转写音频数据（保存为临时文件）
        
        Args:
            audio_data: numpy 音频数组
            
        Returns:
            识别后的文本
        """
        import tempfile
        import wave
        import os
        
        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        # 写入 WAV
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data.astype('int16').tobytes())
        
        try:
            return self.transcribe(temp_path)
        finally:
            os.unlink(temp_path)
