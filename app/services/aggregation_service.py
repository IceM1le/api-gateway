#app/services/aggregation_service.py
import asyncio


class AggregationService:
    def __init__(self, http_client):
        self.http_client = http_client

    async def get_dashboard(self):
        weather_url = "https://httpbin.org/json"
        news_url = "https://httpbin.org/json"
        currency_url = "https://httpbin.org/json"

        weather_task = self.http_client.get(weather_url)
        news_task = self.http_client.get(news_url)
        currency_task = self.http_client.get(currency_url)

        weather, news, currency = await asyncio.gather(
            weather_task,
            news_task,
            currency_task,
            return_exceptions=True
        )

        return {
            "weather": self.safe(weather),
            "news": self.safe(news),
            "currency": self.safe(currency),
        }

    def safe(self, result):
        if isinstance(result, Exception):
            return {"error": "service unavailable"}
        return result