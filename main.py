from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import io

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI está corriendo 🚀"}

@app.post("/procesar-csv")
async def procesar_csv(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    # Agrupar ventas por canción
    resumen = df.groupby("assetTitle")["partnerRevenue"].sum().reset_index()
    resumen = resumen.sort_values(by="partnerRevenue", ascending=False)

    # Convertimos a JSON
    resultado = resumen.to_dict(orient="records")

    return JSONResponse(content={"resumen_por_cancion": resultado})
