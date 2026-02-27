from flask import Flask, render_template, request, jsonify, session
import sqlite3, hashlib, json, random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'techstore_secret_key_2024'
DB_PATH = 'techstore.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def check_pw(pw, h): return hash_pw(pw) == h

def init_db():
    conn = get_db(); c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, phone TEXT, address TEXT, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, brand TEXT, category TEXT, description TEXT, price REAL NOT NULL, stock INTEGER DEFAULT 0, specs TEXT, image_url TEXT, rating REAL DEFAULT 4.0, review_count INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS cart_items (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, total REAL NOT NULL, status TEXT DEFAULT 'confirmed', tracking_number TEXT, address TEXT, payment_method TEXT, estimated_delivery TEXT, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, price REAL NOT NULL);
    ''')
    conn.commit(); conn.close()

def seed_data():
    conn = get_db(); c = conn.cursor()
    if c.execute('SELECT COUNT(*) FROM products').fetchone()[0] > 0:
        conn.close(); return
    products = [
        ('MacBook Pro 16" M3 Max','Apple','laptop','Ultimate professional laptop with M3 Max chip, stunning Liquid Retina XDR display, and all-day battery life.',3499.99,15,json.dumps({'CPU':'Apple M3 Max','RAM':'36GB Unified','Storage':'1TB SSD','Display':'16.2" 3456x2234','Battery':'22hr','OS':'macOS Sonoma'}),'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600',4.9,342),
        ('Dell XPS 15 OLED','Dell','laptop','Premium Windows laptop with stunning OLED display, powerful Intel Core i9, and slim design.',2299.99,20,json.dumps({'CPU':'Intel Core i9-13900H','RAM':'32GB DDR5','Storage':'1TB NVMe SSD','Display':'15.6" 3.5K OLED','GPU':'NVIDIA RTX 4070','OS':'Windows 11 Pro'}),'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600',4.7,218),
        ('Lenovo ThinkPad X1 Carbon','Lenovo','laptop','Ultra-light business powerhouse. Military-grade durability meets enterprise performance.',1849.99,25,json.dumps({'CPU':'Intel Core i7-1365U','RAM':'16GB LPDDR5','Storage':'512GB SSD','Display':'14" 2.8K IPS','Weight':'1.12 kg','OS':'Windows 11 Pro'}),'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600',4.8,491),
        ('ASUS ROG Zephyrus G14','ASUS','laptop','Compact gaming beast with AMD Ryzen 9 and RTX 4090. Dominate any game anywhere.',1999.99,12,json.dumps({'CPU':'AMD Ryzen 9 7940HS','RAM':'32GB DDR5','Storage':'1TB NVMe','Display':'14" 165Hz QHD','GPU':'NVIDIA RTX 4090','OS':'Windows 11 Home'}),'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600',4.8,267),
        ('HP Spectre x360 14','HP','laptop','Elegant 2-in-1 convertible with OLED touch display. Work and create in any mode.',1599.99,18,json.dumps({'CPU':'Intel Core Ultra 7','RAM':'16GB LPDDR5','Storage':'1TB SSD','Display':'14" 2.8K OLED Touch','Battery':'17hr','OS':'Windows 11 Home'}),'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600',4.6,183),
        ('Apple Mac Studio M2 Ultra','Apple','desktop','Extraordinary performance in an impossibly compact design. Built for demanding creative workflows.',3999.99,8,json.dumps({'CPU':'Apple M2 Ultra','RAM':'192GB Unified','Storage':'2TB SSD','GPU':'76-core GPU','Ports':'Thunderbolt 4 x4, USB-A x2, HDMI','OS':'macOS Sonoma'}),'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600',4.9,156),
        ('Custom Gaming PC RTX 4090','TechStore','desktop','Hand-built gaming rig optimized for 4K gaming and content creation. Fully tested and benchmarked.',4299.99,5,json.dumps({'CPU':'Intel Core i9-14900K','RAM':'64GB DDR5-6000','Storage':'2TB NVMe + 4TB HDD','GPU':'NVIDIA RTX 4090 24GB','Cooling':'360mm AIO','OS':'Windows 11 Pro'}),'https://images.unsplash.com/photo-1587831990711-23ca6441447b?w=600',4.9,89),
        ('Dell OptiPlex 7090 Workstation','Dell','desktop','Reliable business desktop for enterprise needs. ISV-certified, highly expandable.',1299.99,30,json.dumps({'CPU':'Intel Core i7-11700','RAM':'16GB DDR4','Storage':'512GB SSD','GPU':'Intel UHD 750','Form Factor':'Small Form Factor','OS':'Windows 11 Pro'}),'https://images.unsplash.com/photo-1547082299-de196ea013d6?w=600',4.5,204),
        ('LG UltraFine 5K Display','LG','accessory','Breathtaking 5K resolution with P3 wide color. The perfect companion for any professional setup.',1299.99,14,json.dumps({'Resolution':'5120x2880','Size':'27"','Panel':'IPS','Refresh':'60Hz','Ports':'Thunderbolt 3, USB-C x2','HDR':'HDR600'}),'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600',4.7,127),
        ('Logitech MX Keys S Combo','Logitech','accessory','Premium wireless keyboard and mouse combo. Works seamlessly across 3 devices.',199.99,50,json.dumps({'Connectivity':'Bluetooth + USB Receiver','Battery':'10-day keyboard, 70-day mouse','Compatibility':'Windows, Mac, Linux','Keys':'Backlit, quiet tactile','Devices':'Up to 3'}),'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600',4.8,893),
        ('Samsung T7 Shield 2TB','Samsung','accessory','Military-grade rugged portable SSD. Blazing fast speeds, IP65 water and dust resistance.',179.99,45,json.dumps({'Capacity':'2TB','Speed':'1050MB/s read','Interface':'USB 3.2 Gen 2','Resistance':'IP65, 3m drop-proof','Weight':'98g'}),'https://images.unsplash.com/photo-1531492746076-161ca9bcad58?w=600',4.7,654),
        ('Laptop Deep Clean & Tune-up','TechStore','service','Complete laptop cleaning, thermal paste replacement, malware removal, and OS optimization.',89.99,99,json.dumps({'Duration':'24-48 hours','Includes':'Interior cleaning, thermal paste, malware scan, OS tune-up','Warranty':'30-day service guarantee','Drop-off':'In-store or mail-in'}),'https://images.unsplash.com/photo-1518770660439-4636190af475?w=600',4.9,412),
        ('Screen Replacement Service','TechStore','service','Cracked or dead display? We replace screens for all major brands with OEM quality parts.',249.99,99,json.dumps({'Duration':'2-4 hours','Brands':'Apple, Dell, HP, Lenovo, ASUS, Samsung','Parts':'OEM quality panels','Warranty':'90-day parts & labor','Estimate':'Free diagnostic'}),'https://images.unsplash.com/photo-1601524909162-ae8725290836?w=600',4.8,287),
        ('Data Recovery Service','TechStore','service','Lost your important files? Our experts recover data from failed drives and corrupted storage.',149.99,99,json.dumps({'Success Rate':'95%+','Media':'HDD, SSD, Flash, RAID','Duration':'1-5 business days','Policy':'No recovery = no charge','Confidentiality':'100% guaranteed'}),'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=600',4.7,198),
    ]
    c.executemany('INSERT INTO products (name,brand,category,description,price,stock,specs,image_url,rating,review_count) VALUES (?,?,?,?,?,?,?,?,?,?)', products)
    c.execute('INSERT INTO users (name,email,password,phone,address) VALUES (?,?,?,?,?)',('Alex Johnson','demo@techstore.com',hash_pw('demo123'),'+1 (555) 012-3456','123 Tech Street, Silicon Valley, CA 94025'))
    did = c.lastrowid
    eta1 = (datetime.utcnow()+timedelta(days=2)).isoformat()
    c1=(datetime.utcnow()-timedelta(days=3)).isoformat()
    c.execute('INSERT INTO orders (user_id,total,status,tracking_number,address,payment_method,estimated_delivery,created_at) VALUES (?,?,?,?,?,?,?,?)',(did,3699.98,'shipped','TRK847392015','123 Tech Street, Silicon Valley, CA 94025','Credit Card',eta1,c1))
    o1=c.lastrowid
    c.execute('INSERT INTO order_items VALUES (NULL,?,1,1,3499.99)',(o1,))
    c.execute('INSERT INTO order_items VALUES (NULL,?,10,1,199.99)',(o1,))
    eta2=(datetime.utcnow()-timedelta(days=1)).isoformat()
    c2=(datetime.utcnow()-timedelta(days=7)).isoformat()
    c.execute('INSERT INTO orders (user_id,total,status,tracking_number,address,payment_method,estimated_delivery,created_at) VALUES (?,?,?,?,?,?,?,?)',(did,89.99,'delivered','TRK521847063','123 Tech Street, Silicon Valley, CA 94025','PayPal',eta2,c2))
    o2=c.lastrowid
    c.execute('INSERT INTO order_items VALUES (NULL,?,12,1,89.99)',(o2,))
    conn.commit(); conn.close()
    print('Seed done! Login: demo@techstore.com / demo123')

@app.route('/') 
def index(): return render_template('index.html')
@app.route('/shop') 
def shop(): return render_template('shop.html')
@app.route('/cart') 
def cart(): return render_template('cart.html') if 'user_id' in session else render_template('index.html')
@app.route('/orders') 
def orders(): return render_template('orders.html') if 'user_id' in session else render_template('index.html')
@app.route('/track/<int:oid>') 
def track(oid): return render_template('track.html', order_id=oid) if 'user_id' in session else render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    d=request.json; conn=get_db()
    if conn.execute('SELECT id FROM users WHERE email=?',(d['email'],)).fetchone():
        conn.close(); return jsonify({'error':'Email already registered'}),400
    conn.execute('INSERT INTO users (name,email,password,phone) VALUES (?,?,?,?)',(d['name'],d['email'],hash_pw(d['password']),d.get('phone','')))
    uid=conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit(); conn.close()
    session['user_id']=uid; session['user_name']=d['name']
    return jsonify({'success':True,'name':d['name']})

@app.route('/api/login', methods=['POST'])
def login():
    d=request.json; conn=get_db()
    u=conn.execute('SELECT * FROM users WHERE email=?',(d['email'],)).fetchone(); conn.close()
    if not u or not check_pw(d['password'],u['password']): return jsonify({'error':'Invalid credentials'}),401
    session['user_id']=u['id']; session['user_name']=u['name']
    return jsonify({'success':True,'name':u['name']})

@app.route('/api/logout',methods=['POST'])
def logout(): session.clear(); return jsonify({'success':True})

@app.route('/api/me')
def me():
    if 'user_id' not in session: return jsonify({'logged_in':False})
    return jsonify({'logged_in':True,'name':session['user_name'],'user_id':session['user_id']})

@app.route('/api/products')
def get_products():
    cat=request.args.get('category','all'); s=request.args.get('search','')
    srt=request.args.get('sort','name'); mn=request.args.get('min_price',0,type=float); mx=request.args.get('max_price',9999999,type=float)
    q='SELECT * FROM products WHERE price>=? AND price<=?'; params=[mn,mx]
    if cat and cat!='all': q+=' AND category=?'; params.append(cat)
    if s: q+=' AND (name LIKE ? OR brand LIKE ? OR description LIKE ?)'; params+=[f'%{s}%']*3
    sm={'price_asc':'price ASC','price_desc':'price DESC','rating':'rating DESC','name':'name ASC'}
    q+=f' ORDER BY {sm.get(srt,"name ASC")}'
    conn=get_db(); rows=conn.execute(q,params).fetchall(); conn.close()
    return jsonify([dp(r) for r in rows])

@app.route('/api/products/<int:pid>')
def get_product(pid):
    conn=get_db(); r=conn.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone(); conn.close()
    return jsonify(dp(r)) if r else (jsonify({'error':'Not found'}),404)

def dp(r): return {'id':r['id'],'name':r['name'],'brand':r['brand'],'category':r['category'],'description':r['description'],'price':r['price'],'stock':r['stock'],'specs':json.loads(r['specs']) if r['specs'] else {},'image_url':r['image_url'],'rating':r['rating'],'review_count':r['review_count']}

@app.route('/api/cart')
def get_cart():
    if 'user_id' not in session: return jsonify([])
    conn=get_db(); rows=conn.execute('SELECT ci.id,ci.quantity,p.id as pid,p.name,p.brand,p.price,p.image_url,p.stock,p.category FROM cart_items ci JOIN products p ON ci.product_id=p.id WHERE ci.user_id=?',(session['user_id'],)).fetchall(); conn.close()
    return jsonify([{'id':r['id'],'quantity':r['quantity'],'product':{'id':r['pid'],'name':r['name'],'brand':r['brand'],'price':r['price'],'image_url':r['image_url'],'stock':r['stock'],'category':r['category']}} for r in rows])

@app.route('/api/cart',methods=['POST'])
def add_cart():
    if 'user_id' not in session: return jsonify({'error':'Login required'}),401
    d=request.json; conn=get_db()
    ex=conn.execute('SELECT id,quantity FROM cart_items WHERE user_id=? AND product_id=?',(session['user_id'],d['product_id'])).fetchone()
    if ex: conn.execute('UPDATE cart_items SET quantity=? WHERE id=?',(ex['quantity']+d.get('quantity',1),ex['id']))
    else: conn.execute('INSERT INTO cart_items (user_id,product_id,quantity) VALUES (?,?,?)',(session['user_id'],d['product_id'],d.get('quantity',1)))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/cart/<int:iid>',methods=['PUT'])
def upd_cart(iid):
    if 'user_id' not in session: return jsonify({'error':'Login required'}),401
    d=request.json; conn=get_db()
    if d['quantity']<=0: conn.execute('DELETE FROM cart_items WHERE id=? AND user_id=?',(iid,session['user_id']))
    else: conn.execute('UPDATE cart_items SET quantity=? WHERE id=? AND user_id=?',(d['quantity'],iid,session['user_id']))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/cart/<int:iid>',methods=['DELETE'])
def del_cart(iid):
    if 'user_id' not in session: return jsonify({'error':'Login required'}),401
    conn=get_db(); conn.execute('DELETE FROM cart_items WHERE id=? AND user_id=?',(iid,session['user_id'])); conn.commit(); conn.close(); return jsonify({'success':True})

STEPS=['confirmed','processing','shipped','out_for_delivery','delivered']

@app.route('/api/orders')
def get_orders():
    if 'user_id' not in session: return jsonify({'error':'Login required'}),401
    conn=get_db(); os=conn.execute('SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall()
    r=[fo(o,conn) for o in os]; conn.close(); return jsonify(r)

@app.route('/api/orders/<int:oid>')
def get_order(oid):
    if 'user_id' not in session: return jsonify({'error':'Login required'}),401
    conn=get_db(); o=conn.execute('SELECT * FROM orders WHERE id=? AND user_id=?',(oid,session['user_id'])).fetchone()
    if not o: conn.close(); return jsonify({'error':'Not found'}),404
    r=fo(o,conn); conn.close(); return jsonify(r)

@app.route('/api/orders',methods=['POST'])
def place_order():
    if 'user_id' not in session: return jsonify({'error':'Login required'}),401
    d=request.json; conn=get_db()
    cart=conn.execute('SELECT ci.id,ci.quantity,p.price,p.id as pid FROM cart_items ci JOIN products p ON ci.product_id=p.id WHERE ci.user_id=?',(session['user_id'],)).fetchall()
    if not cart: conn.close(); return jsonify({'error':'Cart is empty'}),400
    total=sum(r['price']*r['quantity'] for r in cart)
    eta=(datetime.utcnow()+timedelta(days=random.randint(3,7))).isoformat()
    trk='TRK'+str(random.randint(100000000,999999999))
    conn.execute('INSERT INTO orders (user_id,total,status,tracking_number,address,payment_method,estimated_delivery) VALUES (?,?,?,?,?,?,?)',(session['user_id'],total,'confirmed',trk,d.get('address',''),d.get('payment_method','Card'),eta))
    oid=conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    for r in cart:
        conn.execute('INSERT INTO order_items (order_id,product_id,quantity,price) VALUES (?,?,?,?)',(oid,r['pid'],r['quantity'],r['price']))
        conn.execute('UPDATE products SET stock=MAX(0,stock-?) WHERE id=?',(r['quantity'],r['pid']))
        conn.execute('DELETE FROM cart_items WHERE id=?',(r['id'],))
    conn.commit(); conn.close(); return jsonify({'success':True,'order_id':oid,'tracking':trk})

def fo(o,conn):
    items=conn.execute('SELECT oi.quantity,oi.price,p.name,p.brand,p.image_url,p.id as pid FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?',(o['id'],)).fetchall()
    step=STEPS.index(o['status']) if o['status'] in STEPS else 0
    return {'id':o['id'],'total':o['total'],'status':o['status'],'tracking_number':o['tracking_number'],'address':o['address'],'payment_method':o['payment_method'],'estimated_delivery':o['estimated_delivery'],'created_at':o['created_at'],'current_step':step,'items':[{'product_id':r['pid'],'name':r['name'],'brand':r['brand'],'quantity':r['quantity'],'price':r['price'],'image_url':r['image_url']} for r in items]}

# ─── Admin Routes ──────────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return render_template('admin_login.html')
    return render_template('admin.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    d = request.json
    # Simple admin credentials - change in production!
    if d.get('username') == 'admin' and d.get('password') == 'admin123':
        session['is_admin'] = True
        session['admin_name'] = 'Administrator'
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid admin credentials'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_name', None)
    return jsonify({'success': True})

@app.route('/api/admin/products', methods=['GET'])
@admin_required
def admin_get_products():
    conn = get_db()
    rows = conn.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    conn.close()
    return jsonify([dp(r) for r in rows])

@app.route('/api/admin/products', methods=['POST'])
@admin_required
def admin_add_product():
    d = request.json
    specs = json.dumps(d.get('specs', {})) if isinstance(d.get('specs'), dict) else d.get('specs', '{}')
    conn = get_db()
    conn.execute(
        'INSERT INTO products (name,brand,category,description,price,stock,specs,image_url,rating,review_count) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (d['name'], d['brand'], d['category'], d.get('description',''), float(d['price']),
         int(d.get('stock', 0)), specs, d.get('image_url',''), float(d.get('rating', 4.5)), int(d.get('review_count', 0)))
    )
    pid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit(); conn.close()
    return jsonify({'success': True, 'id': pid})

@app.route('/api/admin/products/<int:pid>', methods=['PUT'])
@admin_required
def admin_update_product(pid):
    d = request.json
    specs = json.dumps(d.get('specs', {})) if isinstance(d.get('specs'), dict) else d.get('specs', '{}')
    conn = get_db()
    conn.execute(
        'UPDATE products SET name=?,brand=?,category=?,description=?,price=?,stock=?,specs=?,image_url=?,rating=?,review_count=? WHERE id=?',
        (d['name'], d['brand'], d['category'], d.get('description',''), float(d['price']),
         int(d.get('stock', 0)), specs, d.get('image_url',''), float(d.get('rating', 4.5)),
         int(d.get('review_count', 0)), pid)
    )
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/products/<int:pid>', methods=['DELETE'])
@admin_required
def admin_delete_product(pid):
    conn = get_db()
    # Remove from carts first
    conn.execute('DELETE FROM cart_items WHERE product_id=?', (pid,))
    conn.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/orders', methods=['GET'])
@admin_required
def admin_get_orders():
    conn = get_db()
    os = conn.execute('''
        SELECT o.*, u.name as user_name, u.email as user_email
        FROM orders o JOIN users u ON o.user_id=u.id
        ORDER BY o.created_at DESC
    ''').fetchall()
    result = []
    for o in os:
        items = conn.execute(
            'SELECT oi.quantity,oi.price,p.name,p.brand,p.image_url,p.id as pid FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?',
            (o['id'],)
        ).fetchall()
        step = STEPS.index(o['status']) if o['status'] in STEPS else 0
        result.append({
            'id': o['id'], 'total': o['total'], 'status': o['status'],
            'tracking_number': o['tracking_number'], 'address': o['address'],
            'payment_method': o['payment_method'], 'estimated_delivery': o['estimated_delivery'],
            'created_at': o['created_at'], 'current_step': step,
            'user_name': o['user_name'], 'user_email': o['user_email'],
            'items': [{'product_id':r['pid'],'name':r['name'],'brand':r['brand'],
                       'quantity':r['quantity'],'price':r['price'],'image_url':r['image_url']} for r in items]
        })
    conn.close()
    return jsonify(result)

@app.route('/api/admin/orders/<int:oid>/status', methods=['PUT'])
@admin_required
def admin_update_order_status(oid):
    d = request.json
    new_status = d.get('status')
    if new_status not in STEPS:
        return jsonify({'error': 'Invalid status'}), 400
    conn = get_db()
    conn.execute('UPDATE orders SET status=? WHERE id=?', (new_status, oid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    conn = get_db()
    stats = {
        'total_products': conn.execute('SELECT COUNT(*) FROM products').fetchone()[0],
        'total_orders': conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0],
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_revenue': conn.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='delivered'").fetchone()[0],
        'pending_orders': conn.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('delivered')").fetchone()[0],
        'low_stock': conn.execute("SELECT COUNT(*) FROM products WHERE stock < 5 AND category != 'service'").fetchone()[0],
        'orders_by_status': {}
    }
    for s in STEPS:
        stats['orders_by_status'][s] = conn.execute('SELECT COUNT(*) FROM orders WHERE status=?', (s,)).fetchone()[0]
    conn.close()
    return jsonify(stats)

if __name__=='__main__':
    init_db(); seed_data(); app.run(debug=True,port=5000)
