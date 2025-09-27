from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.location import Location
from src.models.item import Item

location_bp = Blueprint('location', __name__)

@location_bp.route('/locations', methods=['GET'])
def get_locations():
    """全ての場所を取得"""
    locations = Location.query.all()
    return jsonify([location.to_dict() for location in locations])

@location_bp.route('/locations/<location_id>', methods=['GET'])
def get_location(location_id):
    """特定の場所とそのアイテムを取得"""
    location = Location.query.get_or_404(location_id)
    items = Item.query.filter_by(location_id=location_id).all()
    
    result = location.to_dict()
    result['items'] = [item.to_dict() for item in items]
    return jsonify(result)

@location_bp.route('/locations', methods=['POST'])
def create_location():
    """新しい場所を作成"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    location = Location(
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(location)
    db.session.commit()
    
    return jsonify(location.to_dict()), 201

@location_bp.route('/locations/<location_id>', methods=['PUT'])
def update_location(location_id):
    """場所を更新"""
    location = Location.query.get_or_404(location_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        location.name = data['name']
    if 'description' in data:
        location.description = data['description']
    
    db.session.commit()
    
    return jsonify(location.to_dict())

@location_bp.route('/locations/<location_id>', methods=['DELETE'])
def delete_location(location_id):
    """場所を削除（関連するアイテムも削除される）"""
    location = Location.query.get_or_404(location_id)
    
    db.session.delete(location)
    db.session.commit()
    
    return jsonify({'message': 'Location deleted successfully'})

