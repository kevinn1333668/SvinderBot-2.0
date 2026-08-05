import random
from typing import Optional

from sqlalchemy import select, func, exists, delete

from src.repositories.base import BaseRepository
from src.repositories.models import Profile, Like, Complain, Dislike
from src.schemas.enums import SexFilterState, SexEnum
from src.schemas.profile import ProfileSchema, ProfileCreateDTO


class ProfileRepository(BaseRepository):
    async def get_profile_by_tg_id(self, tg_id: int) -> Profile | None:
        stmt = select(Profile).where(
            Profile.tg_id == tg_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_random_profile(
        self,
        curr_user_tg_id: int,
        sex_filter: SexFilterState
    ) -> Profile | None:
        excluded = (
            select(Like.liked_tg_id)
            .where(Like.liker_tg_id == curr_user_tg_id)
            .union_all(
                select(Complain.reported_tg_id).where(Complain.complainant_tg_id == curr_user_tg_id),
                select(Complain.complainant_tg_id).where(Complain.reported_tg_id == curr_user_tg_id),
                select(Dislike.disliked_tg_id).where(
                    (Dislike.disliker_tg_id == curr_user_tg_id) & (Dislike.until > func.now())
                ),
                select(Like.liker_tg_id).where(
                    (Like.liked_tg_id == curr_user_tg_id) & (Like.is_accepted == True)
                ),
            )
            .subquery()
        )

        conditions = [
            Profile.tg_id != curr_user_tg_id,
            ~exists(select(excluded.c.liked_tg_id).where(excluded.c.liked_tg_id == Profile.tg_id)),
            Profile.is_active.is_(True),
        ]

        if sex_filter == SexFilterState.ONLY_GIRLS:
            conditions.append(Profile.sex == SexEnum.FEMALE)
        elif sex_filter == SexFilterState.ONLY_BOYS:
            conditions.append(Profile.sex == SexEnum.MALE)

        count_stmt = select(func.count()).select_from(Profile).where(*conditions)
        total = (await self.session.execute(count_stmt)).scalar()

        if not total:
            return None

        offset = random.randint(0, total - 1)
        stmt = select(Profile).where(*conditions).offset(offset).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: ProfileCreateDTO) -> Profile:
        profile = Profile(
            tg_id=data.tg_id,
            name=data.name,
            age=data.age,
            sex=data.sex,
            town=data.town,
            description=data.description,
            s3_path=data.s3_path,
            sex_filter=SexFilterState.OFF
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update(self, tg_id: int, data: ProfileCreateDTO) -> Profile | None:
        profile = await self.get_profile_by_tg_id(tg_id)

        if profile is None:
            return None

        profile.name = data.name
        profile.age = data.age
        profile.sex = data.sex
        profile.town = data.town
        profile.description = data.description
        profile.s3_path = data.s3_path

        await self.session.flush()
        return profile


    async def delete(self, tg_id: int) -> bool:
        result = await self.session.execute(delete(Profile).where(Profile.tg_id == tg_id))
        return result.rowcount > 0


    async def toggle_sex_filter(self, tg_id: int) -> SexFilterState | None:
        profile = await self.get_profile_by_tg_id(tg_id)
        if profile is None:
            return  None

        order = [SexFilterState.OFF, SexFilterState.ONLY_GIRLS, SexFilterState.ONLY_BOYS]
        next_state = order[(order.index(profile.sex_filter) + 1) % len(order)]

        profile.sex_filter = next_state
        await self.session.flush()
        return next_state


    async def get_pending_liker_profiles(self, tg_id: int) -> list[Profile]:
        stmt = (
            select(Profile)
            .join(Like, Like.liker_tg_id == Profile.tg_id)
            .where(
                Like.liked_tg_id == tg_id,
                Like.is_accepted == False,
                ~exists().where(
                    (Complain.complainant_tg_id == tg_id) &
                    (Complain.reported_tg_id == Like.liker_tg_id)
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_mutual_liker_profiles(self, tg_id: int) -> list[Profile]:
        stmt = (
            select(Profile).where(
                Profile.tg_id.in_(
                    select(Like.liker_tg_id).where(
                        Like.liked_tg_id == tg_id, Like.is_accepted == True
                    )
                )
                | Profile.tg_id.in_(
                    select(Like.liked_tg_id).where(
                        Like.liker_tg_id == tg_id, Like.is_accepted == True
                    )
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
