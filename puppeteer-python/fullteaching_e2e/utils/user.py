# -*- coding: utf-8 -*-
"""Test-data user record, ported from utils/User.java."""
from dataclasses import dataclass


@dataclass
class User:
    name: str
    password: str
    role: str

    def get_user_csv(self) -> str:
        return f"{self.name},{self.password},{self.role}"
