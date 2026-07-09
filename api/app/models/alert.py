from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import INET
from app.db.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    ip_address = Column(INET, nullable=False)
    alert_type = Column(String, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    pattern_started_at = Column(DateTime(timezone=True), nullable=False)
    pattern_ended_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, server_default="open")
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())