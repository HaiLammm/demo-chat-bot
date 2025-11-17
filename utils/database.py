# utils/database.py (PostgreSQL - SQLAlchemy)

from sqlalchemy import create_engine, Column, BigInteger, JSON, DateTime, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import config # Cần import file cấu hình của bạn

# --- CẤU HÌNH KẾT NỐI LINH HOẠT ---
DB_USER = config.DB_USER
# Sử dụng getattr để tránh lỗi nếu DB_PASSWORD không tồn tại trong config
DB_PASSWORD = getattr(config, 'DB_PASSWORD', None) 
DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_NAME = config.DB_NAME

# Xây dựng chuỗi kết nối: Bỏ qua :password nếu DB_PASSWORD là None
auth_part = f"{DB_USER}:{DB_PASSWORD}" if DB_PASSWORD else DB_USER
DATABASE_URL = f"postgresql://{auth_part}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Khởi tạo Engine và Session
Engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# --- ĐỊNH NGHĨA MODEL CƠ SỞ DỮ LIỆU ---

class ChatHistory(Base):
    """Lưu trữ lịch sử trò chuyện (thay thế cho bảng SQLite cũ)."""
    __tablename__ = "chat_history"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class CVSession(Base):
    """Lưu trữ dữ liệu CV đã parse cho phiên làm việc hiện tại."""
    __tablename__ = "cv_sessions"

    user_id = Column(BigInteger, primary_key=True, index=True)
    cv_data_json = Column(JSON, nullable=False)
    job_title = Column(String, nullable=True) 
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- CÁC HÀM TƯƠNG TÁC DB ---

def init_db():
    """Tạo các bảng ChatHistory và CVSession nếu chúng chưa tồn tại."""
    try:
        # Nếu bot được khởi động lại, chỉ tạo các bảng nếu chưa có
        Base.metadata.create_all(bind=Engine)
        print("✅ PostgreSQL tables initialized successfully (chat_history, cv_sessions).")
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo PostgreSQL DB. Kiểm tra service và cấu hình: {e}")

# ----------------- HÀM QUẢN LÝ CHAT HISTORY -----------------

def save_chat(user_id: int, query: str, response: str):
    """Lưu lịch sử trò chuyện vào PostgreSQL."""
    db = SessionLocal()
    try:
        new_entry = ChatHistory(
            user_id=user_id,
            query=query,
            response=response
        )
        db.add(new_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Lỗi khi lưu Chat History cho User {user_id}: {e}")
    finally:
        db.close()

# ----------------- HÀM QUẢN LÝ CV SESSION -----------------

def save_cv_data(user_id: int, cv_data: dict, job_title: str):
    """Lưu hoặc cập nhật dữ liệu CV đã parse vào cơ sở dữ liệu."""
    db = SessionLocal()
    try:
        session_entry = db.query(CVSession).filter(CVSession.user_id == user_id).first()

        if session_entry:
            session_entry.cv_data_json = cv_data
            session_entry.job_title = job_title
        else:
            session_entry = CVSession(
                user_id=user_id,
                cv_data_json=cv_data,
                job_title=job_title
            )
            db.add(session_entry)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Lỗi khi lưu dữ liệu CV cho User {user_id}: {e}")
    finally:
        db.close()

def get_cv_data(user_id: int) -> dict or None:
    """Truy xuất dữ liệu CV đã parse từ cơ sở dữ liệu."""
    db = SessionLocal()
    try:
        session_entry = db.query(CVSession).filter(CVSession.user_id == user_id).first()
        if session_entry:
            # SQLAlchemy/PostgreSQL tự động deserialize JSONB thành dict
            return session_entry.cv_data_json
        return None
    except Exception as e:
        print(f"Lỗi khi truy xuất dữ liệu CV cho User {user_id}: {e}")
        return None
    finally:
        db.close()
