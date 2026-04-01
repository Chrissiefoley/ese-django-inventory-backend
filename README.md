# ESE Inventory Backend

> Enterprise inventory management system with two-layer staff verification and role-based access control

## 📋 Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)

---

## 🏗 Architecture

### System Design

**This repository contains the Django REST API backend. The architecture diagram below shows how it fits into the full system:**

```
┌─────────────────────┐
│  Frontend Client    │
│  (React - separate  │
│   repository)       │
└──────────┬──────────┘
           │ REST API Calls
           │ (JWT in HttpOnly Cookies)
┌──────────┴──────────┐
│   Django Backend    │  ← THIS REPOSITORY
│   REST API          │
│   (Port 8000)       │
└──────────┬──────────┘
           │ ORM Queries
┌──────────┴──────────┐
│     Database        │
│ SQLite (Dev) /      │
│ PostgreSQL (Prod)   │
└─────────────────────┘
```

**Authentication Flow:**
```
1. User Registration
   └─> Check Staff whitelist (employee_id + email)
       ├─> Match found: is_staff_verified = True
       └─> No match: is_staff_verified = False

2. Default Role Assignment
   └─> All new users get role = 'viewer'

3. Admin Promotion (via Django Admin)
   └─> Admin manually changes role to 'staff' or 'admin'

4. Access Control (Two Layers)
   └─> Layer 1: Must have is_staff_verified = True
       └─> Layer 2: Role determines permissions
           ├─> viewer: Read-only access
           ├─> staff: Can create/edit/delete
           └─> admin: Full system access
```

**Separation of Concerns:**
- **Authentication App:** User management, staff verification, JWT auth, profile management
- **Inventory App:** Product CRUD, category management, image handling
- **Backend App:** Configuration, URL routing, settings management

### Project Structure

```
backend/
├── authentication/          # User auth, staff verification, JWT
│   ├── models.py           # User, Staff, UserInfo models
│   ├── permissions.py      # Custom permission classes
│   ├── serializers.py      # Registration, profile update
│   └── tests.py            # 34 authentication tests
├── inventory/              # Item CRUD operations
│   ├── models.py           # Item model
│   ├── views.py            # ItemViewSet with permissions
│   └── tests.py            # Inventory tests (TODO)
└── backend/                # Django settings
    ├── settings.py         # Configuration
    └── urls.py             # API routing
```

**Why Separate Apps:**
- **Modularity:** Each app handles one business domain
- **Reusability:** Authentication can be extracted for other projects
- **Maintainability:** Clear boundaries make code easier to understand
- **Testing:** Apps can be tested independently

---

## 🛠 Tech Stack

### Core Framework
- **Django 6.0.2** - Mature, enterprise-grade framework with excellent ORM and admin interface
- **Django REST Framework** - Provides ViewSets (CRUD operations in ~10 lines), Serializers (validation + data transformation), and built-in permission system
- **Python 3.14** - Latest Python version with improved error messages and performance

### Authentication & Security
- **djangorestframework-simplejwt** - JWT token management with access/refresh token pattern
- **django-cors-headers** - Allows React frontend to communicate with Django backend across different ports
- **Cookie-based JWT storage** - HttpOnly cookies prevent XSS attacks by making tokens inaccessible to JavaScript

### Database
- **SQLite** (Development)
- **PostgreSQL** (Production - TODO for deployment)

### Testing
- **Django TestCase** - Unit tests
- **APITestCase** - Integration tests
- **34 passing tests** covering authentication flows

**Test Coverage:** 34 authentication tests covering all critical user flows including registration, login, staff verification, and permission checks

---

## Key Features

### Enterprise Authentication
- User registration with employee verification
- JWT authentication with httponly cookies
- Profile management (avatar upload via Cloudinary)
- Password reset (TODO - assignment requirement)

### 👥 Two-Layer Security Model

**Layer 1: Staff Verification**
```python
# During registration:
is_verified = Staff.objects.filter(
    employee_id=employee_id,
    email=email
).exists()
```

**Layer 2: Role-Based Permissions**
- **Viewer** - Read-only access to inventory
- **Staff** - Create, update, delete products
- **Admin** - Full system access

**Permissions Matrix:**

| Action | Unverified | Viewer | Staff | Admin |
|--------|:----------:|:------:|:-----:|:-----:|
| View inventory | ❌ | ✅ | ✅ | ✅ |
| Create products | ❌ | ❌ | ✅ | ✅ |
| Edit products | ❌ | ❌ | ✅ | ✅ |
| Delete products | ❌ | ❌ | ✅ | ✅ |
| Manage users | ❌ | ❌ | ❌ | ✅ |

