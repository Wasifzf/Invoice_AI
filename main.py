from fastapi import FastAPI, Query, Depends, HTTPException, status, Body, UploadFile, File, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from database import SessionLocal, User, InvoiceDB
from models import Invoice as InvoiceModel
import os
from datetime import datetime, timedelta
from chatbot import answer_query
from typing import List, Dict
from pydantic import BaseModel
from ocr import extract_structured_data, Invoice as OCRInvoice
import tempfile
import shutil
import re
from sqlalchemy import text

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "dev-secret")

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def determine_category(vendor_name: str, customer_name: str = None) -> str:
    """Determine an appropriate category based on vendor name"""
    if not vendor_name:
        return "Other"
    
    vendor_lower = vendor_name.lower()
    
    # Define category mappings based on vendor names
    if any(word in vendor_lower for word in ["warehouse", "builders", "construction", "hardware"]):
        return "Hardware & Construction"
    elif any(word in vendor_lower for word in ["energy", "electric", "gas", "utility"]):
        return "Utilities"
    elif any(word in vendor_lower for word in ["security", "fire", "alarm"]):
        return "Security Services"
    elif any(word in vendor_lower for word in ["office", "supplies", "stationery"]):
        return "Office Supplies"
    elif any(word in vendor_lower for word in ["software", "tech", "computer", "it"]):
        return "Technology"
    elif any(word in vendor_lower for word in ["logistics", "shipping", "transport"]):
        return "Logistics"
    elif any(word in vendor_lower for word in ["consulting", "services", "professional"]):
        return "Professional Services"
    elif any(word in vendor_lower for word in ["cleaning", "maintenance"]):
        return "Maintenance"
    else:
        return "Other"

