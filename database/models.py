from datetime import date, datetime
from typing import Optional

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

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

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

    user: Mapped["Users"] = relationship(back_populates="feature_usages")


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    sources: Mapped[list["Source"]] = relationship(
        back_populates="term",
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
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"),
        nullable=False,
        index=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    page: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))

    source: Mapped["Source"] = relationship(back_populates="definitions")
    topic: Mapped["Topic"] = relationship(back_populates="definitions")

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


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    topics: Mapped[list["Topic"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    topic_codes: Mapped[list["TopicCode"]] = relationship(
        back_populates="chapter"
    )


class TopicCode(Base):
    __tablename__ = "topic_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    chapter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chapters.id"), nullable=True)

    chapter: Mapped["Optional[Chapter]"] = relationship(
        back_populates="topic_codes",
    )
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="topic_codes",
        secondary="topic_mapping",
    )


class TopicMapping(Base):
    __tablename__ = "topic_mapping"

    topic_code_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("topic_codes.id"),
        primary_key=True,
    )
    topic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("topics.id"),
        primary_key=True,
    )


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("book_id", "name", name="uq_topics_book_id_name"),
        Index("ix_topics_book_id", "book_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)

    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"))

    topic_codes: Mapped[list["TopicCode"]] = relationship(
        back_populates="topics",
        secondary="topic_mapping",
    )

    book: Mapped["Book"] = relationship(
        back_populates="topics",
    )

    definitions: Mapped[list["Definition"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
    )