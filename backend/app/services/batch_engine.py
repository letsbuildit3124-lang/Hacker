import asyncio
import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.database.mongodb import db
from backend.app.services.conversation_manager import conversation_manager
from backend.app.services.evaluation_engine import evaluation_engine
from backend.app.utils.logger import logger

class BatchConfig(BaseModel):
    batchName: str
    scenarioIds: List[str]
    personaIds: List[str]
    languages: List[str] = Field(default_factory=lambda: ["English"])
    maxTurns: int = 10
    concurrency: int = 3

class BatchSessionSummary(BaseModel):
    sessionId: str
    scenarioId: str
    personaId: str
    language: str
    status: str
    turnsCompleted: int = 0
    score: Optional[float] = None
    errorMessage: Optional[str] = None

class BatchRecord(BaseModel):
    batchId: str
    batchName: str
    status: str = "created"  # created, running, completed, cancelled, failed
    totalSessions: int
    runningSessions: int = 0
    completedSessions: int = 0
    failedSessions: int = 0
    concurrency: int = 3
    maxTurns: int = 10
    sessionSummaries: List[BatchSessionSummary] = Field(default_factory=list)
    averageScore: Optional[float] = None
    createdAt: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    updatedAt: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

class BatchEngine:
    """
    Multi-Agent Batch Simulation Engine.
    Executes multiple independent attacker-versus-honeypot simulations in parallel
    using bounded asynchronous semaphores. Tracks batch state in MongoDB.
    """

    def __init__(self):
        self.active_batch_tasks: Dict[str, asyncio.Task] = {}
        self.cancel_flags: Dict[str, bool] = {}

    async def create_and_start_batch(self, config: BatchConfig) -> BatchRecord:
        """
        Creates all permutations of scenarios, personas, and languages,
        initializes the batch record, and starts the background execution runner.
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        summaries: List[BatchSessionSummary] = []

        # Create all combinations
        for sc in config.scenarioIds:
            for p in config.personaIds:
                for lang in config.languages:
                    # Create independent session with its own memory & facts
                    session = await conversation_manager.create_session(
                        scenario=sc,
                        persona_id=p,
                        language=lang,
                        max_turns=config.maxTurns
                    )
                    summaries.append(BatchSessionSummary(
                        sessionId=session.sessionId,
                        scenarioId=sc,
                        personaId=p,
                        language=lang,
                        status="created"
                    ))

        batch = BatchRecord(
            batchId=batch_id,
            batchName=config.batchName,
            status="running",
            totalSessions=len(summaries),
            concurrency=config.concurrency,
            maxTurns=config.maxTurns,
            sessionSummaries=summaries
        )

        coll = db.get_collection("batches")
        await coll.insert_one(batch.model_dump())

        # Start runner
        self.cancel_flags[batch_id] = False
        task = asyncio.create_task(self._run_batch(batch_id, config.concurrency))
        self.active_batch_tasks[batch_id] = task

        logger.info(f"[BatchEngine] Started batch {batch_id} with {len(summaries)} sessions at concurrency {config.concurrency}")
        return batch

    async def get_batch(self, batch_id: str) -> Optional[BatchRecord]:
        """Retrieves batch record by ID from MongoDB."""
        coll = db.get_collection("batches")
        doc = await coll.find_one({"batchId": batch_id})
        if not doc:
            return None
        return BatchRecord(**doc)

    async def list_batches(self, limit: int = 50) -> List[BatchRecord]:
        """Lists recent batches."""
        coll = db.get_collection("batches")
        cursor = coll.find().sort("createdAt", -1)
        docs = await cursor.to_list(limit)
        return [BatchRecord(**d) for d in docs]

    async def cancel_batch(self, batch_id: str) -> BatchRecord:
        """Cancels a running batch."""
        self.cancel_flags[batch_id] = True
        batch = await self.get_batch(batch_id)
        if batch:
            batch.status = "cancelled"
            batch.updatedAt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            coll = db.get_collection("batches")
            await coll.update_one({"batchId": batch_id}, {"$set": batch.model_dump()})

        task = self.active_batch_tasks.pop(batch_id, None)
        if task and not task.done():
            task.cancel()

        logger.info(f"[BatchEngine] Cancelled batch {batch_id}")
        return batch

    async def _run_batch(self, batch_id: str, concurrency: int):
        """Worker loop executing batch sessions with a bounded semaphore."""
        sem = asyncio.Semaphore(max(1, min(10, concurrency)))
        batch = await self.get_batch(batch_id)
        if not batch:
            return

        async def worker(item: BatchSessionSummary):
            if self.cancel_flags.get(batch_id, False):
                return

            async with sem:
                if self.cancel_flags.get(batch_id, False):
                    return

                try:
                    logger.info(f"[BatchEngine] Launching session {item.sessionId} in batch {batch_id}")
                    # Start autonomous simulation
                    await conversation_manager.start_session(item.sessionId)

                    # Poll until session reaches terminal state
                    while True:
                        if self.cancel_flags.get(batch_id, False):
                            await conversation_manager.stop_session(item.sessionId)
                            break
                        s = await conversation_manager.get_session(item.sessionId)
                        if s.status in ("completed", "failed", "stopped"):
                            item.status = s.status
                            item.turnsCompleted = len([m for m in s.conversationHistory if m.sender == "scammer"])
                            item.errorMessage = s.errorMessage
                            # Run automated evaluation upon completion
                            try:
                                eval_result = await evaluation_engine.evaluate_session(s.model_dump())
                                item.score = eval_result.overallScore
                            except Exception as ev_err:
                                logger.warning(f"[BatchEngine] Evaluation failed for {item.sessionId}: {ev_err}")
                            break
                        await asyncio.sleep(1.0)
                except Exception as e:
                    logger.error(f"[BatchEngine] Error executing session {item.sessionId}: {e}")
                    item.status = "failed"
                    item.errorMessage = str(e)
                finally:
                    # Persist incremental progress
                    await self._update_batch_progress(batch_id)

        tasks = [worker(item) for item in batch.sessionSummaries]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Mark batch final status
        final_batch = await self.get_batch(batch_id)
        if final_batch and final_batch.status == "running":
            final_batch.status = "completed"
            final_batch.updatedAt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
            # Compute average score
            scored_sessions = [s.score for s in final_batch.sessionSummaries if s.score is not None]
            if scored_sessions:
                final_batch.averageScore = round(sum(scored_sessions) / len(scored_sessions), 1)

            coll = db.get_collection("batches")
            await coll.update_one({"batchId": batch_id}, {"$set": final_batch.model_dump()})
            logger.info(f"[BatchEngine] Batch {batch_id} completed. Average Score: {final_batch.averageScore}")

    async def _update_batch_progress(self, batch_id: str):
        """Updates live counters and progress for a batch."""
        coll = db.get_collection("batches")
        doc = await coll.find_one({"batchId": batch_id})
        if not doc:
            return
        batch = BatchRecord(**doc)
        
        running_c = 0
        completed_c = 0
        failed_c = 0
        for s in batch.sessionSummaries:
            if s.status == "running":
                running_c += 1
            elif s.status == "completed":
                completed_c += 1
            elif s.status in ("failed", "stopped"):
                failed_c += 1

        batch.runningSessions = running_c
        batch.completedSessions = completed_c
        batch.failedSessions = failed_c
        batch.updatedAt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        await coll.update_one({"batchId": batch_id}, {"$set": batch.model_dump()})

batch_engine = BatchEngine()
