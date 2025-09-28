from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from passlib.context import CryptContext

DATABASE_URL = "sqlite:///./invoices.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    invoices = relationship("InvoiceDB", back_populates="user")

class InvoiceDB(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, nullable=True)
    vendor = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    category = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="invoices")

def hash_password(password):
    return pwd_context.hash(password)

def check_and_fix_database():
    """Check if database has the correct schema and recreate if needed"""
    session = SessionLocal()
    try:
        # Check if the new columns exist
        result = session.execute(text("PRAGMA table_info(invoices)"))
        columns = [col[1] for col in result.fetchall()]
        
        required_columns = ['id', 'invoice_number', 'vendor', 'date', 'amount', 'status', 'category', 'user_id']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"DEBUG: Missing columns in database: {missing_columns}")
            print("DEBUG: Recreating database with correct schema...")
            session.close()
            
            # Drop and recreate tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            
            # Re-seed the data
            init_mock_data()
            print("DEBUG: Database recreated successfully")
        else:
            print("DEBUG: Database schema is correct")
            
    except Exception as e:
        print(f"DEBUG: Error checking database schema: {e}")
        session.close()
        # Recreate database on error
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        init_mock_data()
        print("DEBUG: Database recreated due to error")

def init_mock_data():
    session = SessionLocal()
    print("DEBUG: Starting to seed mock data...")
    if session.query(User).count() == 0:
        print("DEBUG: No users found, creating users...")
        user1 = User(username="user1", password_hash=hash_password("password1"), name="Alice")
        user2 = User(username="user2", password_hash=hash_password("password2"), name="Bob")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)
        print("DEBUG: User1:", user1.username, user1.password_hash)
        print("DEBUG: User2:", user2.username, user2.password_hash)
        print("DEBUG: Users created successfully")
    else:
        print("DEBUG: Users already exist, skipping user creation")
    session.close()

def test_database():
    """Test function to verify database is working"""
    session = SessionLocal()
    try:
        user_count = session.query(User).count()
        invoice_count = session.query(InvoiceDB).count()
        print(f"DEBUG: Database test - Users: {user_count}, Invoices: {invoice_count}")
        
        if user_count > 0:
            users = session.query(User).all()
            for user in users:
                print(f"DEBUG: Found user: {user.username} (ID: {user.id})")
        
        return user_count > 0
    except Exception as e:
        print(f"DEBUG: Database test error: {e}")
        return False
    finally:
        session.close()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize mock data
print("DEBUG: About to initialize mock data...")
init_mock_data()
print("DEBUG: Mock data initialization complete")

# Test the database
test_database()

check_and_fix_database() 