"""
DÖNGÜ AI Asistanı - Araç Kayıt Defteri (Tool Registry)

Bu modül, agent tarafından kullanılabilecek araçları merkezi bir kayıt defterinde (TOOLS) toplar.
Yeni bir araç eklemek için yalnızca ilgili fonksiyonun üzerine `@register` decorator'ı eklemek yeterlidir.
Agent döngüsüne müdahale edilmesine gerek kalmaz.

Güvenlik Kuralı:
- user_id ve db parametreleri ASLA tool JSON şemalarında gösterilmez (LLM'e sızdırılmaz).
- Bu parametreler backend tarafından çalışma anında (runtime) güvenli biçimde enjekte edilir.
"""

from typing import Callable, Dict, Any, List, Optional
import functools

# Merkezi araç kayıt defteri
TOOLS: Dict[str, Dict[str, Any]] = {}


def register(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Any]] = None,
):
    """
    Fonksiyonları DÖNGÜ agent araç kayıt defterine kaydeden decorator.

    Args:
        name: Aracın benzersiz adı (örn: 'get_priority_products')
        description: Aracın ne yaptığını LLM'e açıklayan detaylı metin
        parameters: LLM'in sağlayacağı argümanları tanımlayan JSON Schema dict.
                   Eğer argüman gerektirmiyorsa None veya boş parametre nesnesi verilebilir.
    """
    if parameters is None:
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }

    # Güvenlik doğrulaması: user_id veya db parametrelerinin şemaya eklenmesini engelle
    props = parameters.get("properties", {})
    if "user_id" in props or "db" in props:
        raise ValueError(f"Güvenlik hatası: '{name}' aracının parametre şeması 'user_id' veya 'db' içeremez!")

    def decorator(func: Callable):
        TOOLS[name] = {
            "func": func,
            "description": description,
            "parameters": parameters,
        }

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def tool_schemas() -> List[Dict[str, Any]]:
    """
    OpenAI Chat Completions API uyumlu function calling / tools listesini döndürür.
    """
    try:
        import app.agents.tools  # noqa: F401
    except ImportError:
        pass

    schemas = []
    for name, item in TOOLS.items():
        schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": item["description"],
                "parameters": item["parameters"],
            },
        })
    return schemas


def execute_tool(name: str, db: Any, user_id: int, arguments: Dict[str, Any]) -> Any:
    """
    Kayıtlı bir aracı güvenli bir şekilde çalıştırır.
    db ve user_id backend tarafından otomatik olarak enjekte edilir.
    """
    if name not in TOOLS:
        raise KeyError(f"Tanımsız araç çağrısı: '{name}'")

    func = TOOLS[name]["func"]
    # db ve user_id backend tarafından güvenli şekilde enjekte edilir
    return func(db=db, user_id=user_id, **arguments)
