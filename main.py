from fastapi import FastAPI
import pyodbc

app = FastAPI()

def get_connection():
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=BSERVER\\PBSERVER;"
        "Database=COM_JSF;"
        "UID=sa;"
        "PWD=SVVsvv@999;"
    )

@app.get("/ascur")
def get_customers():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT curno, Cur, rate FROM ascur")
    rows = cursor.fetchall()

    data = []
    for r in rows:
        data.append({
            "Currency#": r[0],   # curno
            "Cur Name": r[1],    # Cur
            "rate": r[2]         # rate
        })

    conn.close()
    return data
