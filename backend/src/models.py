from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # URL-safe slug
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    studies: Mapped[list["Study"]] = relationship("Study", back_populates="organization")
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # owner, admin, member
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(63), nullable=False, unique=True, index=True)
    participant_identity_flow: Mapped[str] = mapped_column(
        String(20), nullable=False, default="anonymous"
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="studies")
    interview_guide: Mapped["InterviewGuide | None"] = relationship(
        "InterviewGuide", back_populates="study", uselist=False
    )
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="study")


class InterviewGuide(Base):
    __tablename__ = "interview_guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("studies.id"), nullable=False, unique=True, index=True
    )
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    study: Mapped["Study"] = relationship("Study", back_populates="interview_guide")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("studies.id"), nullable=False, index=True
    )
    access_token: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    interviewee_firebase_uid: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending"
    )  # pending, completed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_participant_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    platform_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verity_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("verity_users.id"), nullable=True, index=True
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript_url: Mapped[str | None] = mapped_column(String, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(String, nullable=True)
    pipecat_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    study: Mapped["Study"] = relationship("Study", back_populates="interviews")
    verity_user: Mapped["VerityUser | None"] = relationship(
        "VerityUser", back_populates="interviews"
    )
    audio_recording: Mapped["AudioRecording | None"] = relationship(
        "AudioRecording", back_populates="interview", uselist=False
    )
    transcript: Mapped["Transcript | None"] = relationship(
        "Transcript", back_populates="interview", uselist=False
    )


class AudioRecording(Base):
    __tablename__ = "audio_recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interviews.id"), nullable=False, unique=True, index=True
    )
    uri: Mapped[str] = mapped_column(String, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    sample_rate_hz: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    interview: Mapped["Interview"] = relationship("Interview", back_populates="audio_recording")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interviews.id"), nullable=False, unique=True, index=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    interview: Mapped["Interview"] = relationship("Interview", back_populates="transcript")
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan"
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transcript_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripts.id"), nullable=False, index=True
    )
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="segments")


class VerityUser(Base):
    __tablename__ = "verity_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_sign_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="verity_user")
    profile: Mapped["ParticipantProfile | None"] = relationship(
        "ParticipantProfile", back_populates="verity_user", uselist=False
    )


class ParticipantProfile(Base):
    __tablename__ = "participant_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    verity_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("verity_users.id"), unique=True, nullable=False, index=True
    )
    platform_identities: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    verity_user: Mapped["VerityUser"] = relationship("VerityUser", back_populates="profile")