def parse_date(date_str):
    """Parse various date formats from OCR output"""
    if not date_str:
        return datetime.now().date()
    
    # Try different date formats
    date_formats = [
        "%Y-%m-%d",           # 2025-01-02
        "%d %B %Y",           # 02 January 2025
        "%d %b %Y",           # 02 Jan 2025
        "%B %d, %Y",          # January 02, 2025
        "%d/%m/%Y",           # 02/01/2025
        "%m/%d/%Y",           # 01/02/2025
        "%d-%m-%Y",           # 02-01-2025
        "%Y/%m/%d",           # 2025/01/02
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If no format matches, return today's date
    return datetime.now().date()

def verify_password(plain_password, hashed_password):
    """Verify password safely, handling invalid/unknown hash formats.

    Returns False instead of raising when stored hash is invalid or plaintext.
    """
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # Stored value isn't a recognized hash (possibly plaintext from old data)
        print("DEBUG: UnknownHashError during password verify - stored hash not recognized")
        # Optional: support migration if the stored value equals the provided password (plaintext)
        return hashed_password == plain_password
    except Exception as e:
        print(f"DEBUG: Error verifying password: {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(session, username: str):
    return session.query(User).filter(User.username == username).first()

def authenticate_user(session, username: str, password: str):
    print(f"DEBUG: Authenticating user: {username}")
    user = get_user(session, username)
    if not user:
        print(f"DEBUG: User {username} not found in database")
        return None
    print(f"DEBUG: User {username} found, verifying password...")
    
    # Try password verification first
    try:
        if pwd_context.verify(password, user.password_hash):
            print(f"DEBUG: Password verification successful for user {username}")
            return user
    except UnknownHashError:
        print(f"DEBUG: UnknownHashError for user {username} - attempting plaintext migration")
        # If stored value equals provided password (legacy plaintext), migrate now
        if user.password_hash == password and password:
            try:
                user.password_hash = get_password_hash(password)
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"DEBUG: Migrated plaintext password to hashed for user {username}")
                return user
            except Exception as e:
                print(f"DEBUG: Failed password migration for user {username}: {e}")
                return None
        else:
            print(f"DEBUG: Stored password not matching plaintext for user {username}")
            return None
    except Exception as e:
        print(f"DEBUG: Error during password verification for {username}: {e}")
        return None
    
    print(f"DEBUG: Password verification failed for user {username}")
    return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not isinstance(username, str):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    session = SessionLocal()
    user = get_user(session, username)
    session.close()
    if user is None:
        raise credentials_exception
    return user

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Invoice Chatbot API is running."}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"DEBUG: Login attempt for username: {form_data.username}")
    session = SessionLocal()
    user = authenticate_user(session, form_data.username, form_data.password)
    session.close()
    if not user:
        print(f"DEBUG: Login failed for username: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    print(f"DEBUG: Login successful for user: {user.username}")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

class ChatRequest(BaseModel):
    messages: list[dict]

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

@app.post("/chatbot/")
async def chatbot_query(
    chat: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    response = await answer_query(chat.messages, current_user)
    return {"response": response}

@app.post("/debug/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    admin_secret: str | None = Header(default=None, alias="X-Admin-Secret")
):
    """DEBUG ONLY: Reset a user's password by providing an admin secret header.

    Send JSON: {"username": "user1", "new_password": "password1"}
    With header: X-Admin-Secret: <ADMIN_SECRET>
    """
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == payload.username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.password_hash = get_password_hash(payload.new_password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"message": "Password reset", "username": user.username}
    finally:
        session.close()

@app.get("/invoices/")
def list_invoices(current_user: User = Depends(get_current_user)):
    session = SessionLocal()
    print(f"DEBUG: User {current_user.username} (ID: {current_user.id}) requesting invoices")
    
    # Check if user exists and has invoices
    user_invoices = session.query(InvoiceDB).filter(InvoiceDB.user_id == current_user.id).all()
    print(f"DEBUG: Found {len(user_invoices)} invoices for user {current_user.username}")
    
    for inv in user_invoices:
        print(f"DEBUG: Invoice {inv.id} - Vendor: {inv.vendor}, Amount: ${inv.amount}, Status: {inv.status}")
    
    result = [InvoiceModel(
        id=inv.id,
        invoice_number=inv.invoice_number,
        vendor=inv.vendor,
        date=inv.date,
        amount=inv.amount,
        status=inv.status,
        category=inv.category
    ) for inv in user_invoices]
    
    print(f"DEBUG: Returning {len(result)} invoices to frontend")
    session.close()
    return result

@app.post("/upload-invoice/")
async def upload_invoice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Extract data using OCR
        ocr_result = extract_structured_data(temp_path, OCRInvoice)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Convert OCR result to database format and save
        session = SessionLocal()
        
        # Parse the date using the flexible parser
        parsed_date = parse_date(ocr_result.date)
        
        # Create new invoice in database
        new_invoice = InvoiceDB(
            invoice_number=ocr_result.invoice_number,
            vendor=ocr_result.vendor_name or "Unknown Vendor",
            date=parsed_date,
            amount=ocr_result.total_gross_worth or 0.0,
            status="Unpaid",  # Default status for new invoices
            category=ocr_result.category or determine_category(ocr_result.vendor_name, ocr_result.customer_name), # Use OCR category or fallback to vendor-based category
            user_id=current_user.id
        )
        
        print(f"DEBUG: Creating invoice - Vendor: {new_invoice.vendor}, Amount: {new_invoice.amount}, User ID: {new_invoice.user_id}")
        
        session.add(new_invoice)
        session.commit()
        session.refresh(new_invoice)
        
        print(f"DEBUG: Invoice saved with ID: {new_invoice.id}")
        
        session.close()
        
        return {
            "message": "Invoice uploaded and processed successfully",
            "invoice_id": new_invoice.id,
            "extracted_data": {
                "invoice_number": ocr_result.invoice_number,
                "vendor": ocr_result.vendor_name,
                "customer": ocr_result.customer_name,
                "date": ocr_result.date,
                "total": ocr_result.total_gross_worth,
                "items_count": len(ocr_result.items) if ocr_result.items else 0
            }
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing invoice: {str(e)}"
        ) 

@app.get("/debug/db-schema")
def debug_db_schema():
    """Debug endpoint to check database schema"""
    session = SessionLocal()
    try:
        # Get table info
        result = session.execute(text("PRAGMA table_info(invoices)"))
        columns = result.fetchall()
        print("DEBUG: Database schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Count total invoices
        total_invoices = session.query(InvoiceDB).count()
        print(f"DEBUG: Total invoices in database: {total_invoices}")
        
        return {
            "schema": [{"name": col[1], "type": col[2]} for col in columns],
            "total_invoices": total_invoices
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close() 

@app.get("/debug/users")
def debug_users():
    """Debug endpoint to check what users exist in the database"""
    session = SessionLocal()
    try:
        users = session.query(User).all()
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "password_hash": user.password_hash[:20] + "..." if user.password_hash else None
            })
        return {"users": user_list, "count": len(users)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close() 