import os
import time

from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """Regresa el LLM según LLM_PROVIDER en el .env."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL")

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model or "gemini-2.5-flash",
            temperature=0,
            max_retries=3,      # reintenta solo si hay 429 (límite gratis)
        )

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or "llama-3.3-70b-versatile",
            temperature=0,
            max_retries=3,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model or "qwen2.5-coder:7b", temperature=0)

    raise ValueError(f"LLM_PROVIDER no soportado: {provider}")


def _is_rate_limit(e):
    texto = f"{type(e).__name__} {e}".lower()
    return any(s in texto for s in ("ratelimit", "429", "resourceexhausted", "quota"))


def invoke_llm(messages, retries=4, wait=5):
    """Llama al LLM con reintentos. Si es límite de cuota, espera más."""
    llm = get_llm()
    for intento in range(1, retries + 1):
        try:
            return llm.invoke(messages).content
        except Exception as e:
            if intento == retries:
                raise
            espera = 60 if _is_rate_limit(e) else wait * intento   # el límite es por minuto
            print(f"   ⚠️  {type(e).__name__} (intento {intento}/{retries}), esperando {espera}s...")
            time.sleep(espera)