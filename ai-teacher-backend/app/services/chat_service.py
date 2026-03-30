"""Chat service for conversation-based knowledge point recommendation."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.services.llm_service import llm_service
from app.services.course_service import course_service
from app.repositories.course_repository import knowledge_point_repository

logger = logging.getLogger(__name__)


@dataclass
class ChatSession:
    """Chat session for conversation tracking."""

    id: str
    student_id: int
    messages: list[dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    analysis_result: Optional[dict] = None
    recommended_kp_id: Optional[str] = None


# In-memory storage for chat sessions
_chat_sessions: dict[str, ChatSession] = {}


class ChatService:
    """Service for handling chat-based knowledge point recommendation."""

    # Keywords mapping to knowledge points (for mock mode)
    KEYWORD_KP_MAPPING = {
        # 坐标系相关
        "坐标系": ["K1", "K2", "K3"],
        "坐标": ["K1", "K2", "K3"],
        "x轴": ["K1"],
        "y轴": ["K1"],
        "象限": ["K3"],
        "点": ["K2"],
        
        # 变量相关
        "变量": ["K4", "K5", "K6"],
        "常量": ["K5"],
        "自变量": ["K7"],
        "因变量": ["K7"],
        
        # 函数基础
        "函数": ["K6", "K10", "K15"],
        "函数定义": ["K6"],
        "定义域": ["K8"],
        "函数值": ["K9"],
        "解析式": ["K10"],
        
        # 正比例函数
        "正比例": ["K12", "K13", "K14"],
        "正比例函数": ["K12"],
        
        # 一次函数
        "一次函数": ["K15", "K16", "K18", "K24"],
        "k值": ["K21", "K22"],
        "b值": ["K20", "K23"],
        "斜率": ["K21"],
        "截距": ["K20"],
        
        # 图象相关
        "图象": ["K17", "K18", "K19"],
        "画图": ["K17"],
        "描点": ["K17"],
        "直线": ["K18", "K19"],
        
        # 性质相关
        "增减性": ["K24"],
        "单调性": ["K24"],
        "递增": ["K24"],
        "递减": ["K24"],
        "平移": ["K25"],
        
        # 应用相关
        "待定系数": ["K27"],
        "交点": ["K29"],
        "方程": ["K31"],
        "不等式": ["K32"],
        "应用题": ["K30"],
    }

    # Common confusion points and corresponding remedial knowledge points
    CONFUSION_PATTERNS = {
        "分不清正比例和一次函数": ["K16"],
        "不会画图": ["K17", "K19"],
        "不懂k和b的作用": ["K22", "K23"],
        "坐标算错": ["K2"],
        "不会求解析式": ["K27"],
        "搞不懂函数概念": ["K6", "K7"],
        "不会判断象限": ["K3", "K26"],
        "平移搞混了": ["K25"],
    }

    def create_session(self, student_id: int) -> ChatSession:
        """Create a new chat session.

        Args:
            student_id: Student ID.

        Returns:
            New chat session.
        """
        session_id = str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            student_id=student_id,
        )
        _chat_sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID.

        Args:
            session_id: Session ID.

        Returns:
            Chat session or None.
        """
        return _chat_sessions.get(session_id)

    def process_message(
        self,
        message: str,
        student_id: int,
        session_id: Optional[str] = None,
    ) -> dict:
        """Process a message and return recommendation.

        Args:
            message: Student's message.
            student_id: Student ID.
            session_id: Optional session ID for continuing conversation.

        Returns:
            Response dict with reply, is_ready, and recommendation.
        """
        # Get or create session
        if session_id:
            session = self.get_session(session_id)
            if not session or session.student_id != student_id:
                session = self.create_session(student_id)
        else:
            session = self.create_session(student_id)

        # Add message to session
        session.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
        })
        session.updated_at = datetime.now()

        # Analyze conversation
        analysis = self._analyze_conversation(session)
        session.analysis_result = analysis

        # Generate reply
        reply = self._generate_reply(session, analysis)

        # Add assistant reply to session
        session.messages.append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat(),
        })

        # Check if ready to recommend
        is_ready = analysis.get("is_ready", False)
        recommended_kp = None
        recommended_kp_name = None

        if is_ready and analysis.get("recommended_kp_ids"):
            kp_id = analysis["recommended_kp_ids"][0]
            session.recommended_kp_id = kp_id
            kp = knowledge_point_repository.get_by_id(kp_id)
            if kp:
                recommended_kp = kp_id
                recommended_kp_name = kp.name

        return {
            "reply": reply,
            "is_ready": is_ready,
            "recommended_kp": recommended_kp,
            "recommended_kp_name": recommended_kp_name,
            "session_id": session.id,
        }

    def _analyze_conversation(self, session: ChatSession) -> dict:
        """Analyze conversation to understand student needs.

        Args:
            session: Chat session.

        Returns:
            Analysis result.
        """
        # Try LLM analysis first
        if llm_service.is_available():
            try:
                return self._analyze_with_llm(session)
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to mock: {e}")

        # Fallback to mock analysis
        return self._analyze_with_mock(session)

    def _analyze_with_llm(self, session: ChatSession) -> dict:
        """Analyze conversation using LLM.

        Args:
            session: Chat session.

        Returns:
            Analysis result.
        """
        # Get all knowledge points for reference
        all_kps = knowledge_point_repository.get_all()
        kp_info = [
            {"id": kp.id, "name": kp.name, "description": kp.description}
            for kp in all_kps
        ]

        system_prompt = f"""你是一位专业的数学教师，正在分析学生的对话内容，了解学生的学习需求。

课程知识点列表：
{json.dumps(kp_info, ensure_ascii=False, indent=2)}

请分析学生的对话，判断：
1. 学生正在讨论什么数学话题？
2. 学生是否有明确的困惑或薄弱点？
3. 是否可以推荐一个知识点让学生开始学习？

回复格式（JSON）：
{{
    "topics": ["话题1", "话题2"],
    "weaknesses": ["薄弱点1", "薄弱点2"],
    "confidence": 0.7,
    "is_ready": true/false,
    "recommended_kp_ids": ["K1", "K2"],
    "reasoning": "推荐理由"
}}

注意：
- is_ready 为 true 表示已收集足够信息可以推荐知识点
- confidence 表示分析置信度（0-1）
- 如果学生话题不明确，is_ready 设为 false 并继续引导
- 推荐的知识点应该在知识点列表中存在"""

        # Build conversation history
        conversation = "\n".join([
            f"{'学生' if msg['role'] == 'user' else '老师'}：{msg['content']}"
            for msg in session.messages
        ])

        try:
            result = llm_service.chat_json(
                system_prompt=system_prompt,
                user_message=f"请分析以下对话：\n\n{conversation}",
            )
            return result
        except Exception as e:
            logger.error(f"LLM JSON parsing failed: {e}")
            raise

    def _analyze_with_mock(self, session: ChatSession) -> dict:
        """Analyze conversation using keyword matching (mock mode).

        Args:
            session: Chat session.

        Returns:
            Analysis result.
        """
        # Combine all user messages
        user_messages = [
            msg["content"] for msg in session.messages if msg["role"] == "user"
        ]
        combined_text = " ".join(user_messages)

        # Find matching knowledge points
        matched_kps = set()
        matched_keywords = []

        for keyword, kp_ids in self.KEYWORD_KP_MAPPING.items():
            if keyword in combined_text:
                matched_kps.update(kp_ids)
                matched_keywords.append(keyword)

        # Check for confusion patterns
        for pattern, kp_ids in self.CONFUSION_PATTERNS.items():
            if pattern in combined_text:
                matched_kps.update(kp_ids)

        # Determine if ready to recommend
        message_count = len(user_messages)
        is_ready = message_count >= 2 or bool(matched_kps)

        # Calculate confidence
        confidence = min(0.5 + len(matched_keywords) * 0.1 + message_count * 0.1, 1.0)

        # Sort matched KPs by level (prefer foundational ones)
        sorted_kps = self._sort_kps_by_level(list(matched_kps))

        return {
            "topics": matched_keywords[:5],
            "weaknesses": matched_keywords[:3],
            "confidence": confidence,
            "is_ready": is_ready,
            "recommended_kp_ids": sorted_kps[:3] if sorted_kps else [],
            "reasoning": f"根据关键词匹配：{', '.join(matched_keywords)}" if matched_keywords else "暂未发现明确话题",
        }

    def _sort_kps_by_level(self, kp_ids: list[str]) -> list[str]:
        """Sort knowledge points by level (ascending).

        Args:
            kp_ids: List of knowledge point IDs.

        Returns:
            Sorted list of knowledge point IDs.
        """
        kp_with_levels = []
        for kp_id in kp_ids:
            kp = knowledge_point_repository.get_by_id(kp_id)
            if kp:
                kp_with_levels.append((kp_id, kp.level))
        
        # Sort by level
        kp_with_levels.sort(key=lambda x: x[1])
        return [kp_id for kp_id, _ in kp_with_levels]

    def _generate_reply(self, session: ChatSession, analysis: dict) -> str:
        """Generate a reply based on analysis.

        Args:
            session: Chat session.
            analysis: Analysis result.

        Returns:
            Reply message.
        """
        # If ready with recommendation
        if analysis.get("is_ready") and analysis.get("recommended_kp_ids"):
            kp_id = analysis["recommended_kp_ids"][0]
            kp = knowledge_point_repository.get_by_id(kp_id)
            if kp:
                return f"根据我们的对话，我建议你可以从「{kp.name}」开始学习。这个知识点是：{kp.description or '重要基础内容'}。你觉得这个建议怎么样？如果同意，我们可以马上开始学习。"

        # If topics found but not ready
        topics = analysis.get("topics", [])
        if topics:
            return f"我注意到你对「{topics[0]}」比较感兴趣。能告诉我你具体想了解什么，或者遇到了什么困难吗？这样我可以更好地帮助你。"

        # Default guiding message
        greetings = [
            "你好！我是小艾老师，很高兴能帮助你学习数学。你最近在学什么呢？或者有什么数学问题想问我？",
            "欢迎来到数学学习！你可以告诉我你想学习什么内容，或者遇到了什么问题，我会帮你找到最适合的学习起点。",
            "嗨！我们可以聊聊你在数学学习中遇到的问题。比如函数、坐标系，或者任何你感兴趣的话题都可以。",
        ]

        # Return greeting based on message count
        if len(session.messages) <= 1:
            return greetings[0]
        elif len(session.messages) <= 3:
            return greetings[1]
        else:
            return greetings[2]


# Global service instance
chat_service = ChatService()
