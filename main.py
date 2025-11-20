from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TradingView → Alpaca webhook is LIVE! 🚀"}

@app.post("/tv-entry")
async def tradingview_webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
        lines = [line.strip() for line in message.split("\n") if line.strip()]
        if len(lines) >= 4 and lines[0] == "ENTRY":
            direction = lines[1].split(": ")[1]
            ticker = lines[2].split(": ")[1]
            price = lines[3].split(": ")[1]
            
            print(f"🟢 NEW SIGNAL → {direction} {ticker} @ {price}")
            
            return {
                "status": "success",
                "direction": direction,
                "ticker": ticker,
                "entry_price": price,
                "timestamp": data.get("time", "")
            }
        else:
            return {"status": "ignored", "raw": message}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
