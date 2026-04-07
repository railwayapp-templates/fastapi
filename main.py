from fastapi import FastAPI
from pydantic import BaseModel
from gnews import GNews

app = FastAPI()

# 1. n8n에서 받을 데이터 형태 (키워드와 가져올 기사 개수)
class NewsInput(BaseModel):
    keyword: str
    max_results: int = 10  # 기본값 10개 (n8n에서 값을 안 보내면 10개만 가져옴)

# 2. POST 요청 처리
@app.post("/")
def get_google_news(data: NewsInput):
    keyword = data.keyword
    
    try:
        # GNews 설정: 한국어, 한국 지역, 최근 7일(7d), 최대 검색 개수 설정
        google_news = GNews(language='ko', country='KR', period='7d', max_results=data.max_results)
        
        # 키워드로 뉴스 검색
        news_list = google_news.get_news(keyword)
        
        if not news_list:
            return {
                "status": "empty",
                "keyword": keyword,
                "message": "해당 키워드에 대한 최신 기사가 없습니다."
            }
            
        # 수집된 기사 목록 반환
        return {
            "status": "success",
            "keyword": keyword,
            "article_count": len(news_list),
            "articles": news_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
