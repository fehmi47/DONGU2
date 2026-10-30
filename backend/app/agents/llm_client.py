"""
DÖNGÜ AI Asistanı - LLM İstemcisi

OpenAI API istemcisini ve model konfigürasyonunu yönetir.
Ortam değişkenlerinden (OPENAI_API_KEY ve OPENAI_MODEL) değerleri okur.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# .env dosyasındaki ortam değişkenlerini otomatik yükle
load_dotenv()


class LLMConfigurationError(Exception):
    """OpenAI API anahtarı veya konfigürasyonu eksik olduğunda fırlatılır."""
    pass


class LLMAPIError(Exception):
    """OpenAI API çağrısı sırasında bir bağlantı veya servis hatası meydana geldiğinde fırlatılır."""
    pass


def get_model_name() -> str:
    """Kullanılacak model adını döndürür. Varsayılan: gpt-4o-mini"""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def get_openai_client() -> OpenAI:
    """
    OpenAI istemcisini başlatır ve döndürür.
    API anahtarı eksik veya geçersizse LLMConfigurationError fırlatır.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_openai"):
        raise LLMConfigurationError(
            "OPENAI_API_KEY ortam değişkeni ayarlanmamış veya varsayılan yer tutucu değerinde."
        )

    return OpenAI(api_key=api_key)
