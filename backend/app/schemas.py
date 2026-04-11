

from pydantic import BaseModel


class ChatRequest(BaseModel):
	message: str
	location: str | None = None

class ChatResponse(BaseModel):
    route: str
    answer: str

# Weather service models
class WeatherResult(BaseModel):
	location: str
	condition: str
	temp_c: float
	temp_f: float
	feelslike_c: float
	feelslike_f: float
	humidity: int
	wind_kph: float
	wind_mph: float

# News service models
class NewsArticle(BaseModel):
	title: str
	source: str
	publishedAt: str
	url: str

class NewsResult(BaseModel):
	articles: list[NewsArticle]
