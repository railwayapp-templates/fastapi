from fastapi import FastAPI
import requests
from datetime import datetime, timedelta
from icalendar import Calendar

app = FastAPI()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/datas-indisponiveis")
def datas_indisponiveis():
    calendars = {
        "booking": "https://ical.booking.com/v1/export?t=e78ce65d-b3fe-4fd0-b601-c0d3f0c93b65",
        "vrbo": "http://www.vrbo.com/icalendar/72fd59aae4dc47e882434de6743ffe3c.ics?nonTentative",
        "holmy": "https://www.holmy.com.br/ical/251169.ics",
        "airbnb": "https://www.airbnb.com.br/calendar/ical/1358784443208247379.ics?s=e1b5ea024bec66ad2c2867eeba5f4f68"
    }

    def format_date(date):
        return date.strftime('%d/%m/%Y')

    def get_dates_between(start, end):
        dates = []
        current = start
        while current <= end:
            dates.append(format_date(current))
            current += timedelta(days=1)
        return dates

    all_dates = set()

    for plataforma, url in calendars.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            cal = Calendar.from_ical(response.text)

            for component in cal.walk():
                if component.name == "VEVENT":
                    start = component.get("dtstart").dt
                    end = component.get("dtend").dt
                    if isinstance(start, datetime) and isinstance(end, datetime):
                        dates = get_dates_between(start.date(), (end - timedelta(days=1)).date())
                        all_dates.update(dates)
        except Exception as e:
            print(f"Erro ao processar {plataforma}: {e}")
            return {"error": f"Erro ao processar {plataforma}: {e}"}

    sorted_dates = sorted(list(all_dates), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return {"datas_indisponiveis": sorted_dates}
