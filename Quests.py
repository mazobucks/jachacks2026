from __future__ import annotations
from typing import Optional, Dict, Any, Union

try:
	from Goal import Goal
except Exception:
	# Goal may not be importable in some static-analysis contexts; allow forward references
	Goal = Any


class Quest:
	"""A Quest is a task that belongs to a Goal.

	Fields:
	- name: short name of the quest
	- theme: which theme/topic this quest targets
	- study_time: estimated hours to complete (positive float)
	- time_spent: actual hours spent studying (float, default 0.0)
	- date: date to work on the quest (ISO date string)
	- xp_reward: integer XP granted when completed
	- stat_points: mapping of stat name -> integer points granted
	- associated_goal: reference to Goal instance or an identifier (string)
	- description: optional long description
	- progress: float 0.0-100.0 percent (based on time_spent / study_time)
	- completed: bool
	- failed: bool (quest failed quiz)
	"""

	def __init__(
		self,
		name: str,
		theme: str,
		study_time: Union[int, float],
		date: str,
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
		if not date or not isinstance(date, str):
			raise ValueError("date must be a non-empty string (ISO format)")

		if not isinstance(xp_reward, int) or xp_reward < 0:
			raise ValueError("xp_reward must be a non-negative integer")
		if stat_points is None:
			stat_points = {}
		if not isinstance(stat_points, dict):
			raise ValueError("stat_points must be a dict mapping stat->int")

		self.name: str = name.strip()
		self.theme: str = theme.strip()
		self.study_time: float = float(study_time)
		self.time_spent: float = 0.0  # Track actual time spent studying
		self.date: str = date.strip()
		self.xp_reward: int = int(xp_reward)
		# shallow copy to avoid external mutation
		self.stat_points: Dict[str, int] = {k: int(v) for k, v in stat_points.items()}
		self.associated_goal = associated_goal
		self.description: str = description or ""

		self.progress: float = 0.0  # Updated based on time_spent / study_time
		self.completed: bool = False
		self.failed: bool = False  # Quest failed after quiz

	def __repr__(self) -> str:
		return (
			f"Quest({self.name!r}, theme={self.theme!r}, study_time={self.study_time}h,"
			f" date={self.date}, xp={self.xp_reward})"
		)
	
	def quizInfoString(self):
		return (f"name: {self.name}, theme: {self.theme}, description: {self.description}")

	def increase_progress(self, increment: Union[int, float]) -> None:
		"""Increase progress by a positive increment; cap at 100 and mark completed."""
		if not isinstance(increment, (int, float)) or increment <= 0:
			raise ValueError("increment must be a positive number")
		self.progress = min(100.0, self.progress + float(increment))
		if self.progress >= 100.0:
			self.completed = True

	def update_time_spent(self, hours: Union[int, float]) -> None:
		"""Update time spent and recalculate progress as (time_spent / study_time) * 100."""
		if not isinstance(hours, (int, float)) or hours < 0:
			raise ValueError("hours must be a non-negative number")
		self.time_spent = float(hours)
		# Recalculate progress based on time spent vs planned time
		if self.study_time > 0:
			self.progress = min(100.0, (self.time_spent / self.study_time) * 100.0)

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
			"time_spent": self.time_spent,
			"date": self.date,
			"xp_reward": self.xp_reward,
			"stat_points": dict(self.stat_points),
			"associated_goal": goal_repr,
			"description": self.description,
			"progress": self.progress,
			"completed": self.completed,
			"failed": self.failed,
		}

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "Quest":
		"""Create a Quest from a dict produced by `to_dict`.

		Note: `associated_goal` will be left as the raw value from the dict.
		"""
		quest = cls(
			name=data["name"],
			theme=data.get("theme", ""),
			study_time=data.get("study_time", 0),
			date=data.get("date", ""),
			xp_reward=data.get("xp_reward", 0),
			stat_points=data.get("stat_points", {}),
			associated_goal=data.get("associated_goal", None),
			description=data.get("description", ""),
		)
		# FIXED: Restore time_spent, progress, completed, and failed state BEFORE return
		quest.time_spent = data.get("time_spent", 0.0)
		quest.progress = data.get("progress", 0.0)
		quest.completed = data.get("completed", False)
		quest.failed = data.get("failed", False)
		return quest