### 📦 Inventory Management (CRUD)
- [x] Create products with duplicate name validation
- [x] Read inventory with category filtering
- [x] Update stock counts and product images
- [x] Delete products with confirmation
- [x] Image upload via Cloudinary URLs
- [x] Category management for menu filters

**Key Implementation Details:**
- Duplicate product names are prevented via unique constraint
- Images stored as Cloudinary URLs (no server storage needed)
- Category management uses existing categories with "Add new" option
- Low stock warnings automatically shown for items with count < 10

---

## 🚀 Getting Started

### Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.14+

# Install dependencies
pip install -r requirements.txt
```

**Create `requirements.txt`:**
```
Django==6.0.2
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.3.1
python-decouple==3.8
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000

# TODO: Add database credentials for production
# DATABASE_URL=postgres://...
```

**SECURITY WARNING:** Never commit `.env` to git! Add it to `.gitignore`

### Database Setup

```bash
cd backend/

# Run migrations
python3 manage.py migrate

# Create superuser for admin access
python3 manage.py createsuperuser
```

### Running the Server

```bash
# Development server
python3 manage.py runserver

# Server runs at http://localhost:8000
# Admin panel at http://localhost:8000/admin
```

**Port Configuration:**
- Backend runs on **port 8000** (Django default)
- Frontend runs on **port 3000** (React default)
- Admin panel accessible at http://localhost:8000/admin

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication Endpoints

#### Register
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@company.com",
  "password": "SecurePass123!",
  "employee_id": "EMP001",
  "contact_info": "+1234567890"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@company.com",
    "role": "viewer",
    "is_staff_verified": true,
    "user_info": {
      "employee_id": "EMP001",
      "contact_info": "+1234567890",
      "avatar": ""
    }
  }
}
```

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:** Sets JWT cookies and returns user data

#### Logout
```http
POST /api/auth/logout/
```

**Response:** Deletes JWT cookies

#### Refresh Token
```http
POST /api/auth/refresh/
```

**Response:** Issues new access token using refresh token from cookie

#### Get Current User
```http
GET /api/auth/me/
Authorization: Cookie (access_token)
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@test.com",
  "role": "admin",
  "is_staff_verified": true,
  "user_info": {
    "employee_id": "EMP001",
    "contact_info": "+1234567890",
    "avatar": "https://res.cloudinary.com/..."
  }
}
```

#### Update Profile
```http
PATCH /api/auth/me/
Content-Type: application/json

{
  "avatar": "https://res.cloudinary.com/new-avatar.jpg"
}
```

### Inventory Endpoints

#### List Items
```http
GET /api/items/
Authorization: Cookie (access_token)
```

#### Create Item
```http
POST /api/items/
Authorization: Cookie (access_token)
Content-Type: application/json

{
  "name": "Laptop",
  "description": "High-performance laptop",
  "category": "Electronics",
  "count": 10,
  "price": "999.99",
  "image": "https://res.cloudinary.com/..."
}
```

**Required Permission:** Staff or Admin

#### Get Single Item
```http
GET /api/items/1/
Authorization: Cookie (access_token)
```

#### Update Item
```http
PATCH /api/items/1/
Content-Type: application/json

{
  "count": 5
}
```

**Required Permission:** Staff or Admin

#### Delete Item
```http
DELETE /api/items/1/
```

**Required Permission:** Staff or Admin

---

## 🧪 Testing

### Run All Tests
```bash
python3 manage.py test
```

### Run Specific Test Suites
```bash
# Authentication tests (34 tests)
python3 manage.py test authentication.tests

# Inventory tests
python3 manage.py test inventory.tests
```

### Test Coverage

**Current Test Results:**
- **34 authentication tests** - All passing ✅
- **Coverage:** Authentication flows, staff verification, role permissions
- **Test Categories:**
  - User registration with staff verification
  - Login/logout flows
  - JWT token refresh
  - Profile updates
  - Permission-based access control

### Key Test Cases

**Critical Test Cases Covered:**

1. **Staff Verification Tests:**
   - Matching employee_id + email → User verified ✅
   - Wrong email → User not verified ✅
   - Non-existent employee → User not verified ✅

2. **Permission Tests:**
   - Verified viewer can view inventory ✅
   - Verified viewer cannot create items ✅
   - Verified staff can create items ✅
   - Unverified users blocked from all inventory access ✅

