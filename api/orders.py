from fastapi import FastAPI
from pydantic import BaseModel, Field
app=FastAPI(title="TradeAI Paper Orders API")
class PaperOrder(BaseModel):
    symbol:str=Field(min_length=1,max_length=30)
    side:str
    qty:float=Field(gt=0)
    price:float=Field(gt=0)
@app.post("/api/orders/paper")
def paper_order(o:PaperOrder):
    side=o.side.upper()
    if side not in {"BUY","SELL"}: return {"accepted":False,"error":"side_must_be_buy_or_sell"}
    return {"accepted":True,"mode":"paper","order":{"symbol":o.symbol.upper(),"side":side,"qty":o.qty,"price":o.price,"notional":round(o.qty*o.price,2)},"live_execution":False,"message":"Paper order accepted by API boundary; broker execution is not connected."}
