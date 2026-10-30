"""
DÖNGÜ AI Asistanı - Temel Agent Döngüsü

Tek agent, OpenAI Chat Completions API ve araç çağırma (tool-calling) döngüsü.
Kullanıcının sorusunu analiz eder, gerektiğinde salt-okunur araçları çalıştırır
ve elde edilen verilere dayanarak samimi, güvenilir bir yanıt üretir.
"""

import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import openai

# Araç modüllerini yükleyerek registry'ye kaydedilmesini sağla
import app.agents.tools  # noqa: F401
from app.agents.registry import tool_schemas, execute_tool
from app.agents.llm_client import get_openai_client, get_model_name, LLMConfigurationError, LLMAPIError

logger = logging.getLogger(__name__)

# Maksimum döngü iterasyon sayısı (sonsuz döngüyü önlemek için)
MAX_ITERATIONS = 5

SYSTEM_PROMPT = (
    "Sen DÖNGÜ asistanısın. Kısa, samimi Türkçe cevap ver. "
    "Sadece araçlardan gelen verilere dayan; veri yoksa bunu açıkça söyle, tahmin yürütme. "
    "Tahmini değerlerden bahsederken mutlaka 'tahmini' kelimesini kullan. "
    "Tarihi geçmiş ürünler için kendi güvenlik yorumunu yapma; yalnızca araçtan gelen 'uyari' metnini aktar. "
    "Kullanıcının bahsettiği malzeme mutfağında yoksa bunu açıkça söyle. "
    "'Bugün' sorularında yalnızca aciliyeti yüksek ürünleri öner (tarihine 3 gün veya daha az kalanlar ve tarihi geçmiş TETT ürünleri). "
    "Konu DÖNGÜ dışındaysa (mutfak, tarif, tüketim, geri dönüşüm dışı) kibarca bunu belirt."
)


def run_agent(user_message: str, db: Session, user_id: int) -> Dict[str, Any]:
    """
    Kullanıcı mesajını alır, OpenAI Chat Completions API ile araç çağırma döngüsünü yürütür
    ve nihai yanıtı kullanılan araçların listesiyle birlikte döndürür.

    Args:
        user_message: Kullanıcının girdiği metin
        db: Aktif SQLAlchemy veritabanı oturumu
        user_id: Doğrulanmış kullanıcının ID'si

    Returns:
        dict: {"answer": str, "tools": List[str]}
    """
    try:
        client = get_openai_client()
        model = get_model_name()
    except LLMConfigurationError:
        raise
    except Exception as e:
        raise LLMAPIError(f"LLM istemcisi başlatılamadı: {e}") from e

    schemas = tool_schemas()
    tools_used: List[str] = []

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for iteration in range(MAX_ITERATIONS):
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
            }
            if schemas:
                kwargs["tools"] = schemas
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
        except (openai.APIError, openai.APIConnectionError, openai.RateLimitError) as e:
            logger.error(f"OpenAI API çağrı hatası: {e}")
            raise LLMAPIError(f"OpenAI API iletişim hatası: {e}") from e
        except Exception as e:
            logger.error(f"Beklenmeyen LLM hatası: {e}")
            raise LLMAPIError(f"LLM işlenirken bir hata oluştu: {e}") from e

        choice = response.choices[0]
        response_message = choice.message

        # Eğer asistan bir araç çağırmak istiyorsa
        if response_message.tool_calls:
            # Asistanın mesajını geçmişe ekle
            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in response_message.tool_calls
                ],
            }
            messages.append(assistant_msg)

            # İstenen her bir aracı güvenli bir şekilde çalıştır
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

                # Argümanları ayrıştır
                try:
                    tool_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    tool_args = {}

                # Aracı çağır ve sonucunu al
                try:
                    tool_result = execute_tool(
                        name=tool_name,
                        db=db,
                        user_id=user_id,
                        arguments=tool_args,
                    )
                    tool_result_str = json.dumps(tool_result, ensure_ascii=False)
                except Exception as err:
                    logger.exception(f"Araç çalıştırma hatası ({tool_name}): {err}")
                    tool_result_str = json.dumps({"error": "Bu bilgiye şu an ulaşılamadı."}, ensure_ascii=False)

                # Araç çıktısını mesaj geçmişine ekle
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_str,
                })

            # Döngünün bir sonraki adımında model araç çıktılarını değerlendirecek
            continue

        # Model artık nihai bir metin yanıtı üretmiş durumda
        final_answer = response_message.content or ""
        return {
            "answer": final_answer,
            "tools": tools_used,
        }

    # 5 iterasyon tamamlandığında hala nihai cevap gelmediyse
    return {
        "answer": "Üzgünüm, sorunuzu işlerken adım sınırına (maksimum 5 adım) ulaşıldı. Lütfen sorunuzu daha spesifik şekilde tekrar iletin.",
        "tools": tools_used,
    }
