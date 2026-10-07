from fastapi import FastAPI
from pydantic import BaseModel, Field
app=FastAPI(title="TradeAI Risk API")
class OrderRisk(BaseModel):
    equity: float=Field(gt=0)
    notional: float=Field(gt=0)
    daily_loss_pct: float=Field(ge=0)
    drawdown_pct: float=Field(ge=0)
    data_age_minutes: float=Field(ge=0)
    max_position_pct: float=0.15
    max_daily_loss_pct: float=0.03
    max_drawdown_pct: float=0.25
    max_data_age_minutes: float=5760
@app.post("/api/risk/check")
def risk_check(o:OrderRisk):
    reasons=[]
    if o.notional/o.equity>o.max_position_pct: reasons.append("position_limit")
    if o.daily_loss_pct>=o.max_daily_loss_pct: reasons.append("daily_loss_limit")
    if o.drawdown_pct>=o.max_drawdown_pct: reasons.append("drawdown_limit")
    if o.data_age_minutes>o.max_data_age_minutes: reasons.append("stale_market_data")
    return {"allowed":not reasons,"reasons":reasons,"protective_exit_allowed":True}
