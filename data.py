from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import os
import uuid

# ✅ Initialize FastAPI app
app = FastAPI(title="CSV Upload & Analyzer API")

# ✅ Directories for uploads and charts
UPLOAD_DIR = "uploads"
CHART_DIR = "charts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)


@app.post("/upload-csv/")
async def upload_csv(
    file: UploadFile,
    x_axis: str = Form(None),
    y_axis: str = Form(None),
    chart_type: str = Form("line")
):
    """
    Uploads a CSV, cleans missing data, generates basic statistics,
    and creates a chart based on user input.
    """

    # ✅ Save uploaded CSV
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.csv")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # ✅ Read the CSV file
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to read CSV: {str(e)}"}, status_code=400)

    # ✅ Identify numeric and categorical columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    # ✅ Handle missing values
    for col in categorical_cols:
        if df[col].isnull().mean() * 100 < 20:
            df[col].fillna(df[col].mode()[0], inplace=True)
        else:
            df.drop(columns=[col], inplace=True)

    for col in numeric_cols:
        if df[col].isnull().mean() * 100 < 20:
            df[col].fillna(df[col].mean(), inplace=True)
        else:
            df.drop(columns=[col], inplace=True)

    # ✅ Update column lists after cleaning
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    # ✅ Default axis handling
    if not x_axis or x_axis not in df.columns:
        x_axis = df.columns[0]
    if numeric_cols:
        if not y_axis or y_axis not in numeric_cols:
            y_axis = numeric_cols[0]
    else:
        y_axis = None

    # ✅ Get stats
    stats = df.describe().to_dict() if numeric_cols else {}

    # ✅ Chart generation
    chart_path = None
    if x_axis and y_axis and x_axis in df.columns and y_axis in df.columns:
        plt.figure(figsize=(8, 5))
        try:
            if chart_type == "bar":
                df.plot(kind="bar", x=x_axis, y=y_axis)
            elif chart_type == "scatter":
                df.plot(kind="scatter", x=x_axis, y=y_axis)
            else:
                df.plot(kind="line", x=x_axis, y=y_axis)

            plt.title(f"{chart_type.capitalize()} Chart of {y_axis} vs {x_axis}")
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
            plt.tight_layout()

            chart_filename = f"{uuid.uuid4()}.png"
            chart_path = os.path.join(CHART_DIR, chart_filename)
            plt.savefig(chart_path)
            plt.close()
        except Exception as e:
            return JSONResponse(content={"error": f"Chart generation failed: {str(e)}"}, status_code=500)

    # ✅ Response
    return {
        "message": "✅ CSV processed successfully!",
        "x_axis": x_axis,
        "y_axis": y_axis,
        "chart_type": chart_type,
        "chart_file": chart_path,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "stats": stats,
        "rows": len(df),
        "columns": len(df.columns)
    }


# ✅ Main entry point (for Railway / Render / Local)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Railway auto-assigns this
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
