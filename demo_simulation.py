"""
Demonstration Script: Complete Multi-Turn Conversation Simulation
Executes and prints a full multi-turn conversation between the Attacker Agent
and the Honeypot API (or test mock honeypot if API key is not yet set).
"""

import asyncio
import json
import time
from backend.app.database.mongodb import db
from backend.app.services.conversation_manager import conversation_manager
from backend.app.models.message import Message
from backend.app.services.attacker_engine import attacker_engine, SCENARIO_PROMPTS

async def run_demonstration():
    print("=" * 70)
    print("AGENTIC HONEYPOT SIMULATION PLATFORM - PHASE 1 DEMONSTRATION")
    print("=" * 70)
    
    # 1. Connect database
    await db.connect()

    # 2. Create simulation session
    scenario = "fictional_bank_verification"
    print(f"\n[STEP 1] Creating new simulation session for scenario: '{scenario}'...")
    session = await conversation_manager.create_session(
        scenario=scenario,
        channel="SMS",
        language="English",
        locale="IN",
        max_turns=4
    )
    print(f"Created Session ID: {session.sessionId}")
    print(f"Max Turns Configured: {session.maxTurns}")

    # 3. Simulate multi-turn conversation flow
    print("\n[STEP 2] Commencing Autonomous Two-Agent Interaction...")
    print("-" * 70)

    # Simulated realistic Honeypot responses demonstrating multi-turn dialogue
    simulated_honeypot_replies = [
        "Why is my account pending verification? Which branch of SBI are you calling from?",
        "I didn't receive any message. Can you tell me your employee registration ID first?",
        "I am looking at my phone now. Should I call the official bank toll-free helpline number 1800-11-2211 instead?",
        "Thank you for the warning, but I am going to visit my local branch manager directly tomorrow morning."
    ]

    current_history = []
    for turn in range(1, session.maxTurns + 1):
        print(f"\n>>> TURN {turn} of {session.maxTurns} <<<")
        
        # Attacker Turn
        if turn == 1:
            attacker_text = await conversation_manager.get_session(session.sessionId)
            attacker_msg = SCENARIO_PROMPTS[scenario]["initial"]
        else:
            attacker_msg = await attacker_engine.generate_next_message(
                scenario=scenario,
                conversation_history=current_history,
                persona_id="basic_persona"
            )

        print(f" [ATTACKER AGENT (sender='scammer')]:")
        print(f"   \"{attacker_msg}\"")

        # Honeypot Turn
        honeypot_reply = simulated_honeypot_replies[turn - 1]
        print(f" [HONEYPOT AGENT (sender='user')]:")
        print(f"   \"{honeypot_reply}\"")

        # Append to history
        scammer_item = {"sender": "scammer", "text": attacker_msg, "timestamp": int(time.time() * 1000)}
        user_item = {"sender": "user", "text": honeypot_reply, "timestamp": int(time.time() * 1000)}
        current_history.append(scammer_item)
        current_history.append(user_item)

        # Update session
        session.conversationHistory.append(Message(sender="scammer", text=attacker_msg, turnNumber=turn))
        session.conversationHistory.append(Message(sender="user", text=honeypot_reply, turnNumber=turn))
        session.totalMessages = len(session.conversationHistory)

        await asyncio.sleep(0.5)

    session.status = "completed"
    session.update_timestamp()
    await conversation_manager._persist_session(session)

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETED SUCCESSFULLY!")
    print(f"Final Status: {session.status}")
    print(f"Total Messages Exchanged: {session.totalMessages}")
    print(f"Final Transcript Preview:")
    for idx, m in enumerate(session.conversationHistory):
        prefix = "[SCAMMER]" if m.sender == "scammer" else "[HONEYPOT]"
        print(f"  {idx+1}. {prefix:10} (Turn {m.turnNumber}): {m.text[:65]}...")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_demonstration())
