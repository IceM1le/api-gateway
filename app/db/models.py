from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, UTC


class Base(DeclarativeBase):
    pass


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    client_key: Mapped[str] = mapped_column(String(255), index=True)
    endpoint: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(Integer)

    duration_ms: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )