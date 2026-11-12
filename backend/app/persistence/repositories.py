"""MongoDB persistence layer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from pymongo import ReturnDocument

from app.config import settings
from app.domain.models import (
    AuditDefinition,
    AuditRun,
    CheckResult,
    CrawlPage,
    DeliveryAttempt,
    IssueIdentity,
    IssueObservation,
    PageCoverage,
    PageSnapshot,
    RulePassage,
    RunStatus,
    Schedule,
)


def _collection_name(base_name: str) -> str:
    """Get collection name with optional prefix."""
    prefix = settings.MONGODB_COLLECTION_PREFIX
    return f"{prefix}{base_name}" if prefix else base_name


class AuditDefinitionRepository:
    """Repository for AuditDefinition."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("audit_definitions")]

    async def create(self, definition: AuditDefinition) -> AuditDefinition:
        """Create audit definition."""
        doc = definition.model_dump()
        doc["targets"] = [
            {**target, "url": str(target["url"])} for target in doc["targets"]
        ]
        await self.collection.insert_one(doc)
        return definition

    async def get(self, id: str) -> AuditDefinition | None:
        """Get audit definition by ID."""
        doc = await self.collection.find_one({"id": id})
        if doc:
            return AuditDefinition(**doc)
        return None


class AuditRunRepository:
    """Repository for AuditRun."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("audit_runs")]

    async def create(self, run: AuditRun) -> AuditRun:
        """Create audit run."""
        doc = run.model_dump()
        await self.collection.insert_one(doc)
        return run

    async def get(self, id: str) -> AuditRun | None:
        """Get audit run by ID."""
        doc = await self.collection.find_one({"id": id})
        if doc:
            return AuditRun(**doc)
        return None

    async def list_by_definition(self, audit_definition_id: str) -> list[AuditRun]:
        """List runs for an audit definition, newest first."""
        cursor = self.collection.find(
            {"audit_definition_id": audit_definition_id}
        ).sort("completed_at", -1)
        return [AuditRun(**doc) async for doc in cursor]

    async def find_baseline(
        self,
        comparison_key: str,
        exclude_id: str,
        started_before: datetime,
    ) -> AuditRun | None:
        """Newest audited run with the same key that finished before the given run started."""
        doc = await self.collection.find_one(
            {
                "comparison_key": comparison_key,
                "id": {"$ne": exclude_id},
                "status": {"$in": [RunStatus.COMPLETED.value, RunStatus.PARTIAL.value]},
                "completed_pages": {"$gt": 0},
                "completed_at": {"$lt": started_before},
            },
            sort=[("completed_at", -1)],
        )
        return AuditRun(**doc) if doc else None

    async def update_status(
        self,
        id: str,
        status: str,
        completed_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_pages: int | None = None,
        failed_pages: int | None = None,
        warnings: list[str] | None = None,
        coverage: PageCoverage | None = None,
        coverage_pages: list[CrawlPage] | None = None,
        active_page_progress: float | None = None,
        page_statuses: list[str] | None = None,
    ) -> None:
        """Update run status and progress fields."""
        update: dict[str, object] = {"status": status}
        if completed_at is not None:
            update["completed_at"] = completed_at
        if started_at is not None:
            update["started_at"] = started_at
        if completed_pages is not None:
            update["completed_pages"] = completed_pages
        if failed_pages is not None:
            update["failed_pages"] = failed_pages
        if warnings is not None:
            update["warnings"] = warnings
        if coverage is not None:
            update["coverage"] = coverage.model_dump()
        if coverage_pages is not None:
            update["coverage_pages"] = [page.model_dump() for page in coverage_pages]
        if active_page_progress is not None:
            update["active_page_progress"] = active_page_progress
        if page_statuses is not None:
            update["page_statuses"] = page_statuses
        await self.collection.update_one({"id": id}, {"$set": update})

    async def heartbeat(self, id: str) -> None:
        """Record that a live worker still owns this run."""
        await self.collection.update_one(
            {"id": id}, {"$set": {"heartbeat_at": datetime.now(UTC)}}
        )

    async def fail_stale(self, stale_after_seconds: int) -> int:
        """Fail queued or running runs whose worker stopped heartbeating."""
        stale_before = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
        result = await self.collection.update_many(
            {
                "status": {"$in": [RunStatus.QUEUED.value, RunStatus.RUNNING.value]},
                "$or": [
                    {"heartbeat_at": None},
                    {"heartbeat_at": {"$lt": stale_before}},
                ],
            },
            {
                "$set": {"status": RunStatus.FAILED.value},
                "$push": {"warnings": "run_interrupted"},
            },
        )
        return result.modified_count


class PageSnapshotRepository:
    """Repository for PageSnapshot."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("page_snapshots")]

    async def create(self, snapshot: PageSnapshot) -> PageSnapshot:
        """Create page snapshot."""
        doc = snapshot.model_dump()
        await self.collection.insert_one(doc)
        return snapshot

    async def get(self, snapshot_id: str) -> PageSnapshot | None:
        """Get one snapshot."""
        doc = await self.collection.find_one({"id": snapshot_id})
        return PageSnapshot(**doc) if doc else None

    async def get_by_run(self, run_id: str) -> list[PageSnapshot]:
        """Get all snapshots for a run."""
        cursor = self.collection.find({"run_id": run_id})
        return [PageSnapshot(**doc) async for doc in cursor]


class PageCaptureRepository:
    """MongoDB GridFS repository for rendered HTML captures."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        self.bucket = AsyncIOMotorGridFSBucket(
            db,
            bucket_name=_collection_name("page_captures"),
            chunk_size_bytes=8 * 1024 * 1024,
        )

    async def create(self, html: str, metadata: dict[str, object]) -> str:
        """Store one HTML capture and return its GridFS ID."""
        file_id = ObjectId()
        upload = self.bucket.open_upload_stream_with_id(
            file_id,
            "capture.html",
            metadata=metadata,
        )
        await upload.write(html.encode("utf-8"))
        await upload.close()
        return str(file_id)

    async def get(self, capture_id: str) -> bytes:
        """Read one capture by GridFS ID."""
        download = await self.bucket.open_download_stream(ObjectId(capture_id))
        return await download.read()


class RulePassageRepository:
    """Repository for RulePassage."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("rule_passages")]
        self.catalog = db[_collection_name("rule_catalog")]

    async def replace_version(self, version: str, passages: list[RulePassage]) -> int:
        """Replace the stored passages for one rule version, so restarts do not duplicate."""
        await self.collection.delete_many({"version": version})
        if not passages:
            return 0
        result = await self.collection.insert_many([p.model_dump() for p in passages])
        await self.catalog.replace_one(
            {"_id": "current"},
            {"_id": "current", "version": version, "ingested_at": datetime.now(UTC)},
            upsert=True,
        )
        return len(result.inserted_ids)

    async def list(self, version: str | None = None) -> list[RulePassage]:
        """List rule passages, optionally restricted to one version."""
        query = {"version": version} if version else {}
        cursor = self.collection.find(query).sort("source_range.0", 1)
        return [RulePassage(**doc) async for doc in cursor]

    async def get_by_version(self, version: str) -> list[RulePassage]:
        """Get all passages for a version."""
        return await self.list(version)

    async def get_latest_version(self) -> str | None:
        """Get the rule version of the most recently ingested guide."""
        doc = await self.catalog.find_one({"_id": "current"})
        return doc["version"] if doc else None


