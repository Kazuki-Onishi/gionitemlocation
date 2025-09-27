from flask import Blueprint, request, jsonify
import pandas as pd
import io
from src.models.user import db
from src.models.location import Location
from src.models.item import Item

data_import_bp = Blueprint('data_import', __name__)

@data_import_bp.route('/import/excel', methods=['POST'])
def import_excel():
    """Excelファイルからデータをインポート"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'File must be an Excel file'}), 400
    
    try:
        # Excelファイルを読み込み
        excel_data = pd.read_excel(io.BytesIO(file.read()), sheet_name=None)
        
        imported_locations = 0
        imported_items = 0
        
        for sheet_name, df in excel_data.items():
            # シート1とシート2はスキップ（SNS投稿内容と口コミ）
            if sheet_name in ['シート1', 'シート2']:
                continue
            
            # 場所を作成または取得
            location = Location.query.filter_by(name=sheet_name).first()
            if not location:
                location = Location(name=sheet_name)
                db.session.add(location)
                db.session.commit()
                imported_locations += 1
            
            # データフレームを処理してアイテムを作成
            items_data = parse_sheet_data(df, sheet_name)
            
            for item_data in items_data:
                # 既存のアイテムをチェック
                existing_item = Item.query.filter_by(
                    name=item_data['name'],
                    location_id=location.id,
                    sub_location=item_data['sub_location']
                ).first()
                
                if not existing_item:
                    item = Item(
                        name=item_data['name'],
                        location_id=location.id,
                        sub_location=item_data['sub_location'],
                        notes=item_data.get('notes', '')
                    )
                    db.session.add(item)
                    imported_items += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Import successful',
            'imported_locations': imported_locations,
            'imported_items': imported_items
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Import failed: {str(e)}'}), 500

def parse_sheet_data(df, sheet_name):
    """シートのデータを解析してアイテムリストを返す"""
    items = []
    
    if sheet_name == '3階の物の場所':
        # 3階のデータを解析
        for col in df.columns:
            if pd.isna(col) or col.startswith('Unnamed'):
                continue
            
            sub_location = col
            for idx, value in df[col].items():
                if pd.notna(value) and str(value).strip():
                    items.append({
                        'name': str(value).strip(),
                        'sub_location': sub_location
                    })
    
    elif sheet_name == '1階冷蔵庫、冷凍庫':
        # 1階冷蔵庫・冷凍庫のデータを解析（複雑な構造）
        # セルの内容を文字列として取得し、改行で分割して処理
        for col in df.columns:
            for idx, cell_value in df[col].items():
                if pd.notna(cell_value):
                    parse_complex_cell(str(cell_value), items)
    
    elif sheet_name == '3階靴棚':
        # 3階靴棚のデータを解析
        for col in df.columns:
            for idx, cell_value in df[col].items():
                if pd.notna(cell_value):
                    parse_complex_cell(str(cell_value), items)
    
    elif sheet_name == '階段下など':
        # 階段下のデータを解析
        for col in df.columns:
            for idx, cell_value in df[col].items():
                if pd.notna(cell_value):
                    parse_complex_cell(str(cell_value), items)
    
    return items

def parse_complex_cell(cell_content, items):
    """複雑なセル内容を解析してアイテムを抽出"""
    lines = cell_content.split('\n')
    current_sub_location = ''
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # サブロケーションの判定（A上段、上段、中段1など）
        if any(keyword in line for keyword in ['上段', '中段', '下段', 'A', 'B', 'C', 'D']):
            if len(line) < 20:  # 短い行はサブロケーション
                current_sub_location = line
                continue
        
        # アイテム名の抽出（、で区切られている場合）
        if '、' in line:
            item_names = line.split('、')
            for item_name in item_names:
                item_name = item_name.strip()
                if item_name and not any(keyword in item_name for keyword in ['階', '冷蔵庫', '冷凍庫', '棚']):
                    items.append({
                        'name': item_name,
                        'sub_location': current_sub_location
                    })
        else:
            # 単一のアイテム
            if line and not any(keyword in line for keyword in ['階', '冷蔵庫', '冷凍庫', '棚']):
                items.append({
                    'name': line,
                    'sub_location': current_sub_location
                })

