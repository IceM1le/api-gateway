from app.services.base_service import BaseService


class DashboardService(BaseService):

    async def get_dashboard(self):
        data = await self.http_client.get("https://httpbin.org/json")

        return {
            "service": "dashboard",
            "data": data
        }