"""Test-data user record, ported from ``utils/User.java``."""
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """A user of the benchmark data set: e-mail (the login name), password and role."""

    name: str
    password: str
    role: str

    @property
    def is_student(self) -> bool:
        return self.role.strip().upper() == "STUDENT"

    @property
    def is_teacher(self) -> bool:
        return self.role.strip().upper() == "TEACHER"

    def csv(self) -> str:
        return f"{self.name},{self.password},{self.role}"
