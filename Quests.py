from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, Union

try:
	from Goal import Goal
except Exception:
	# Goal may not be importable in some static-analysis contexts; allow forward references
	Goal = Any


def _parse_datetime(value: Union[str, datetime]) -> datetime:
	if isinstance(value, datetime):
		return value
	if isinstance(value, str):
		try:
			# accept ISO-8601 like strings
			return datetime.fromisoformat(value)
		except Exception:
			raise ValueError("datetime strings must be ISO-8601 format")
	raise TypeError("start and end must be datetime or ISO-8601 string")


class Quest:
	"""A Quest is a task that belongs to a Goal.

	Fields:
	- name: short name of the quest
	- theme: which theme/topic this quest targets
	- study_time: estimated hours to complete (positive float)
	- start: start datetime (datetime or ISO string)
	- end: end datetime (datetime or ISO string)
	- xp_reward: integer XP granted when completed
	- stat_points: mapping of stat name -> integer points granted
	- associated_goal: reference to Goal instance or an identifier (string)
	- description: optional long description
	- progress: float 0.0-100.0 percent
	- completed: bool
	"""

	def __init__(
		self,
		name: str,
		theme: str,
		study_time: Union[int, float],
		start: Union[str, datetime],
		end: Union[str, datetime],
		xp_reward: int = 0,
		stat_points: Optional[Dict[str, int]] = None,
		associated_goal=None,
		description: str = "",
	) -> None:
		if not name or not isinstance(name, str):
			raise ValueError("name must be a non-empty string")
		if not theme or not isinstance(theme, str):
			raise ValueError("theme must be a non-empty string")
		if not isinstance(study_time, (int, float)) or study_time <= 0:
			raise ValueError("study_time must be a positive number (hours)")

		start_dt = _parse_datetime(start)
		end_dt = _parse_datetime(end)
		if end_dt < start_dt:
			raise ValueError("end datetime must be the same or after start datetime")

		if not isinstance(xp_reward, int) or xp_reward < 0:
			raise ValueError("xp_reward must be a non-negative integer")
		if stat_points is None:
			stat_points = {}
		if not isinstance(stat_points, dict):
			raise ValueError("stat_points must be a dict mapping stat->int")

		self.name: str = name.strip()
		self.theme: str = theme.strip()
		self.study_time: float = float(study_time)
		self.start: datetime = start_dt
		self.end: datetime = end_dt
		self.xp_reward: int = int(xp_reward)
		# shallow copy to avoid external mutation
		self.stat_points: Dict[str, int] = {k: int(v) for k, v in stat_points.items()}
		self.associated_goal = associated_goal
		self.description: str = description or ""

		self.progress: float = 0.0
		self.completed: bool = False

	def __repr__(self) -> str:
		return (
			f"Quest({self.name!r}, theme={self.theme!r}, study_time={self.study_time}h,"
			f" start={self.start.isoformat()}, end={self.end.isoformat()}, xp={self.xp_reward})"
		)

	def duration_hours(self) -> float:
		"""Return the planned duration in hours between start and end."""
		delta = self.end - self.start
		return delta.total_seconds() / 3600.0

	def increase_progress(self, increment: Union[int, float]) -> None:
		"""Increase progress by a positive increment; cap at 100 and mark completed."""
		if not isinstance(increment, (int, float)) or increment <= 0:
			raise ValueError("increment must be a positive number")
		self.progress = min(100.0, self.progress + float(increment))
		if self.progress >= 100.0:
			self.completed = True

	def mark_complete(self) -> None:
		"""Mark quest as fully completed and set progress to 100."""
		self.progress = 100.0
		self.completed = True

	def to_dict(self) -> Dict[str, Any]:
		"""Serialize the quest to a JSON-serializable dict."""
		goal_repr = None
		if self.associated_goal is None:
			goal_repr = None
		elif hasattr(self.associated_goal, "__dict__"):
			# try to represent Goal by name if it's an object
			goal_repr = getattr(self.associated_goal, "exam_name", str(self.associated_goal))
		else:
			goal_repr = str(self.associated_goal)

		return {
			"name": self.name,
			"theme": self.theme,
			"study_time": self.study_time,
			"start": self.start.isoformat(),
			"end": self.end.isoformat(),
			"xp_reward": self.xp_reward,
			"stat_points": dict(self.stat_points),
			"associated_goal": goal_repr,
			"description": self.description,
			"progress": self.progress,
			"completed": self.completed,
		}

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "Quest":
		"""Create a Quest from a dict produced by `to_dict`.

		Note: `associated_goal` will be left as the raw value from the dict.
		"""
		return cls(
			name=data["name"],
			theme=data.get("theme", ""),
			study_time=data.get("study_time", 0),
			start=data.get("start"),
			end=data.get("end"),
			xp_reward=data.get("xp_reward", 0),
			stat_points=data.get("stat_points", {}),
			associated_goal=data.get("associated_goal", None),
			description=data.get("description", ""),
		)

