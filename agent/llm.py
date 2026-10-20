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

def invoke_llm(messages, retries=3, wait=5):
    """Llama al LLM con reintentos ante errores de red."""
    llm = get_llm()
    for intento in range(1, retries + 1):
        try:
            return llm.invoke(messages).content
        except Exception as e:
            print(f"   ⚠️  Error del LLM (intento {intento}/{retries}): {type(e).__name__}")
            if intento == retries:
                raise
            time.sleep(wait * intento)   # espera 5s, 10s, 15s..