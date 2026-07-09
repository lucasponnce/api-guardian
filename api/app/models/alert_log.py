from sqlalchemy import Column, Integer, DateTime, ForeignKey
from app.db.database import Base

class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True)
    request_logs_id = Column(Integer, ForeignKey("request_logs.id"), unique=True, nullable=False)
    alerts_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)    