class CheckResultRepository:
    """Repository for CheckResult."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("check_results")]

    async def create(self, result: CheckResult) -> CheckResult:
        """Create check result."""
        doc = result.model_dump()
        await self.collection.insert_one(doc)
        return result

    async def get_by_run(self, run_id: str) -> list[CheckResult]:
        """Get all results for a run."""
        cursor = self.collection.find({"run_id": run_id})
        return [CheckResult(**doc) async for doc in cursor]


class IssueIdentityRepository:
    """Repository for IssueIdentity."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("issue_identities")]

    async def create(self, identity: IssueIdentity) -> IssueIdentity:
        """Create issue identity."""
        doc = identity.model_dump()
        await self.collection.insert_one(doc)
        return identity

    async def get_or_create(self, identity: IssueIdentity) -> IssueIdentity:
        """Get existing or create new identity."""
        existing = await self.collection.find_one({"id": identity.id})
        if existing:
            return IssueIdentity(**existing)
        return await self.create(identity)

    async def get_many(self, ids: list[str]) -> dict[str, IssueIdentity]:
        """Get identities by id."""
        cursor = self.collection.find({"id": {"$in": ids}})
        return {doc["id"]: IssueIdentity(**doc) async for doc in cursor}


class IssueObservationRepository:
    """Repository for IssueObservation."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("issue_observations")]

    async def create(self, observation: IssueObservation) -> IssueObservation:
        """Create issue observation."""
        doc = observation.model_dump()
        await self.collection.insert_one(doc)
        return observation

    async def get_by_run(self, run_id: str) -> list[IssueObservation]:
        """Get all observations for a run."""
        cursor = self.collection.find({"run_id": run_id})
        return [IssueObservation(**doc) async for doc in cursor]


class ScheduleRepository:
    """Repository for recurring audit schedules."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("schedules")]

    async def create(self, schedule: Schedule) -> Schedule:
        """Create a schedule."""
        await self.collection.insert_one(schedule.model_dump())
        return schedule

    async def get(self, schedule_id: str) -> Schedule | None:
        """Get one schedule."""
        doc = await self.collection.find_one({"id": schedule_id})
        return Schedule(**doc) if doc else None

    async def list(self) -> list[Schedule]:
        """List schedules ordered by next run."""
        cursor = self.collection.find({}).sort("next_run_at_utc", 1)
        return [Schedule(**doc) async for doc in cursor]

    async def update(self, schedule: Schedule) -> Schedule:
        """Replace one schedule."""
        await self.collection.replace_one({"id": schedule.id}, schedule.model_dump())
        return schedule

    async def delete(self, schedule_id: str) -> None:
        """Delete one schedule."""
        await self.collection.delete_one({"id": schedule_id})

    async def claim_due_schedule(
        self,
        now_utc: datetime,
        lease_until_utc: datetime,
    ) -> Schedule | None:
        """Atomically claim one due schedule."""
        doc = await self.collection.find_one_and_update(
            {
                "enabled": True,
                "next_run_at_utc": {"$lte": now_utc},
                "$or": [
                    {"lease_until_utc": None},
                    {"lease_until_utc": {"$exists": False}},
                    {"lease_until_utc": {"$lt": now_utc}},
                ],
            },
            {"$set": {"lease_until_utc": lease_until_utc}},
            sort=[("next_run_at_utc", 1)],
            return_document=ReturnDocument.AFTER,
        )
        return Schedule(**doc) if doc else None


class DeliveryAttemptRepository:
    """Repository for SMTP delivery attempts."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]):
        self.collection = db[_collection_name("delivery_attempts")]

    async def create(self, attempt: DeliveryAttempt) -> DeliveryAttempt:
        """Create a delivery attempt."""
        await self.collection.insert_one(attempt.model_dump())
        return attempt

    async def update(self, attempt: DeliveryAttempt) -> DeliveryAttempt:
        """Replace a delivery attempt."""
        await self.collection.replace_one({"id": attempt.id}, attempt.model_dump())
        return attempt

    async def get(self, attempt_id: str) -> DeliveryAttempt | None:
        """Get one delivery attempt."""
        doc = await self.collection.find_one({"id": attempt_id})
        return DeliveryAttempt(**doc) if doc else None

    async def list_by_schedule(self, schedule_id: str) -> list[DeliveryAttempt]:
        """List delivery attempts for one schedule."""
        cursor = self.collection.find({"schedule_id": schedule_id}).sort(
            "attempted_at", -1
        )
        return [DeliveryAttempt(**doc) async for doc in cursor]
