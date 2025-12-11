from fastapi import APIRouter, Form, HTTPException, BackgroundTasks, Depends
from backend.models import User, Tariff, Duration, Request, Status, Subscription, Referral
from backend.models.file import AccessFile
from backend.schemas import RequestOut
from backend.services.settings_service import SettingsService
from backend.api.admin import get_current_admin
from backend.models.admin import Admin
from datetime import datetime, timedelta
import httpx

router = APIRouter(prefix="/admin/requests", tags=["Admin - Requests"])

BOT_URL = "http://bot:8001/notify" 

@router.get("/subscriptions")
async def list_subscriptions(admin: Admin = Depends(get_current_admin)):
    """
    Получить все активные подписки с именем файла (требует аутентификации админа)
    """
    subs = await Subscription.all().prefetch_related(
        "user", "group", "group__files"
    )

    result = []
    for s in subs:
        files = await s.group.files.all() if s.group else []
        file_name = files[0].path if files else None

        result.append({
            "id": s.id,
            "username": s.user.username if s.user else None,
            "tg_id": s.user.tg_id if s.user else None,
            "user_id": s.user.id if s.user else None,
            "bonus_balance": s.user.bonus_balance if s.user else 0,
            "token_balance": s.user.token_balance if s.user else 0,
            "tariff_id": s.tariff_id,
            "status_id": s.status_id,
            "start_date": s.start_date,
            "end_date": s.end_date,
            "group": s.group.name if s.group else None,
            "file_name": file_name,
        })

    return result

async def notify_user(tg_id: int, message: str):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(BOT_URL, json={"tg_id": tg_id, "message": message})
        except Exception as e:
            print(f"⚠ Ошибка при отправке уведомления: {e}")

async def get_status(type: str, code: str):
    status = await Status.get_or_none(type=type, code=code)
    if not status:
        status = await Status.create(type=type, code=code, name=code.capitalize())
    return status


@router.get("/", response_model=list[RequestOut])
async def list_requests(admin: Admin = Depends(get_current_admin)):
    """
    Получить все заявки (требует аутентификации админа)
    """
    print(f"[list_requests] Запрос от админа: {admin.username}")
    requests = await Request.all().prefetch_related('user', 'tariff', 'duration', 'status')
    result = [await RequestOut.from_orm(req) for req in requests]
    print(f"[list_requests] Возвращено заявок: {len(result)}")
    return result


@router.post("/")
async def create_request(data: dict):
    """
    Создание заявки из бота
    data = { tg_id, tariff_code, duration_months, subscription_type, group_id?, user_email? }
    """
    print(f"[CREATE_REQUEST] Received data: {data}")

    try:
        user = await User.get_or_none(tg_id=data["tg_id"])
        if not user:
            print(f"[CREATE_REQUEST] User not found: tg_id={data['tg_id']}")
            raise HTTPException(status_code=404, detail="User not found")

        tariff = await Tariff.get_or_none(code=data["tariff_code"])
        if not tariff:
            print(f"[CREATE_REQUEST] Invalid tariff: {data['tariff_code']}")
            raise HTTPException(status_code=400, detail="Invalid tariff")

        duration = await Duration.get_or_none(months=data["duration_months"])
        if not duration:
            print(f"[CREATE_REQUEST] Invalid duration: {data['duration_months']}")
            raise HTTPException(status_code=400, detail="Invalid duration")

        subscription_type = data.get("subscription_type", "group")  # По умолчанию складчина
        group_id = data.get("group_id")
        user_email = data.get("user_email")
        
        # Валидация в зависимости от типа подписки
        if subscription_type == "group" and not group_id:
            raise HTTPException(status_code=400, detail="Для складчины необходимо указать group_id")
        elif subscription_type == "individual":
            # Для индивидуального доступа сохраняем email, если был указан
            if user_email:
                user.email = user_email
                await user.save()

        status = await get_status(type="request", code="PENDING")
        print(f"[CREATE_REQUEST] Status: {status.name} (id={status.id})")

        req = await Request.create(
            user=user,
            tariff=tariff,
            duration=duration,
            status=status,
            subscription_type=subscription_type,
            group_id=group_id,
            user_email=user_email,
        )

        print(f"[CREATE_REQUEST] Request created successfully: id={req.id}, user={user.tg_id}, tariff={tariff.code}, duration={duration.months}, type={subscription_type}")
        
        return {"received_data": data, "id": req.id, "message": "Request created"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CREATE_REQUEST] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{request_id}/approve")
