from dotenv import load_dotenv
load_dotenv()
import os
import httpx
from database import SessionLocal, InvoiceDB
from sqlalchemy import func
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
print("GROQ_API_KEY:", GROQ_API_KEY)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are an expert assistant for an invoice and expense processing system.\n"
    "- If the user’s question is ambiguous, politely ask for clarification.\n"
    "- Never mix general definitions with specific data unless the user’s question clearly requests both.\n"
    "\n"
    "Examples:\n"
    "User: How many invoices do I have?\n"
    "Assistant: [Use the provided data to answer, e.g., 'You have 3 invoices in the system.']\n"
    "\n"
    "User: What is the total amount due?\n"
    "Assistant: [Sum the amounts of all unpaid invoices from the provided data.]\n"
    "- When the user asks for a list or details of invoices, ALWAYS respond ONLY with a Markdown table, with columns: ID, Invoice #, Vendor, Date, Amount, Status, Category.\n"
    "- Do NOT add any text before or after the table unless the user specifically asks for it.\n"
    "- The Amount column should always be formatted as currency (e.g., $1200.50).\n"
    "- If there are no invoices, return a table with only the header row and a single row saying 'No invoices found'.\n"
    "- For all other questions, answer normally.\n"
    "\n"
    "Example:\n"
    "| ID | Invoice # | Vendor    | Date       | Amount    | Status  | Category      |\n"
    "|----|-----------|-----------|------------|-----------|---------|---------------|\n"
    "| 1  | INV-001   | Acme Corp | 2024-05-01 | $1200.50  | Unpaid  | Office Supplies |\n"
    "| 2  | INV-002   | Gamma Inc | 2024-03-20 | $450.75   | Unpaid  | Software      |\n"
)

async def answer_query(messages, current_user) -> str:
    session = SessionLocal()
    invoices = session.query(InvoiceDB).filter(InvoiceDB.user_id == current_user.id).all()
    invoice_data = [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor": inv.vendor,
            "date": str(inv.date),
            "amount": inv.amount,
            "status": inv.status,
            "category": inv.category
        }
        for inv in invoices
    ]
    session.close()

    # Prepend system prompt and user context
    system_message = {"role": "system", "content": SYSTEM_PROMPT + f"\nUser name: {current_user.name}\nInvoice data: {invoice_data}"}
    groq_messages = [system_message] + messages

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # Updated to current Groq model name
        "messages": groq_messages,
        "max_tokens": 800,
        "temperature": 0.2,
        "stream": False
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = f": {error_data.get('error', {}).get('message', str(error_data))}"
            except:
                error_detail = f": {e.response.text}"
            return f"Error contacting Groq API: {e.response.status_code} {e.response.reason_phrase}{error_detail}"
        except Exception as e:
            return f"Error contacting Groq API: {e}" 