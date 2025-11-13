from typing import Optional
from datetime import datetime
from backend.models import Subscription, Status, AccessFile

class SubscriptionService:
    @staticmethod
    async def get_active_subscription(user_id: int) -> Optional[dict]:
        active_status = await Status.get_or_none(type="subscription", code="ACTIVE")
        if not active_status:
            return None

        sub = await Subscription.filter(
            user_id=user_id,
            status_id=active_status.id,
            end_date__gte=datetime.utcnow(),
        ).prefetch_related("group").order_by("-end_date").first()

        if not sub:
            return None
        access_file = None
        if sub.group_id:
            access_file = await AccessFile.filter(group_id=sub.group_id).first()

        return {
            "tariff_id": sub.tariff_id,
            "status_id": sub.status_id,
            "end_date": sub.end_date,
            "group_name": sub.group.name if sub.group_id else None,
            "file_path": access_file.path if access_file else None,
        }
