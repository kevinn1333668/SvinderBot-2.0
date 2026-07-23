import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

from src.repositories.uow import UnitOfWork
from src.schemas.enums import SexFilterState
from src.schemas.profile import ProfileSchema, ProfileCreateDTO, ProfileUpdateDTO

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def search_random_profile(self, curr_user_tg_id, sex_filter: SexFilterState) -> Optional[ProfileSchema]:
        async with self._uow as uow:
            profile = await uow.profiles.get_random_profile(curr_user_tg_id, sex_filter)

            if profile is None:
                return None

            return ProfileSchema.model_validate(profile)

    async def get_profile_by_tg_id(self, tg_id: int) -> Optional[ProfileSchema]:
        async with self._uow as uow:
            profile = await uow.profiles.get_profile_by_tg_id(tg_id)

            if profile is None:
                return None

            return ProfileSchema.model_validate(profile)

    async def create_profile(self, profile: ProfileCreateDTO) -> ProfileSchema | None:
        async with self._uow as uow:
            logger.info("Creating new profile for tg_id=%s", profile.tg_id)
            try:
                profile = await uow.profiles.create(profile)
                await uow.commit()
                return ProfileSchema.model_validate(profile)
            except IntegrityError:
                logger.exception("Failed to create new profile for tg_id=%s", profile.tg_id)
                await uow.rollback()
                return None

    async def update_profile(self, tg_id: int, data: ProfileUpdateDTO) -> ProfileSchema | None:
        async with self._uow as uow:
            logger.info("Updating profile for tg_id=%s", tg_id)
            profile = await uow.profiles.update(tg_id, data)
            if profile is None:
                return None
            await uow.commit()
            await uow.session.refresh(profile)
            return ProfileSchema.model_validate(profile)

    async def delete_profile(self, tg_id: int) -> bool:
        async with self._uow as uow:
            logger.info("Deleting profile for tg_id=%s", tg_id)
            result = await uow.profiles.delete(tg_id)
            await uow.commit()
            return result

    async def toggle_sex_filter(self, tg_id: int) -> SexFilterState | None:
        async with self._uow as uow:
            new_state = await uow.profiles.toggle_sex_filter(tg_id)
            if new_state is None:
                return None
            await uow.commit()
            return new_state

    async def get_pending_liker_profiles(self, tg_id: int) -> list[ProfileSchema] | None:
        async with self._uow as uow:
            profiles = await uow.profiles.get_pending_liker_profiles(tg_id)
            return [ProfileSchema.model_validate(profile) for profile in profiles]

    async def get_mutual_liker_profiles(self, tg_id: int) -> list[ProfileSchema] | None:
        async with self._uow as uow:
            profiles = await uow.profiles.get_mutual_liker_profiles(tg_id)
            if profiles is None:
                return None
            return [ProfileSchema.model_validate(profile) for profile in profiles]
