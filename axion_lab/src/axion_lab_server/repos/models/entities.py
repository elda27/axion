"""SQLAlchemy entity models"""

from datetime import datetime

from axion_lab_server.repos.models.base import Base
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Org(Base):
    """Organization entity"""

    __tablename__ = "orgs"

    org_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="org", cascade="all, delete-orphan"
    )


class Project(Base):
    """Project entity"""

    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    org_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("orgs.org_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    org: Mapped["Org"] = relationship("Org", back_populates="projects")
    batches: Mapped[list["Batch"]] = relationship(
        "Batch", back_populates="project", cascade="all, delete-orphan"
    )
    aggregations: Mapped[list["Aggregation"]] = relationship(
        "Aggregation", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_projects_org_created", "org_id", "created_at"),)


class Batch(Base):
    """Batch entity (experiment condition grouping)"""

    __tablename__ = "batches"

    batch_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="batches")
    runs: Mapped[list["Run"]] = relationship(
        "Run", back_populates="batch", cascade="all, delete-orphan"
    )
    dp_jobs: Mapped[list["DPJob"]] = relationship(
        "DPJob", back_populates="batch", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_batches_project_created", "project_id", "created_at"),)


class Run(Base):
    """Run entity (single experiment execution)"""

    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("batches.batch_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, garbage, archived
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="runs")
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="run", cascade="all, delete-orphan"
    )
    run_metrics: Mapped[list["RunMetric"]] = relationship(
        "RunMetric", back_populates="run", cascade="all, delete-orphan"
    )
    comparison_indicators: Mapped[list["ComparisonIndicator"]] = relationship(
        "ComparisonIndicator", back_populates="run", cascade="all, delete-orphan"
    )
    pins: Mapped[list["RunPin"]] = relationship(
        "RunPin", back_populates="run", cascade="all, delete-orphan"
    )
    aggregation_members: Mapped[list["AggregationMember"]] = relationship(
        "AggregationMember", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_runs_batch_created", "batch_id", "created_at"),
        Index("ix_runs_batch_status_created", "batch_id", "status", "created_at"),
    )


class RunPin(Base):
    """Run pin entity (champion / user_selected)"""

    __tablename__ = "run_pins"

    pin_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("runs.run_id"), nullable=False
    )
    batch_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("batches.batch_id"), nullable=False
    )
    pin_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # champion, user_selected
    pinned_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pinned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="pins")
    batch: Mapped["Batch"] = relationship("Batch")

    __table_args__ = (
        Index("ix_run_pins_batch_type", "batch_id", "pin_type", "pinned_at"),
        # Ensure only one champion per batch
        UniqueConstraint(
            "batch_id",
            "pin_type",
            name="uq_batch_champion",
            sqlite_on_conflict="REPLACE",
        ),
    )


class Artifact(Base):
    """Artifact entity (references or inline values)"""

    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("runs.run_id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # url, local, inline_text, inline_number, inline_json
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # langfuse_trace, object_storage, note, evaluation, etc.
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # for url, local, text, json
    payload_number: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # for inline_number
    meta_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="artifacts")

    __table_args__ = (
        Index("ix_artifacts_run_created", "run_id", "created_at"),
        Index("ix_artifacts_type_created", "type", "created_at"),
    )


class RunMetric(Base):
    """Run Metric entity (run quality indicators)"""

    __tablename__ = "run_metrics"

    qm_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("runs.run_id"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # raw, derived, manual
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="run_metrics")

    __table_args__ = (
        Index("ix_run_metrics_run_computed", "run_id", "computed_at"),
        UniqueConstraint("run_id", "key", "version", name="uq_rm_run_key_version"),
    )


class ComparisonIndicator(Base):
    """Comparison Indicator entity (run comparison indicators)"""

    __tablename__ = "comparison_indicators"

    ci_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("runs.run_id"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_ref: Mapped[str | None] = mapped_column(String(26), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="comparison_indicators")

    __table_args__ = (
        Index("ix_comparison_indicators_run_computed", "run_id", "computed_at"),
        UniqueConstraint("run_id", "key", "version", name="uq_ci_run_key_version"),
    )


class Aggregation(Base):
    """Aggregation entity (cross-batch metadata-based grouping).

    While a Batch groups Runs by experiment condition, an Aggregation groups
    Runs across batches (or within a batch) based on metadata keys.
    Typical use-cases:
    - ML epoch × method Loss/metric comparison
    - LLM model × agent implementation version comparison
    """

    __tablename__ = "aggregations"

    aggregation_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_by_keys_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON list of metadata keys, e.g. ["epoch", "model_name"]
    filter_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )  # JSON filter spec, e.g. {"model_name": ["gpt-4o", "claude-3"]}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="aggregations")
    members: Mapped[list["AggregationMember"]] = relationship(
        "AggregationMember",
        back_populates="aggregation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_aggregations_project_created", "project_id", "created_at"),
    )


class AggregationMember(Base):
    """Links a Run to an Aggregation with associated metadata values."""

    __tablename__ = "aggregation_members"

    member_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    aggregation_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("aggregations.aggregation_id"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("runs.run_id"), nullable=False
    )
    metadata_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )  # e.g. {"epoch": 5, "model_name": "gpt-4o"}
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    aggregation: Mapped["Aggregation"] = relationship(
        "Aggregation", back_populates="members"
    )
    run: Mapped["Run"] = relationship("Run", back_populates="aggregation_members")

    __table_args__ = (
        Index("ix_agg_members_agg_added", "aggregation_id", "added_at"),
        Index("ix_agg_members_run", "run_id"),
        UniqueConstraint("aggregation_id", "run_id", name="uq_aggregation_run"),
    )


class DPJob(Base):
    """DP Job entity (computation job tracking)"""

    __tablename__ = "dp_jobs"

    job_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("batches.batch_id"), nullable=False
    )
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # active_only, include_garbage
    recompute: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0 or 1
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued"
    )  # queued, running, succeeded, failed, canceled
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="dp_jobs")

    __table_args__ = (
        Index("ix_dp_jobs_batch_created", "batch_id", "created_at"),
        Index("ix_dp_jobs_status_created", "status", "created_at"),
    )
