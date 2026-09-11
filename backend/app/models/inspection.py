from datetime import datetime
from bson import ObjectId


class Inspection:
    def __init__(
        self,
        image_path: str,
        user_id: str,
        category: str = None,
        status: str = "uploaded",
        result: str = None,
        anomaly_score: str = None,
        threshold: float = None,
        id=None,
        created_at=None
    ):
        self.id = str(id) if id else str(ObjectId())
        self.image_path = image_path
        self.category = category
        self.status = status
        self.result = result
        self.anomaly_score = anomaly_score
        self.threshold = threshold
        self.user_id = str(user_id)
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "image_path": self.image_path,
            "category": self.category,
            "status": self.status,
            "result": self.result,
            "anomaly_score": self.anomaly_score,
            "threshold": self.threshold,
            "user_id": self.user_id,
            "created_at": self.created_at
        }

    def to_response_dict(self):
        return {
            "id": self.id,
            "image_path": self.image_path,
            "category": self.category,
            "status": self.status,
            "result": self.result,
            "anomaly_score": self.anomaly_score,
            "threshold": self.threshold,
            "user_id": self.user_id,
            "created_at": self.created_at
        }