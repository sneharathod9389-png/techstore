# TechStore — Full Stack Web Application

A full-featured e-commerce platform for computers, laptops, and repair services.

## Tech Stack
- **Backend**: Python Flask
- **Database**: SQLite (development) / MySQL (production)
- **Frontend**: Vanilla JS, HTML5, CSS3 — no heavy frameworks needed

## Features
- 🔐 **Auth**: Register, login, logout with hashed passwords
- 🛍️ **Shop**: Browse by category, search, filter by price, sort by rating/price
- 🛒 **Cart**: Add items, update quantities, remove items
- 📦 **Orders**: Place orders with delivery address & payment selection
- 🚚 **Tracking**: Live order status with step-by-step progress, ETA
- 📱 **Responsive**: Works on mobile, tablet, and desktop

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app (auto-seeds demo data)
python app.py

# 3. Open browser
http://localhost:5000
```

## Demo Login
- **Email**: demo@techstore.com
- **Password**: demo123

## Switch to MySQL

Edit `app.py` line ~15:
```python
# Replace SQLite line with:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://USER:PASSWORD@HOST/techstore'
```

Create the MySQL database:
```sql
CREATE DATABASE techstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Project Structure
```
techstore/
├── app.py                  # Flask app, models, routes, API
├── requirements.txt
├── templates/
│   ├── base.html           # Navbar, auth modal, layout
│   ├── index.html          # Landing page
│   ├── shop.html           # Product catalog with filters
│   ├── cart.html           # Shopping cart + checkout
│   ├── orders.html         # Order history
│   └── track.html          # Order tracking
└── static/
    ├── css/style.css       # All styles
    └── js/app.js           # Auth, cart, UI logic
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/register | Create account |
| POST | /api/login | Sign in |
| POST | /api/logout | Sign out |
| GET | /api/me | Current user info |
| GET | /api/products | List products (with filters) |
| GET | /api/products/:id | Single product |
| GET | /api/cart | Get cart |
| POST | /api/cart | Add to cart |
| PUT | /api/cart/:id | Update quantity |
| DELETE | /api/cart/:id | Remove item |
| GET | /api/orders | Order history |
| GET | /api/orders/:id | Single order |
| POST | /api/orders | Place order |
