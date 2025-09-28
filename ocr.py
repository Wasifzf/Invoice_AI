import os
from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Type, Optional

# Load environment variables from .env file
load_dotenv()

# For local development, set your API key directly or use environment variable
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY is not set. Add it to your environment or .env file.")

# Create a client
client = genai.Client(api_key=api_key)

# Define the model you are going to use (allow override via env and provide safer defaults)
# Many projects may not have access to specific pinned versions like -002. Using -latest is safer.
model_id = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash-lite")

def extract_structured_data(file_path: str, model_schema: Type[BaseModel]):
    """Extract structured data from invoice files using Gemini AI"""

    # Check file extension
    ext = os.path.splitext(file_path)[1].lower()

    # Determine display text in prompt based on file type
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        file_type_desc = "invoice image"
    elif ext == ".pdf":
        file_type_desc = "invoice PDF file"
    else:
        raise ValueError("Unsupported file format. Use JPG, PNG, or PDF.")

    print(f"Uploading {file_type_desc}...")
    # Upload file to Gemini
    uploaded_file = client.files.upload(file=file_path, config={'display_name': os.path.basename(file_path)})

    # Use the exact model name that should work - try gemini-1.5-flash-001 specifically
    chosen_model = "gemini-2.5-flash-lite"
    
    # Get token count for monitoring
    file_size = client.models.count_tokens(model=chosen_model, contents=uploaded_file)
    print(f"Using model '{chosen_model}'. File: {uploaded_file.display_name} equals to {file_size.total_tokens} tokens")

    print("Processing with Gemini AI...")
    # Prompt Gemini to extract structured data
    prompt = f"Extract the structured data from the following {file_type_desc}. Pay special attention to account numbers, invoice numbers, dates, and itemized details. Determine the appropriate category for the invoice based on the vendor name and invoice content. Choose from: Hardware & Construction, Utilities, Security Services, Office Supplies, Technology, Logistics, Professional Services, Maintenance, or Other."

    response = client.models.generate_content(
        model=chosen_model,
        contents=[prompt, uploaded_file],
        config={
            'response_mime_type': 'application/json',
            'response_schema': model_schema
        }
    )

    print("Parsing response...")
    # Debug: Print raw response
    print("Raw response:", response.text)

    # Manually parse the response and validate it against the Pydantic model
    try:
        data = response.text
        parsed_data = model_schema.parse_raw(data)
        return parsed_data
    except Exception as e:
        print(f"Error parsing response: {e}")
        raise

class Item(BaseModel):
    description: str = Field(description="The description of the item")
    quantity: float = Field(description="The quantity of the item")
    unit_price: Optional[float] = Field(description="The unit price of the item", default=None)
    gross_worth: Optional[float] = Field(description="The gross worth/total price of the item", default=None)

class Invoice(BaseModel):
    """Extract comprehensive invoice data including account information"""
    invoice_number: Optional[str] = Field(description="The invoice number e.g. 1234567890", default=None)
    account_number: Optional[str] = Field(description="The customer account number or account ID", default=None)
    date: Optional[str] = Field(description="The date of the invoice e.g. 2024-01-01", default=None)
    due_date: Optional[str] = Field(description="The due date of the invoice", default=None)
    vendor_name: Optional[str] = Field(description="The vendor/company name", default=None)
    customer_name: Optional[str] = Field(description="The customer/client name", default=None)
    items: Optional[list[Item]] = Field(description="The list of items with description, quantity and gross worth", default_factory=list)
    subtotal: Optional[float] = Field(description="The subtotal before taxes", default=None)
    tax_amount: Optional[float] = Field(description="The tax amount", default=None)
    total_gross_worth: Optional[float] = Field(description="The total gross worth of the invoice", default=None)
    category: Optional[str] = Field(description="The category of the invoice based on vendor name and invoice content. Choose from: Hardware & Construction, Utilities, Security Services, Office Supplies, Technology, Logistics, Professional Services, Maintenance, or Other", default=None)