from fastapi import HTTPException
from backend.services.subscription_service import SubscriptionService
from backend.models import User
from backend.models.enums import Tariff
from backend.schemas import UserOut, UserBase, UserUpdate, UserCreate
from backend.schemas.user import ProfileOut

class UserService:

    @staticmethod
    async def get_or_create_by_tg(user: UserCreate) -> User:
        existing = await User.get_or_none(tg_id=user.tg_id)
        if existing:
            return existing
        return await User.create(**user.dict())

    @staticmethod
    async def get_by_tg(tg_id: int) -> User:
        user = await User.get_or_none(tg_id=tg_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    async def create_user(data: UserCreate):
        existing = await User.get_or_none(tg_id=data.tg_id)
        if existing:
            return existing
        return await User.create(**data.dict())

    @staticmethod
    async def list_users() -> list[UserOut]:
        users = await User.all()
        return [UserOut.from_orm(user) for user in users]

    @staticmethod
    async def get_user(user_id: int) -> UserOut:
        user = await User.get_or_none(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.from_orm(user)
    
    @staticmethod
    async def update_user(user_id: int, data: UserUpdate) -> UserOut:
        user = await User.get(id=user_id)
        data_dict = data.dict(exclude_unset=True)

        for key, value in data_dict.items():
            setattr(user, key, value)

        await user.save()
        return UserOut.from_orm(user)

    @staticmethod
    async def deactivate_user(user_id: int) -> dict:
        user = await User.get(id=user_id)
        user.is_active = False
        await user.save()
        return {"message": f"Пользователь {user_id} деактивирован"}
    
    @staticmethod
    async def get_profile_by_tg(tg_id: int) -> ProfileOut:
        user = await UserService.get_by_tg(tg_id)

        sub_info = await SubscriptionService.get_active_subscription(user.id)

        tariff_code = tariff_name = None
        active_until = None
        access_group = None
        access_file_path = None

        if sub_info:
            active_until = sub_info["end_date"]
            access_group = sub_info["group_name"]
            access_file_path = sub_info["file_path"]

            tariff = await Tariff.get_or_none(id=sub_info["tariff_id"])
            if tariff:
                tariff_code = tariff.code
                tariff_name = tariff.name

        return ProfileOut(
            user_id=user.id,
            tg_id=user.tg_id,
            username=user.username,
            full_name=user.full_name,
            tariff_code=tariff_code,
            tariff_name=tariff_name,
            active_until=active_until,
            access_group=access_group,
            access_file_path=access_file_path,
            bonus_balance=user.bonus_balance,
            token_balance=user.token_balance,
            channel_bonus_given=user.channel_bonus_given,
            channel_subscription_message_shown=user.channel_subscription_message_shown,
        )