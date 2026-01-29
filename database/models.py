from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enums.features import Feature
from enums.grades import UserGrade
from enums.roles import UserRole


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(64), index=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
    )
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    grade: Mapped[UserGrade] = mapped_column(
        Enum(UserGrade, native_enum=False),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False,
    )
    is_alive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # back_populates ссылается на атрибут 'user' в классе Activity
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # back_populates ссылается на атрибут 'user' в классе FeatureUsage
    feature_usages: Mapped[list["FeatureUsage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Activity(Base):
    __tablename__ = "activity"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="idx_activity_user_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
    )
    activity_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    actions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # back_populates ссылается на атрибут 'activities' в классе Users
    user: Mapped["Users"] = relationship(back_populates="activities")


class FeatureUsage(Base):
    __tablename__ = "feature_usage"
    __table_args__ = (
        Index("ix_feature_usage_lookup", "user_id", "feature_name", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id"),
        nullable=False,
    )
    feature_name: Mapped[Feature] = mapped_column(
        Enum(Feature, native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
    )

    # ВНИМАНИЕ: back_populates должен быть "feature_usages", как названо поле в классе Users
    user: Mapped["Users"] = relationship(back_populates="feature_usages")


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    sources: Mapped[list["Source"]] = relationship(
        back_populates="term",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    term: Mapped["Term"] = relationship(back_populates="sources")
    definitions: Mapped[list["Definition"]] = relationship(
        back_populates="source",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class Definition(Base):
    __tablename__ = "definitions"
    __table_args__ = (
        Index(
            "ix_definitions_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(255))
    page: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))

    source: Mapped["Source"] = relationship(back_populates="definitions")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )
    definition_id: Mapped[int] = mapped_column(
        ForeignKey("definitions.id"),
        nullable=False,
        index=True,
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
    )

    user: Mapped["Users"] = relationship()
    definition: Mapped["Definition"] = relationship()
