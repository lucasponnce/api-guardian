from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import INET
from app.db.database import Base

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True)
    users_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(INET, nullable=False)
    method = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    query_params = Column(String)
    request_payload = Column(Text)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())