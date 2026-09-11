from datetime import datetime
from bson import ObjectId


class User:
    def __init__(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str,
        id=None,
        created_at=None
    ):
        self.id = str(id) if id else str(ObjectId())
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "created_at": self.created_at
        }

    def to_response_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role
        }