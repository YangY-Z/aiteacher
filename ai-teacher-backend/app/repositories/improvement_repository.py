"""专项提升模块数据访问层。"""

from typing import Optional

from app.models.improvement import ImprovementSession
from app.repositories.memory_db import db


class ImprovementRepository:
    """专项提升数据仓库。"""

    def create_session(self, session: ImprovementSession) -> ImprovementSession:
        db._improvement_sessions[session.session_id] = session
        db.save_student_data()
        return session

    def get_session(self, session_id: str) -> Optional[ImprovementSession]:
        return db._improvement_sessions.get(session_id)

    def update_session(self, session: ImprovementSession) -> ImprovementSession:
        db._improvement_sessions[session.session_id] = session
        db.save_student_data()
        return session

    def get_student_sessions(self, student_id: str, course_id: str) -> list[ImprovementSession]:
        return [
            session
            for session in db._improvement_sessions.values()
            if session.student_id == student_id and session.course_id == course_id
        ]


improvement_repository = ImprovementRepository()
