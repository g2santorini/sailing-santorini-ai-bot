import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Δεν βρέθηκε το OPENAI_API_KEY.")

client = OpenAI(api_key=api_key)

with open("company_knowledge.md", "r", encoding="utf-8") as f:
    knowledge = f.read()

customer_question = input("Write the customer question: ")

prompt = f"""
You are a professional sales assistant for a luxury Santorini sailing company.

Use the following company knowledge to answer:

{knowledge}

Customer question:
{customer_question}
"""

response = client.responses.create(
    model="gpt-5.4-mini",
    input=prompt
)

print("\nAI reply:\n")
print(response.output_text)