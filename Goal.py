from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def _parse_date(value: Union[str, datetime]) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        try:
            # accept ISO-8601 like strings
            dt = datetime.fromisoformat(value)
            return dt.date().isoformat()
        except Exception:
            # assume it's already a date string in some user-provided format
            return value
    raise TypeError("exam_date must be a date string or datetime")


class Goal:
    """Represents an exam goal composed of many quests/tasks.

    Attributes:
    - exam_name, exam_subject: strings
    - exam_date: ISO date string
    - hours_willing: planned total study hours (float)
    - themes: list of theme strings
    - quests: list of quest dicts or objects (kept generic to avoid circular imports)
    - progress: percentage 0.0-100.0
    - completed: bool
    """

    def __init__(
        self,
        exam_name: str,
        exam_subject: str,
        exam_date: Union[str, datetime],
        hours_willing: Union[int, float],
        themes: Union[List[str], tuple],
    ) -> None:
        if not exam_name or not isinstance(exam_name, str):
            raise ValueError("exam_name must be a non-empty string")
        if not exam_subject or not isinstance(exam_subject, str):
            raise ValueError("exam_subject must be a non-empty string")
        if not exam_date:
            raise ValueError("exam_date must be provided")
        if not isinstance(hours_willing, (int, float)) or hours_willing <= 0:
            raise ValueError("hours_willing must be a positive number")
        if not isinstance(themes, (list, tuple)) or not themes:
            raise ValueError("themes must be a non-empty list or tuple of strings")

        self.exam_name: str = exam_name.strip()
        self.exam_subject: str = exam_subject.strip()
        self.exam_date: str = _parse_date(exam_date)
        self.hours_willing: float = float(hours_willing)
        self.themes: List[str] = [str(t).strip() for t in list(themes)]

        # quests are stored as-is (can be dicts or objects with expected attrs)
        self.quests: List[Any] = []

        self.progress: float = 0.0
        self.completed: bool = False

    def __repr__(self) -> str:
        return (
            f"Goal({self.exam_name!r}, {self.exam_subject!r}, date={self.exam_date},"
            f" hours_willing={self.hours_willing}h, themes={self.themes})"
        )

    def add_quest(self, quest: Any) -> None:
        """Attach a quest to this goal.

        `quest` can be an object (e.g., instance of `Quest`) or a dict-like object.
        The method performs minimal validation (requires a `study_time` attribute or key).
        """
        # try to read study_time
        study_time = None
        if isinstance(quest, dict):
            study_time = quest.get("study_time")
        else:
            study_time = getattr(quest, "study_time", None)

        if study_time is None:
            raise ValueError("quest must provide a `study_time` value")
        if not isinstance(study_time, (int, float)) or study_time <= 0:
            raise ValueError("quest.study_time must be a positive number")

        self.quests.append(quest)
        self.recalc_progress()

    def remove_quest(self, identifier: Union[str, Any]) -> bool:
        """Remove a quest by name or by object reference.

        Returns True if a quest was removed.
        """
        removed = False
        for q in list(self.quests):
            name = None
            if isinstance(q, dict):
                name = q.get("name")
            else:
                name = getattr(q, "name", None)

            if identifier is q or identifier == name:
                self.quests.remove(q)
                removed = True
        if removed:
            self.recalc_progress()
        return removed

    def total_study_time(self) -> float:
        """Sum of study_time across all attached quests."""
        total = 0.0
        for q in self.quests:
            if isinstance(q, dict):
                st = q.get("study_time", 0)
            else:
                st = getattr(q, "study_time", 0)
            try:
                total += float(st)
            except Exception:
                continue
        return total

    def recalc_progress(self) -> float:
        """Recalculate goal progress based on the number of completed quests.

        Progress = (completed_quests / total_quests) * 100%
        If no quests are attached, returns current `self.progress` unchanged.
        """
        if not self.quests:
            return self.progress

        completed_count = 0
        for q in self.quests:
            if isinstance(q, dict):
                completed = q.get("completed", False)
            else:
                completed = getattr(q, "completed", False)
            
            if completed:
                completed_count += 1

        total_quests = len(self.quests)
        self.progress = (completed_count / total_quests) * 100.0
        self.progress = min(100.0, max(0.0, self.progress))
        self.completed = self.progress >= 100.0
        return self.progress

    def increase_progress(self, increment: Union[int, float]) -> None:
        """Increase goal-level progress manually. This does not change quests."""
        if not isinstance(increment, (int, float)) or increment <= 0:
            raise ValueError("increment must be a positive number")
        self.progress = min(100.0, self.progress + float(increment))
        if self.progress >= 100.0:
            self.completed = True

    def mark_complete(self) -> None:
        """Mark the goal as completed (sets progress to 100)."""
        self.progress = 100.0
        self.completed = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Goal to a JSON-serializable dict.

        Quests are represented by their dict form when possible (call `to_dict` on objects that have it).
        """
        quests_serialized: List[Any] = []
        for q in self.quests:
            if isinstance(q, dict):
                quests_serialized.append(q)
            else:
                to_dict = getattr(q, "to_dict", None)
                if callable(to_dict):
                    quests_serialized.append(to_dict())
                else:
                    # fall back to a minimal dict representation
                    quests_serialized.append({
                        "name": getattr(q, "name", str(q)),
                        "study_time": getattr(q, "study_time", 0),
                        "progress": getattr(q, "progress", 0),
                    })

        return {
            "exam_name": self.exam_name,
            "exam_subject": self.exam_subject,
            "exam_date": self.exam_date,
            "hours_willing": self.hours_willing,
            "themes": list(self.themes),
            "quests": quests_serialized,
            "progress": self.progress,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        """Create a Goal instance from a dict (as produced by `to_dict`).

        Note: quests will be kept as dicts; callers may convert them to Quest objects.
        """
        g = cls(
            exam_name=data["exam_name"],
            exam_subject=data.get("exam_subject", ""),
            exam_date=data.get("exam_date", ""),
            hours_willing=data.get("hours_willing", 0),
            themes=data.get("themes", []),
        )
        quests = data.get("quests", [])
        for q in quests:
            g.quests.append(q)
        g.progress = float(data.get("progress", g.progress))
        g.completed = bool(data.get("completed", g.completed))
        return g