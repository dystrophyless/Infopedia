from datetime import datetime, date

from sqlalchemy import text, Integer, BigInteger, String, Date, DateTime, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("TIMEZONE('utc', now())"))
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    is_alive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean, nullable=False)

    activities: Mapped[list["Activity"]] = relationship(back_populates="user")


class Activity(Base):
    __tablename__ = "activity"
    __table_args__ = (UniqueConstraint("user_id", "activity_date", name="idx_activity_user_day"), )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("TIMEZONE('utc', now())"))
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    actions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user: Mapped[Users] = relationship(back_populates="activities")