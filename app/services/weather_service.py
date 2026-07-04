from app.services.base_service import BaseService


class WeatherService(BaseService):

    async def get_weather(self):
        return await self.http_client.get(
            "https://jsonplaceholder.typicode.com/todos/2"
        )