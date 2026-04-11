"""
Mock data for testing: sample Goal and Quests for a Linux exam.
This file exposes `MOCK_GOALS` as a list of dicts. Dates are ISO-8601 strings.
"""
from datetime import datetime

MOCK_GOALS = [
    {
        "exam_name": "Linux System Administrator Certification",
        "exam_subject": "Linux Administration",
        "exam_date": "2026-06-15",
        "hours_willing": 120,
        "themes": ["Shell & Scripting", "Filesystem", "Networking", "Security", "Services"],
        "quests": [
            {
                "name": "Intro to Shell and Navigation",
                "theme": "Shell & Scripting",
                "study_time": 3.0,
                "start": "2026-04-20T18:00:00",
                "end": "2026-04-20T21:00:00",
                "xp_reward": 30,
                "stat_points": {"focus": 1, "speed": 1},
                "progress": 100.0,
                "completed": True,
                "description": "Basic shell commands, file navigation, wildcards, and man pages.",
            },
            {
                "name": "Bash Scripting Fundamentals",
                "theme": "Shell & Scripting",
                "study_time": 5.0,
                "start": "2026-04-22T19:00:00",
                "end": "2026-04-22T22:00:00",
                "xp_reward": 60,
                "stat_points": {"logic": 2, "focus": 1},
                "progress": 40.0,
                "completed": False,
                "description": "Variables, control flow, functions, and small automation scripts.",
            },
            {
                "name": "Filesystem Hierarchy & Permissions",
                "theme": "Filesystem",
                "study_time": 4.0,
                "start": "2026-04-25T17:00:00",
                "end": "2026-04-25T21:00:00",
                "xp_reward": 50,
                "stat_points": {"memory": 1, "focus": 1},
                "progress": 20.0,
                "completed": False,
                "description": "FHS layout, ownership, chmod, chown, ACLs, and special permissions.",
            },
            {
                "name": "Network Configuration Basics",
                "theme": "Networking",
                "study_time": 6.0,
                "start": "2026-05-01T10:00:00",
                "end": "2026-05-01T16:00:00",
                "xp_reward": 80,
                "stat_points": {"networking": 3, "logic": 1},
                "progress": 0.0,
                "completed": False,
                "description": "IP addressing, routing, DNS basics, systemd-networkd and net-tools.",
            },
            {
                "name": "Securing SSH and Services",
                "theme": "Security",
                "study_time": 4.0,
                "start": "2026-05-03T18:00:00",
                "end": "2026-05-03T22:00:00",
                "xp_reward": 70,
                "stat_points": {"security": 3, "focus": 1},
                "progress": 0.0,
                "completed": False,
                "description": "Harden SSH, keys, sshd_config, firewall basics (ufw/iptables), and service hardening.",
            },
            {
                "name": "System Services and Logging",
                "theme": "Services",
                "study_time": 3.0,
                "start": "2026-05-07T14:00:00",
                "end": "2026-05-07T17:00:00",
                "xp_reward": 40,
                "stat_points": {"ops": 2},
                "progress": 0.0,
                "completed": False,
                "description": "systemd units, journalctl, service management, timer units.",
            },
        ],
        "progress": 0.0,
        "completed": False,
    }
]


if __name__ == "__main__":
    import json
    print(json.dumps(MOCK_GOALS, indent=2))
