#!/usr/bin/env python3
"""
テスト用データインポートスクリプト
Excelファイルからデータベースにデータを直接インポートします
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from src.models.user import db
from src.models.location import Location
from src.models.item import Item
from src.main import app

def parse_complex_cell(cell_content, items, current_sub_location=''):
    """複雑なセル内容を解析してアイテムを抽出"""
    if pd.isna(cell_content):
        return current_sub_location
    
    lines = str(cell_content).split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # サブロケーションの判定
        if any(keyword in line for keyword in ['上段', '中段', '下段']) and len(line) < 20:
            current_sub_location = line
            continue
        elif line in ['A', 'B', 'C', 'D'] and len(line) == 1:
            current_sub_location = line
            continue
        
        # アイテム名の抽出
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
    
    return current_sub_location

def import_excel_data():
    """Excelファイルからデータをインポート"""
    excel_file = '祇園店googlemap.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"エラー: {excel_file} が見つかりません")
        return
    
    # Excelファイルを読み込み
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    imported_locations = 0
    imported_items = 0
    
    for sheet_name, df in excel_data.items():
        # シート1とシート2はスキップ
        if sheet_name in ['シート1', 'シート2']:
            continue
        
        print(f"処理中: {sheet_name}")
        
        # 場所を作成または取得
        location = Location.query.filter_by(name=sheet_name).first()
        if not location:
            location = Location(name=sheet_name)
            db.session.add(location)
            db.session.commit()
            imported_locations += 1
            print(f"  場所を作成: {sheet_name}")
        
        # データフレームを処理してアイテムを作成
        items_data = []
        
        if sheet_name == '3階の物の場所':
            # 3階のデータを解析
            for col in df.columns:
                if pd.isna(col) or col.startswith('Unnamed'):
                    continue
                
                sub_location = col
                for idx, value in df[col].items():
                    if pd.notna(value) and str(value).strip():
                        items_data.append({
                            'name': str(value).strip(),
                            'sub_location': sub_location
                        })
        
        else:
            # その他のシートの複雑なデータを解析
            current_sub_location = ''
            for col in df.columns:
                for idx, cell_value in df[col].items():
                    if pd.notna(cell_value):
                        current_sub_location = parse_complex_cell(str(cell_value), items_data, current_sub_location)
        
        # アイテムをデータベースに追加
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
                    sub_location=item_data['sub_location']
                )
                db.session.add(item)
                imported_items += 1
        
        print(f"  {len(items_data)}個のアイテムを処理")
    
    db.session.commit()
    
    print(f"\nインポート完了:")
    print(f"場所: {imported_locations}件")
    print(f"アイテム: {imported_items}件")

if __name__ == '__main__':
    with app.app_context():
        import_excel_data()

