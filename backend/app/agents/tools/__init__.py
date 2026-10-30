"""
DÖNGÜ AI Asistanı - Araçlar Paketi

Tüm araç modüllerini içe aktararak merkezi registry'ye kaydedilmelerini sağlar.
"""

from app.agents.tools import kitchen
from app.agents.tools import recipes
from app.agents.tools import stats
from app.agents.tools import recycling

__all__ = ["kitchen", "recipes", "stats", "recycling"]
