"""
Domestic LLM Providers - 国内 LLM 提供商

支持：DeepSeek (免费额度)、智谱AI (免费额度)
"""

import os
import logging
from typing import Optional, Dict
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMBase(ABC):
    """LLM 基类"""
    
    @abstractmethod
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        pass
    
    @abstractmethod
    def get_name(self) -> str:


class DeepSeekLLM(LLMBase):
    """DeepSeek LLM - 免费额度"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com"
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.enabled = bool(self.api_key)
    
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        if not self.enabled:
            return None
        
        try:
            import requests
            
            url = f"{self.base_url}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"DeepSeek error: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return None
    
    def get_name(self) -> str:
        return "DeepSeek"


class ZhipuLLM(LLMBase):
    """智谱AI - 有免费额度"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY", "")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.model = os.environ.get("ZHIPU_MODEL", "glm-4")
        self.enabled = bool(self.api_key)
    
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        if not self.enabled:
            return None
        
        try:
            import requests
            
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Zhipu error: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Zhipu API error: {e}")
            return None
    
    def get_name(self) -> str:
        return "智谱AI"


class SiliconFlowLLM(LLMBase):
    """SiliconFlow - 便宜"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY", "")
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = os.environ.get("SILICONFLOW_MODEL", "Qwen/Qwen2-7B-Instruct")
        self.enabled = bool(self.api_key)
    
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        if not self.enabled:
            return None
        
        try:
            import requests
            
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"SiliconFlow error: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"SiliconFlow API error: {e}")
            return None
    
    def get_name(self) -> str:
        return "SiliconFlow"


class DomesticLLM:
    """国内 LLM 管理器"""
    
    def __init__(self):
        self.llms = []
        self._init_llms()
    
    def _init_llms(self):
        # 按优先级添加
        deepseek = DeepSeekLLM()
        if deepseek.enabled:
            self.llms.append(deepseek)
            logger.info("DeepSeek LLM enabled")
        
        zhipu = ZhipuLLM()
        if zhipu.enabled:
            self.llms.append(zhipu)
            logger.info("智谱AI LLM enabled")
        
        siliconflow = SiliconFlowLLM()
        if siliconflow.enabled:
            self.llms.append(siliconflow)
            logger.info("SiliconFlow LLM enabled")
    
    def chat(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        # 尝试每个可用的 LLM
        for llm in self.llms:
            try:
                result = llm.chat(prompt, system_prompt)
                if result:
                    logger.info(f"Using {llm.get_name()} for chat")
                    return result
            except Exception as e:
                logger.warning(f"{llm.get_name()} failed: {e}")
                continue
        
        return None
    
    def is_available(self) -> bool:
        return len(self.llms) > 0
    
    def get_provider_name(self) -> str:
        if self.llms:
            return self.llms[0].get_name()
        return "None"


def get_domestic_llm() -> DomesticLLM:
    """获取国内 LLM 实例"""
    return DomesticLLM()


if __name__ == "__main__":
    print("Testing Domestic LLM...")
    
    llm = get_domestic_llm()
    print(f"Available: {llm.is_available()}")
    print(f"Provider: {llm.get_provider_name()}")
    
    if llm.is_available():
        result = llm.chat("你好，请用一句话介绍自己")
        print(f"Response: {result}")
