from datetime import datetime

from matplotlib.dates import relativedelta
from backend.models import Request, Status
from backend.models.subscription import AccessGroup, Subscription
from backend.schemas import RequestOut
from tortoise.exceptions import DoesNotExist


class RequestService:

    @staticmethod
    async def list_requests() -> list[RequestOut]:
        return await RequestOut.from_queryset(Request.all())

    @staticmethod
    async def get_request(request_id: int) -> RequestOut:
        request = await Request.get(id=request_id)
        return RequestOut.from_orm(request)
    
    @staticmethod
    async def approve_request(request_id: int, group_id: int | None = None) -> dict:
        request = await Request.get(id=request_id).prefetch_related("user", "duration", "tariff")

        status = await Status.get(type="subscription", code="ACTIVE")

        request.status = status
        await request.save()

        if not group_id:
            groups = await AccessGroup.all()
            if not groups:
                return {"error": "Нет доступных групп"}

            group_counts = []
            for g in groups:
                count = await Subscription.filter(group=g).count()
                group_counts.append((g, count))

            group, _ = min(group_counts, key=lambda x: x[1])
        else:
            group = await AccessGroup.get(id=group_id)

        duration_months = request.duration.months
        start_date = datetime.utcnow()
        end_date = start_date + relativedelta(months=duration_months)

        await Subscription.create(
            user=request.user,
            tariff_id=request.tariff.id,
            status_id=status.id,
            group=group,
            start_date=start_date,
            end_date=end_date
        )

        return {"message": f"Заявка {request_id} одобрена", "group": group.name, "duration_months": duration_months}

    @staticmethod
    async def reject_request(request_id: int) -> dict:
        request = await Request.get(id=request_id)

        status = await Status.get(type="request", code="REJECTED")

        request.status = status
        await request.save()

        return {"message": f"Заявка {request_id} отклонена"}
