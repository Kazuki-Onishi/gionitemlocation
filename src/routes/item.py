from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.item import Item
from src.models.location import Location

item_bp = Blueprint('item', __name__)

@item_bp.route('/items', methods=['GET'])
def get_items():
    """全てのアイテムを取得（検索機能付き）"""
    search = request.args.get('search', '')
    location_id = request.args.get('location_id', '')
    
    query = Item.query
    
    if search:
        # アイテム名、サブロケーション、備考で検索
        query = query.filter(
            db.or_(
                Item.name.contains(search),
                Item.sub_location.contains(search),
                Item.notes.contains(search)
            )
        )
    
    if location_id:
        query = query.filter_by(location_id=location_id)
    
    items = query.all()
    return jsonify([item.to_dict() for item in items])

@item_bp.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    """特定のアイテムを取得"""
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())

@item_bp.route('/items', methods=['POST'])
def create_item():
    """新しいアイテムを作成"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'location_id' not in data:
        return jsonify({'error': 'Name and location_id are required'}), 400
    
    # 場所が存在するかチェック
    location = Location.query.get(data['location_id'])
    if not location:
        return jsonify({'error': 'Location not found'}), 404
    
    item = Item(
        name=data['name'],
        location_id=data['location_id'],
        sub_location=data.get('sub_location', ''),
        quantity=data.get('quantity', 1),
        notes=data.get('notes', '')
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify(item.to_dict()), 201

@item_bp.route('/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    """アイテムを更新"""
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        item.name = data['name']
    if 'location_id' in data:
        # 場所が存在するかチェック
        location = Location.query.get(data['location_id'])
        if not location:
            return jsonify({'error': 'Location not found'}), 404
        item.location_id = data['location_id']
    if 'sub_location' in data:
        item.sub_location = data['sub_location']
    if 'quantity' in data:
        item.quantity = data['quantity']
    if 'notes' in data:
        item.notes = data['notes']
    
    db.session.commit()
    
    return jsonify(item.to_dict())

@item_bp.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """アイテムを削除"""
    item = Item.query.get_or_404(item_id)
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted successfully'})

@item_bp.route('/search', methods=['GET'])
def search_items():
    """アイテムと場所を横断検索"""
    search = request.args.get('q', '')
    
    if not search:
        return jsonify({'items': [], 'locations': []})
    
    # アイテム検索
    items = Item.query.filter(
        db.or_(
            Item.name.contains(search),
            Item.sub_location.contains(search),
            Item.notes.contains(search)
        )
    ).all()
    
    # 場所検索
    locations = Location.query.filter(
        db.or_(
            Location.name.contains(search),
            Location.description.contains(search)
        )
    ).all()
    
    return jsonify({
        'items': [item.to_dict() for item in items],
        'locations': [location.to_dict() for location in locations]
    })

