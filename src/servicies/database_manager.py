from contextlib import contextmanager
from typing import Any, Generator, cast, Optional

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine, URL

import logging

from src.core.config import settings
from src.servicies.models import Base, UserProfile
from src.servicies.schema import UserProfileResponse, UserProfileUpdate, UserProfileModel, UserProfileCreate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        url = URL(
            drivername=settings.driver,
            username=settings.user,
            password=settings.password,
            host=settings.host,
            database=settings.db,
            port=settings.port,
            query=settings.query
        )

        self.engine = create_engine(url)
        self.session = sessionmaker(bind=self.engine)

        if not database_exists(url):
            create_database(url)
            logger.info('Database created successfully')
        else:
            logger.info('Database already exists')

        Base.metadata.create_all(self.engine)

    @contextmanager
    def _session_scope(self) -> Generator[Session, Any, None]:
        session = self.session()
        try:
            yield cast(Session, session)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f'Error during working with session: {e}')

        finally:
            session.close()

    # —————————————————————————————
    # CRUD для UserProfile
    # —————————————————————————————

    def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfileResponse:
        with self._session_scope() as session:
            db_profile = UserProfile(**profile_data.model_dump())
            session.add(db_profile)
            session.flush()  # Чтобы получить id
            return UserProfileResponse.model_validate(db_profile)

    def get_user_profile_by_id(self, profile_id: int) -> Optional[UserProfileResponse]:
        with self._session_scope() as session:
            profile = session.get(UserProfile, profile_id)
            return UserProfileResponse.model_validate(profile) if profile else None

    def get_user_profile_by_user_id(self, user_id: int) -> Optional[UserProfileResponse]:
        with self._session_scope() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            return UserProfileResponse.model_validate(profile) if profile else None

    def update_user_profile(self, user_id: int, profile_update: UserProfileUpdate) -> Optional[UserProfileResponse]:
        with self._session_scope() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return None

            # Обновляем только непустые поля
            update_data = profile_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(profile, key, value)

            session.add(profile)
            return UserProfileResponse.model_validate(profile)

    def delete_user_profile(self, user_id: int) -> bool:
        with self._session_scope() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return False

            session.delete(profile)
            return True