3. **Authentication Tests:**
   - Registration creates user with correct role ✅
   - Login returns JWT cookies ✅
   - Token refresh works with valid cookie ✅
   - Profile updates work for authenticated users ✅

---

## 🚢 Deployment

### Production Checklist

**Production Deployment Checklist:**

1. **Environment Configuration:**
   - [ ] Set `DEBUG=False` in production
   - [ ] Generate new `SECRET_KEY` for production
   - [ ] Configure `ALLOWED_HOSTS` with your domain

2. **Database:**
   - [ ] Migrate from SQLite to PostgreSQL
   - [ ] Run `python manage.py migrate` on production database
   - [ ] Create superuser for production admin access

3. **Security:**
   - [ ] Set up environment variables securely (use platform's secrets)
   - [ ] Configure HTTPS (redirect HTTP to HTTPS)
   - [ ] Update `CORS_ALLOWED_ORIGINS` with production frontend URL
   - [ ] Set secure cookie flags: `SESSION_COOKIE_SECURE = True`

4. **Static Files:**
   - [ ] Run `python manage.py collectstatic`
   - [ ] Configure static file serving (Whitenoise or CDN)

5. **Monitoring:**
   - [ ] Set up error logging (Sentry recommended)
   - [ ] Monitor database connections
   - [ ] Set up health check endpoint

### Deployment Platforms

**Options to consider:**
- **Railway** - Easiest for Django + Postgres
- **Render** - Free tier available
- **Heroku** - Industry standard
- **AWS/GCP** - Enterprise scale

**Recommended Platform: Railway**

**Why Railway:**
- Automatic PostgreSQL provisioning
- Zero-config deployment (detects Django automatically)
- Built-in environment variable management
- Free tier suitable for development/demo
- Easy scaling when needed

**Alternative Options:**
- **Render** - Similar to Railway, good free tier
- **Heroku** - Industry standard but requires credit card
- **AWS/GCP** - Enterprise scale but more complex setup

### Database Migrations in Production

```bash
# CRITICAL: Always backup before migrating
python3 manage.py migrate --check
python3 manage.py migrate
```

---

## 🔒 Security

### Authentication Flow

```
1. User registers with employee_id + email
2. System checks Staff whitelist
3. Sets is_staff_verified = True/False
4. Creates user with role='viewer' (default)
5. Admin manually promotes to 'staff' or 'admin' via Django admin
```

**Authentication Sequence:**
```
User → Frontend: Register with employee_id + email
Frontend → Backend: POST /api/auth/register/
Backend → Staff DB: Query(employee_id, email)
Staff DB → Backend: Match found/not found
Backend: Create User(is_staff_verified=True/False, role='viewer')
Backend → Frontend: Return user data + JWT cookies
Frontend: Store cookies (httponly, automatic)
Frontend: User can login and access based on verification + role
```

### Security Features

- **Two-layer verification** - Must be in Staff whitelist AND have proper role
- **JWT in HttpOnly cookies** - Protection against XSS attacks
- **CORS configuration** - Only allowed origins can access API
- **Unique product names** - Prevents duplicate inventory entries
- **Role-based permissions** - Fine-grained access control

**Security Decision Rationale:**

1. **HttpOnly Cookies for JWT:**
   - **Threat:** XSS attacks can steal tokens from localStorage
   - **Mitigation:** HttpOnly cookies are inaccessible to JavaScript

2. **Two-Layer Verification:**
   - **Threat:** User creates account with fake employee_id
   - **Mitigation:** Must match Staff whitelist to get verified
   - **Threat:** Verified user shouldn't have full access immediately
   - **Mitigation:** Starts as 'viewer', admin promotes manually

3. **Unique Product Names:**
   - **Threat:** Duplicate entries cause inventory confusion
   - **Mitigation:** Database constraint prevents duplicates

4. **CORS Whitelist:**
   - **Threat:** Malicious sites could make requests to your API
   - **Mitigation:** Only allowed origins can access endpoints


---

### Adding New Features

**Example: Adding a new field to Item model**

```python
# 1. Update models.py
class Item(models.Model):
    # ... existing fields
    supplier = models.CharField(max_length=100, blank=True)

# 2. Create migration
python3 manage.py makemigrations

# 3. Apply migration
python3 manage.py migrate

# 4. Update serializer
# 5. Write tests
# 6. Update API documentation
```

Extending the project : 

---

Please note: 
This README was created with assistance from Claude Code (Anthropic) to review the project structure and implementation details.
