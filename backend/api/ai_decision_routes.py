from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import requests
import logging

from database.connection import get_db
from database.models import AIDecisionLog, AIDecisionQA, Account

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/decision/{decision_id}/qa")
async def get_decision_qa(decision_id: int, db: Session = Depends(get_db)):
    """Get all Q&A entries for a specific AI decision"""
    decision = db.query(AIDecisionLog).filter(AIDecisionLog.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    qa_entries = db.query(AIDecisionQA).filter(
        AIDecisionQA.decision_id == decision_id
    ).order_by(AIDecisionQA.created_at.desc()).all()

    return {
        "decision_id": decision_id,
        "qa_entries": [
            {
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "created_at": qa.created_at.isoformat() if qa.created_at else None
            }
            for qa in qa_entries
        ]
    }


@router.post("/account/{account_id}/ask")
async def ask_account_ai(
    account_id: int,
    payload: Dict,
    db: Session = Depends(get_db)
):
    """Ask a question to the AI with context of all its trading decisions"""
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get all decisions for this account (most recent first)
    decisions = db.query(AIDecisionLog).filter(
        AIDecisionLog.account_id == account_id
    ).order_by(AIDecisionLog.decision_time.desc()).limit(20).all()

    # Build context with all decisions
    decisions_context = ""
    for i, d in enumerate(reversed(decisions), 1):
        decisions_context += f"""
Decision #{i} - {d.decision_time}:
  Operation: {d.operation.upper()}
  Symbol: {d.symbol or 'N/A'}
  Previous Portion: {float(d.prev_portion):.2%}
  Target Portion: {float(d.target_portion):.2%}
  Total Balance: ${float(d.total_balance):,.2f}
  Reasoning: {d.reason}
  Executed: {'Yes' if d.executed == 'true' else 'No'}
"""

    context_prompt = f"""You are an AI trading assistant named "{account.name}". A user is asking you a question about your trading activity and decisions.

YOUR TRADING HISTORY (most recent {len(decisions)} decisions):
{decisions_context}

USER QUESTION:
{question}

Please provide a clear, helpful answer based on your trading history and knowledge. Be conversational and explain your reasoning."""

    try:
        # Call the AI API
        api_endpoint = account.base_url.rstrip('/') + '/chat/completions'
        verify_ssl = not api_endpoint.startswith('http://localhost') and not api_endpoint.startswith('http://127.0.0.1')

        response = requests.post(
            api_endpoint,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {account.api_key}'
            },
            json={
                'model': account.model,
                'messages': [
                    {'role': 'user', 'content': context_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 800
            },
            timeout=30,
            verify=verify_ssl
        )

        response.raise_for_status()
        ai_response = response.json()
        answer = ai_response['choices'][0]['message']['content'].strip()

        # Save Q&A entry (link to most recent decision)
        qa_entry = AIDecisionQA(
            decision_id=decisions[0].id if decisions else None,
            question=question,
            answer=answer
        )
        db.add(qa_entry)
        db.commit()
        db.refresh(qa_entry)

        logger.info(f"Created chat entry {qa_entry.id} for account {account_id}")

        return {
            "id": qa_entry.id,
            "question": question,
            "answer": answer,
            "created_at": qa_entry.created_at.isoformat() if qa_entry.created_at else None
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling AI API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in ask_account_ai: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/chat-history")
async def get_account_chat_history(account_id: int, db: Session = Depends(get_db)):
    """Get all chat history for an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get all QA entries for decisions of this account
    qa_entries = db.query(AIDecisionQA).join(
        AIDecisionLog, AIDecisionQA.decision_id == AIDecisionLog.id
    ).filter(
        AIDecisionLog.account_id == account_id
    ).order_by(AIDecisionQA.created_at.desc()).all()

    return {
        "account_id": account_id,
        "chat_history": [
            {
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "created_at": qa.created_at.isoformat() if qa.created_at else None
            }
            for qa in qa_entries
        ]
    }
