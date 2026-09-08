from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Replit Database file
DB_FILE = 'inventory.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {'items': [], 'history': []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    db = load_db()
    role = request.args.get('role', 'employee')
    
    if role == 'admin':
        return jsonify(db['items'])
    else:
        # Werknemers zien alleen naam en huidige hoeveelheid
        return jsonify([{'id': i['id'], 'name': i['name'], 'quantity': i['quantity']} for i in db['items']])

@app.route('/api/items', methods=['POST'])
def add_item():
    db = load_db()
    data = request.json
    
    new_item = {
        'id': int(datetime.now().timestamp() * 1000),
        'name': data['name'],
        'quantity': data['quantity'],
        'minimum': data['minimum'],
        'createdAt': datetime.now().isoformat()
    }
    
    db['items'].append(new_item)
    db['history'].append({
        'action': 'added',
        'product': data['name'],
        'quantity': data['quantity'],
        'by': 'Admin',
        'timestamp': datetime.now().isoformat()
    })
    
    save_db(db)
    return jsonify(new_item), 201

@app.route('/api/delivery', methods=['POST'])
def add_delivery():
    db = load_db()
    data = request.json
    
    item = next((i for i in db['items'] if i['id'] == data['item_id']), None)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    item['quantity'] += data['quantity']
    
    db['history'].append({
        'action': 'delivery',
        'product': item['name'],
        'quantity': data['quantity'],
        'by': 'Admin',
        'timestamp': datetime.now().isoformat()
    })
    
    save_db(db)
    return jsonify(item)

@app.route('/api/checkout', methods=['POST'])
def checkout():
    db = load_db()
    data = request.json
    employee_name = data['employee_name']
    items_taken = data['items']  # [{id: ..., quantity: ...}, ...]
    
    for item_data in items_taken:
        item = next((i for i in db['items'] if i['id'] == item_data['id']), None)
        if item and item_data['quantity'] > 0:
            item['quantity'] = max(0, item['quantity'] - item_data['quantity'])
            
            db['history'].append({
                'action': 'checkout',
                'product': item['name'],
                'quantity': item_data['quantity'],
                'by': employee_name,
                'timestamp': datetime.now().isoformat()
            })
    
    save_db(db)
    return jsonify({'success': True})

@app.route('/api/history', methods=['GET'])
def get_history():
    db = load_db()
    return jsonify(db['history'])

@app.route('/api/item/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    db = load_db()
    db['items'] = [i for i in db['items'] if i['id'] != item_id]
    save_db(db)
    return jsonify({'success': True})

@app.route('/api/item/<int:item_id>/minimum', methods=['PATCH'])
def update_minimum(item_id):
    db = load_db()
    data = request.json
    
    item = next((i for i in db['items'] if i['id'] == item_id), None)
    if item:
        item['minimum'] = data['minimum']
        save_db(db)
        return jsonify(item)
    
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/warnings', methods=['GET'])
def get_warnings():
    db = load_db()
    warnings = [i for i in db['items'] if i['quantity'] <= i['minimum']]
    return jsonify(warnings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
