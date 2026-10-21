import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
secret_key = os.getenv("GOOGLE_API_KEY")
LLM_prvide = os.getenv("LLM_PROVIDER")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

respuesta = llm.invoke(
    "Traduce a PySpark: data a; set b; where x > 5; run;"
)

print(respuesta.content)
