import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.database.mongodb import db
from backend.app.models.message import Message
from backend.app.models.session import SimulationSession
from backend.app.services.persona_engine import persona_engine
from backend.app.services.scenario_engine import scenario_engine
from backend.app.services.memory_engine import memory_engine
from backend.app.services.attacker_engine import attacker_engine
from backend.app.services.honeypot_client import honeypot_client
from backend.app.services.response_adapter import HoneypotResponseError, HoneypotAPIError
from backend.app.utils.logger import logger

class ConversationManager:
    """
    Phase 2 Advanced Conversation Manager.
    Orchestrates stateful, multi-turn autonomous simulations with persistent
    fictional scenario facts, active strategy decisions, and compact rolling memory.
    """

    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.stop_flags: Dict[str, bool] = {}
        self.attacker_engine = attacker_engine

    async def create_session(
        self,
        scenario: str = "fictional_bank_verification",
        persona_id: str = "friendly_support",
        channel: str = "SMS",
        language: str = "English",
        locale: str = "IN",
        max_turns: int = 15,
        initial_message: Optional[str] = None,
        session_id: Optional[str] = None,
        scenario_id: Optional[str] = None
    ) -> SimulationSession:
        """
        Creates and stores a new simulation session with established scenario facts.
        """
        if scenario_id:
            scenario = scenario_id
        session_id = session_id or f"sim_{uuid.uuid4().hex[:8]}"
        persona = persona_engine.get_persona(persona_id)
        
        # Generate scenario facts ONCE at session creation
        established_facts = scenario_engine.generate_session_facts(scenario, persona.name)
        initial_memory = memory_engine.initialize_memory(scenario, persona_id, established_facts)

        metadata = {
            "channel": channel,
            "language": language,
            "locale": locale
        }
        if initial_message:
            metadata["customInitialMessage"] = initial_message

        session = SimulationSession(
            sessionId=session_id,
            status="created",
            personaId=persona_id,
            scenario=scenario,
            language=language,
            conversationHistory=[],
            totalMessages=0,
            maxTurns=max_turns or settings.MAX_CONVERSATION_TURNS,
            metadata=metadata,
            establishedFacts=established_facts,
            conversationMemory=initial_memory,
            currentStrategy={"selectedStrategy": "trust_building", "conversationState": "initiating", "reason": "Session created"},
            consistencyStatus={"isValid": True, "issues": []}
        )

        collection = db.get_collection("sessions")
        await collection.insert_one(session.model_dump())
        logger.info(f"[ConversationManager] Created Phase 2 simulation session: {session_id} (Persona: {persona.name}, Scenario: {scenario})")
        return session

    async def get_session(self, session_id: str) -> Optional[SimulationSession]:
        """Retrieves a session from DB by sessionId."""
        collection = db.get_collection("sessions")
        doc = await collection.find_one({"sessionId": session_id})
        if not doc:
            return None
        return SimulationSession(**doc)

    async def list_sessions(self, status: Optional[str] = None, limit: int = 50) -> List[SimulationSession]:
        """Retrieves sessions list, sorted by createdAt descending."""
        collection = db.get_collection("sessions")
        filter_dict = {"status": status} if status else {}
        cursor = collection.find(filter_dict).sort("createdAt", -1)
        docs = await cursor.to_list(limit)
        return [SimulationSession(**d) for d in docs]

    async def get_session_stats(self) -> Dict[str, int]:
        """Calculates aggregated metrics across all sessions."""
        collection = db.get_collection("sessions")
        all_docs = await collection.find().to_list(1000)
        
        total = len(all_docs)
        running = sum(1 for d in all_docs if d.get("status") == "running")
        completed = sum(1 for d in all_docs if d.get("status") == "completed")
        failed = sum(1 for d in all_docs if d.get("status") == "failed")
        stopped = sum(1 for d in all_docs if d.get("status") == "stopped")
        total_messages = sum(d.get("totalMessages", 0) for d in all_docs)

        return {
            "totalSimulations": total,
            "runningSimulations": running,
            "completedSimulations": completed,
            "failedSimulations": failed,
            "stoppedSimulations": stopped,
            "totalMessages": total_messages
        }

    async def start_session(self, session_id: str) -> SimulationSession:
        """Starts autonomous execution of a simulation in the background."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        # If already actively executing in background, do not duplicate
        if session.status == "running" and session_id in self.active_tasks and not self.active_tasks[session_id].done():
            logger.info(f"Session {session_id} is already actively running.")
            return session

        session.status = "running"
        session.errorMessage = None
        session.update_timestamp()
        await self._persist_session(session)

        self.stop_flags[session_id] = False

        # Launch background task for conversational loop
        task = asyncio.create_task(self._run_conversation_loop(session_id))
        self.active_tasks[session_id] = task

        logger.info(f"Started simulation session task: {session_id}")
        return session

    async def stop_session(self, session_id: str) -> SimulationSession:
        """Gracefully stops a running simulation session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        self.stop_flags[session_id] = True
        session.status = "stopped"
        session.update_timestamp()
        await self._persist_session(session)

        # Cancel background task if running
        task = self.active_tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()

        logger.info(f"Stopped simulation session: {session_id}")
        return session

    async def resume_session(self, session_id: str) -> SimulationSession:
        """Resumes a stopped, completed, or failed simulation without resetting history or memory."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        completed_turns = len([m for m in session.conversationHistory if m.sender == "scammer"])
        if completed_turns >= session.maxTurns:
            # Dynamically extend max turns by 5 so conversation can keep going
            session.maxTurns = completed_turns + 5
            logger.info(f"[Resume] Extended maxTurns to {session.maxTurns} for session {session_id}")

        session.status = "running"
        session.errorMessage = None
        session.update_timestamp()
        await self._persist_session(session)

        self.stop_flags[session_id] = False
        old_task = self.active_tasks.pop(session_id, None)
        if old_task and not old_task.done():
            old_task.cancel()

        task = asyncio.create_task(self._run_conversation_loop(session_id))
        self.active_tasks[session_id] = task

        logger.info(f"Resuming simulation session: {session_id} with {len(session.conversationHistory)} existing messages")
        return session

    async def _persist_session(self, session: SimulationSession):
        """Saves current session state to MongoDB atomically."""
        collection = db.get_collection("sessions")
        await collection.update_one(
            {"sessionId": session.sessionId},
            {"$set": session.model_dump()}
        )

    async def _run_conversation_loop(self, session_id: str):
        """
        Main autonomous loop exchanging turns between Attacker Agent and Honeypot API.
        """
        logger.info(f"[Loop] Initiating simulation loop for {session_id}")
        try:
            while True:
                # Check cancellation flag
                if self.stop_flags.get(session_id, False):
                    logger.info(f"[Loop] Stop flag detected for {session_id}. Exiting loop.")
                    break

                session = await self.get_session(session_id)
                if not session or session.status != "running":
                    logger.info(f"[Loop] Session {session_id} status is no longer running ({getattr(session, 'status', None)}). Exiting.")
                    break

                # Count completed turns
                completed_turns = len([m for m in session.conversationHistory if m.sender == "scammer"])
                current_turn = completed_turns + 1
                remaining_turns = max(0, session.maxTurns - current_turn)

                if current_turn > session.maxTurns:
                    logger.info(f"[Loop] Reached max turns ({session.maxTurns}) for session {session_id}. Completing.")
                    session.status = "completed"
                    session.update_timestamp()
                    await self._persist_session(session)
                    break

                # Generate Attacker Agent message with stateful Phase 2 engines
                history_dicts = [m.to_honeypot_format() for m in session.conversationHistory]

                if not session.conversationHistory:
                    # Initial message
                    custom_init = session.metadata.get("customInitialMessage")
                    attacker_text, strat_dict, const_dict = await attacker_engine.generate_initial_turn(
                        scenario=session.scenario,
                        custom_prompt=custom_init,
                        persona_id=session.personaId,
                        language=session.language or "English",
                        established_facts=session.establishedFacts
                    )
                else:
                    # Subsequent turn
                    attacker_text, strat_dict, const_dict = await attacker_engine.generate_next_turn(
                        scenario=session.scenario,
                        conversation_history=history_dicts,
                        persona_id=session.personaId,
                        language=session.language or "English",
                        established_facts=session.establishedFacts,
                        memory=session.conversationMemory,
                        remaining_turns=remaining_turns
                    )

                session.currentStrategy = strat_dict
                session.consistencyStatus = const_dict

                attacker_msg = Message(
                    sender="scammer",
                    text=attacker_text,
                    timestamp=int(time.time() * 1000),
                    turnNumber=current_turn
                )

                # Send message to Honeypot API (history contains PREVIOUS messages only)
                logger.info(f"[Loop] Turn {current_turn}/{session.maxTurns}: Submitting scammer message to Honeypot")

                try:
                    honeypot_reply = await honeypot_client.send_message(
                        session_id=session.sessionId,
                        message_text=attacker_text,
                        conversation_history=history_dicts,
                        metadata=session.metadata,
                        timestamp=attacker_msg.timestamp
                    )
                except (HoneypotAPIError, HoneypotResponseError, Exception) as err:
                    err_str = str(err)
                    logger.error(f"[Loop] Honeypot call failed on turn {current_turn}: {err_str}")
                    
                    # Record the attempt and mark session as failed
                    session.conversationHistory.append(attacker_msg)
                    session.totalMessages = len(session.conversationHistory)
                    session.status = "failed"
                    session.errorMessage = err_str
                    session.update_timestamp()
                    await self._persist_session(session)
                    break

                # Honeypot reply successfully extracted via ResponseAdapter
                honeypot_msg = Message(
                    sender="user",
                    text=honeypot_reply,
                    timestamp=int(time.time() * 1000),
                    turnNumber=current_turn
                )

                # Store both messages in chronological order
                session.conversationHistory.append(attacker_msg)
                session.conversationHistory.append(honeypot_msg)
                session.totalMessages = len(session.conversationHistory)

                # Update conversation memory
                updated_memory = memory_engine.update_memory_turn(
                    current_memory=session.conversationMemory,
                    attacker_message=attacker_text,
                    honeypot_message=honeypot_reply,
                    strategy=strat_dict.get("selectedStrategy", "contextual_adaptation"),
                    state=strat_dict.get("conversationState", "conversing"),
                    established_facts=session.establishedFacts
                )
                session.conversationMemory = updated_memory

                # Check turn limit
                if current_turn >= session.maxTurns:
                    session.status = "completed"
                    logger.info(f"[Loop] Completed all {session.maxTurns} turns for session {session_id}")
                else:
                    session.status = "running"

                session.update_timestamp()
                await self._persist_session(session)

                # Conversational pacing pause if still running
                if session.status == "running":
                    await asyncio.sleep(1.5)

        except asyncio.CancelledError:
            logger.info(f"[Loop] Conversation loop task cancelled for session {session_id}")
        except Exception as e:
            logger.exception(f"[Loop] Unexpected exception in loop for {session_id}: {e}")
            session = await self.get_session(session_id)
            if session:
                session.status = "failed"
                session.errorMessage = f"Internal loop error: {str(e)}"
                session.update_timestamp()
                await self._persist_session(session)
        finally:
            self.active_tasks.pop(session_id, None)
            self.stop_flags.pop(session_id, None)

conversation_manager = ConversationManager()
