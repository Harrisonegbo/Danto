"""
XAUUSD AI Research Platform - FastAPI backend
Educational / research use only. Not financial advice.
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime

from app.database import engine, Base, get_db
from app.models_db import User, BacktestResult, SignalLog
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

app = FastAPI(
    title="XAUUSD AI Research Platform",
    description="Educational paper-trading research tool. Not financial advice.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------- Auth ----------
@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register")
async def register(username: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(username=username, hashed_password=get_password_hash(password))
    db.add(user)
    await db.commit()
    return {"msg": "User created successfully"}


# ---------- Protected API ----------
@app.get("/api/me")
async def read_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}


class BacktestIn(BaseModel):
    stats: dict
    trades: list
    notes: Optional[str] = None


@app.post("/api/backtest/save")
async def save_backtest(
    payload: BacktestIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = BacktestResult(
        user_id=current_user.id,
        stats_json=json.dumps(payload.stats),
        trades_json=json.dumps(payload.trades),
        notes=payload.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"id": record.id, "created_at": record.created_at}


@app.get("/api/backtests")
async def list_backtests(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BacktestResult)
        .where(BacktestResult.user_id == current_user.id)
        .order_by(BacktestResult.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "stats": json.loads(r.stats_json),
            "notes": r.notes,
        }
        for r in rows
    ]


@app.post("/api/signal/log")
async def log_signal(
    signal: int,
    confidence: float,
    price: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = SignalLog(
        signal=signal, confidence=confidence, price=price, user_id=current_user.id
    )
    db.add(record)
    await db.commit()
    return {"status": "logged"}


# ---------- WebSocket for real-time paper signals ----------
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send a welcome / heartbeat message
        await websocket.send_json(
            {
                "type": "connected",
                "msg": "Paper-trading signal stream ready",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        while True:
            # Keep connection alive; clients can send ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Helper to push a paper signal (can be called from training scripts)
async def push_paper_signal(signal: int, confidence: float, price: float):
    await manager.broadcast(
        {
            "type": "signal",
            "signal": signal,
            "confidence": confidence,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ---------- Static frontend ----------
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    return FileResponse("app/static/index.html")
