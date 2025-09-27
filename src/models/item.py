from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
import uuid

class Item(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    sub_location = db.Column(db.String(100))  # A上段、B中段1など
    quantity = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)
    
    # 外部キー: 場所への参照
    location_id = db.Column(db.String(36), db.ForeignKey('location.id'), nullable=False)

    def __repr__(self):
        return f'<Item {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sub_location': self.sub_location,
            'quantity': self.quantity,
            'notes': self.notes,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None
        }

