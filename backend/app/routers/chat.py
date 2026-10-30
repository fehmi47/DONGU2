"""
DÖNGÜ AI Asistanı - Sohbet Router'ı

Kullanıcıların AI asistanı ile doğal dilde iletişim kurmasını sağlayan
POST /api/chat uç noktasını tanımlar.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.agent import run_agent
from app.agents.llm_client import LLMConfigurationError, LLMAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["AI Asistanı"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="AI Asistanı ile Sohbet",
    description=(
        "Kullanıcının doğal dildeki sorularını alır, arka planda mutfak stoklarını "
        "ve önceliklerini inceleyerek bağlama uygun yanıt üretir."
    ),
    responses={
        503: {
            "description": "LLM servisine ulaşılamıyor veya API yapılandırması eksik.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Asistan şu an ulaşılamıyor, birazdan tekrar dene."
                    }
                }
            },
        }
    },
)
def chat_with_assistant(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Oturum açmış kullanıcının sorusunu DÖNGÜ agent döngüsüne aktarır.
    """
    try:
        result = run_agent(
            user_message=request.message,
            db=db,
            user_id=current_user.id,
            history=request.history,
        )
        return ChatResponse(
            answer=result["answer"],
            tools=result["tools"],
        )
    except (LLMConfigurationError, LLMAPIError) as e:
        logger.error(f"AI Asistanı çalıştırılırken hata: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asistan şu an ulaşılamıyor, birazdan tekrar dene.",
        )
    except Exception as e:
        logger.exception(f"Beklenmeyen asistan hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Asistan yanıt üretirken beklenmeyen bir hata oluştu.",
        )
