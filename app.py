from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = 'inventory.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Items table
    c.execute('''CREATE TABLE IF NOT EXISTS Items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    quantity INTEGER DEFAULT 0,
                    min_quantity INTEGER DEFAULT 0,
                    unit TEXT,
                    supplier TEXT,
                    location TEXT
                )''')
    # Stock movements table
    c.execute('''CREATE TABLE IF NOT EXISTS StockMovements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    movement_type TEXT,
                    quantity INTEGER,
                    user TEXT,
                    date TEXT,
                    notes TEXT,
                    FOREIGN KEY(item_id) REFERENCES Items(id)
                )''')
    conn.commit()
    conn.close()

# Home / Dashboard
@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Items")
    total_items = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM Items WHERE quantity <= min_quantity")
    low_stock = c.fetchone()[0]
    
    c.execute("SELECT * FROM StockMovements ORDER BY date DESC LIMIT 5")
    recent_movements = c.fetchall()
    conn.close()
    return render_template('dashboard.html', total_items=total_items, low_stock=low_stock, recent_movements=recent_movements)

# Inventory page
@app.route('/inventory')
def inventory():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM Items")
    items = c.fetchall()
    conn.close()
    return render_template('inventory.html', items=items)

# Add new item
@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        quantity = int(request.form['quantity'])
        min_quantity = int(request.form['min_quantity'])
        unit = request.form['unit']
        supplier = request.form['supplier']
        location = request.form['location']

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('INSERT INTO Items (name, category, quantity, min_quantity, unit, supplier, location) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (name, category, quantity, min_quantity, unit, supplier, location))
        conn.commit()
        conn.close()
        return redirect(url_for('inventory'))
    return render_template('add_item.html')

# Stock Movements
@app.route('/movements', methods=['GET', 'POST'])
def movements():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM Items")
    items = c.fetchall()
    
    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        movement_type = request.form['movement_type']
        quantity = int(request.form['quantity'])
        user = request.form['user']
        notes = request.form['notes']
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update item quantity
        if movement_type == 'IN':
            c.execute("UPDATE Items SET quantity = quantity + ? WHERE id = ?", (quantity, item_id))
        else:
            c.execute("UPDATE Items SET quantity = quantity - ? WHERE id = ?", (quantity, item_id))
        
        # Add movement record
        c.execute('INSERT INTO StockMovements (item_id, movement_type, quantity, user, date, notes) VALUES (?, ?, ?, ?, ?, ?)',
                  (item_id, movement_type, quantity, user, date, notes))
        conn.commit()
        return redirect(url_for('movements'))
    
    c.execute("SELECT sm.id, i.name, sm.movement_type, sm.quantity, sm.user, sm.date, sm.notes FROM StockMovements sm JOIN Items i ON sm.item_id = i.id ORDER BY sm.date DESC")
    movements_list = c.fetchall()
    conn.close()
    return render_template('movements.html', items=items, movements_list=movements_list)

if __name__ == '__main__':
    init_db()
    app.run()