async def approve_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(get_current_admin),
    group_id: int | None = Form(None),  # ID группы для складчины
):
    try:
        # Загружаем заявку с связанными объектами
        req = await Request.get_or_none(id=request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Загружаем связанные объекты
        await req.fetch_related("user", "tariff", "duration")
        
        if not req.user:
            raise HTTPException(status_code=400, detail="User not found in request")
        if not req.tariff:
            raise HTTPException(status_code=400, detail="Tariff not found in request")
        if not req.duration:
            raise HTTPException(status_code=400, detail="Duration not found in request")

        active_status = await get_status(type="subscription", code="ACTIVE")
        approved_status = await get_status(type="request", code="APPROVED")
        end_date = datetime.utcnow() + timedelta(days=30 * req.duration.months)

        subscription_type = getattr(req, 'subscription_type', 'group')
        group = None
        
        # Для складчины - привязываем группу файлов
        if subscription_type == "group":
            if group_id:
                from backend.models.subscription import AccessGroup
                group = await AccessGroup.get_or_none(id=group_id)
                if not group:
                    raise HTTPException(status_code=404, detail="AccessGroup not found")
            else:
                # Используем группу из заявки, если она была указана при создании
                request_group_id = getattr(req, 'group_id', None)
                if request_group_id:
                    from backend.models.subscription import AccessGroup
                    group = await AccessGroup.get_or_none(id=request_group_id)
                    if not group:
                        raise HTTPException(status_code=404, detail="AccessGroup from request not found")
                else:
                    raise HTTPException(status_code=400, detail="Для складчины необходимо указать group_id")
        # Для индивидуального доступа - группа не привязывается (group остается None)

        subscription = await Subscription.create(
            user_id=req.user.id,
            tariff_id=req.tariff.id,
            duration_id=req.duration.id,
            status_id=active_status.id,
            group=group,  # None для индивидуального доступа
            start_date=datetime.utcnow(),
            end_date=end_date,
        )

        req.status = approved_status
        await req.save()

        # Создание ожидающего реферального бонуса вместо автоматического начисления
        referral = await Referral.get_or_none(referred=req.user)
        if referral and not referral.activated:
            referral.activated = True
            await referral.save()

            # Получаем размер бонуса из настроек
            bonus_amount = await SettingsService.get_referral_bonus()
            # Загружаем referrer явно
            await referral.fetch_related("referrer")
            referrer = referral.referrer
            
            if referrer:
                # Создаем запись о pending bonus вместо автоматического начисления
                from backend.models.pending_bonus import PendingBonus
                await PendingBonus.create(
                    referral=referral,
                    referrer=referrer,
                    referred=req.user,
                    bonus_amount=bonus_amount,
                    request=req,
                    status="pending"
                )
        
        subscription_type_name = "Индивидуальный доступ" if subscription_type == "individual" else "Складчина"
        message = f"✅ Ваша заявка #{req.id} на тариф {req.tariff.name} ({subscription_type_name}) одобрена!\nИспользуйте /start еще раз для перехода в профиль и использования бота!"
        if group:
            message += f"\nГруппа файлов: {group.name} привязана к вашей подписке."
        background_tasks.add_task(notify_user, req.user.tg_id, message)

        return {
            "message": f"Request {request_id} approved",
            "subscription_id": subscription.id,
            "subscription_type": subscription_type,
            "group": group.name if group else None,
            "group_id": group.id if group else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{request_id}/reject")
async def reject_request(
    request_id: int, 
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(get_current_admin)
):
    """
    Отклонить заявку (требует аутентификации админа)
    """
    req = await Request.get_or_none(id=request_id).prefetch_related("user", "tariff")
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    rejected_status = await get_status(type="request", code="REJECTED")
    req.status = rejected_status
    await req.save()

    background_tasks.add_task(
        notify_user,
        req.user.tg_id,
        f"❌ Ваша заявка #{req.id} на тариф {req.tariff.name} отклонена."
    )

    return {"message": f"Request {request_id} rejected"}
