from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
import uuid

class Location(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # リレーション: 1つの場所に複数のアイテム
    items = db.relationship('Item', backref='location', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Location {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'items_count': len(self.items)
        }

