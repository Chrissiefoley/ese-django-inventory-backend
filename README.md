# ESE Inventory Backend

> Django REST API with JWT authentication and role-based access control for inventory management

##  Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security](#security)
- [Technical Decisions](#technical-decisions)
- [AI Statement](#ai-statement)

---

## Architecture

### System Design

```
┌─────────────────────┐
│  Frontend Client    │
│  (React + TypeScript│
│   - Port 3000)      │
└──────────┬──────────┘
           │ REST API calls (Axios)
           │ JWT in httponly cookies
┌──────────┴──────────┐
│   Django Backend    │  
│   REST API          │
│   (Port 8000)       │
└──────────┬──────────┘
           │ Django ORM
┌──────────┴──────────┐
│     Database        │
│ SQLite (Dev)        │
└─────────────────────┘
```

### Authentication Flow

```
1. Registration Flow
   User registers → Backend checks Staff table (employee_id + email)
   ├─ Match found → is_staff_verified = True, role = 'staff' (immediate full access)
   └─ No match → Registration rejected

2. Access Control
   Verified staff users have full CRUD access to inventory
   Admins additionally have user management capabilities
```

**Why Two Layers?**
- **Staff verification** ensures only company employees can register
- **Roles** provide granular permission control within verified users
- **Separation of concerns** - identity verification vs. authorization

### Project Structure

```
backend/
├── authentication/          # User management & JWT auth
│   ├── models.py           # User, Staff, UserInfo models
│   ├── serializers.py      # Registration, profile, validation
│   ├── views.py            # Auth endpoints
│   ├── permissions.py      # IsStaffVerified permission class
│   ├── cookie_views.py     # JWT cookie handlers
│   └── tests.py            # 22 authentication tests
├── inventory/              # Product CRUD operations
│   ├── models.py           # Item model
│   ├── serializers.py      # Item validation
│   ├── views.py            # ItemViewSet with permissions
│   ├── signals.py          # Low stock email alerts
│   └── tests.py            # 8 inventory tests
└── backend/                # Django configuration
    ├── settings.py         # App configuration
    └── urls.py             # API routing
```

**App Separation Rationale:**
- **authentication/** - Reusable auth module (can extract for other projects)
- **inventory/** - Business logic for inventory domain
- **backend/** - Configuration and routing only

---

## 🛠 Tech Stack

### Core Framework
- **Django 6.0.2** - Modern web framework with robust ORM and admin panel
- **Django REST Framework 3.15.2** - RESTful API toolkit (ViewSets, Serializers, Permissions)
- **Python 3.14** - Latest Python with enhanced error messages

### Authentication & Security
- **djangorestframework-simplejwt 5.3.1** - JWT token management (access + refresh tokens)
- **django-cors-headers 4.3.1** - Cross-origin request handling for React frontend
- **Cookie-based JWT storage** - Httponly cookies prevent XSS token theft

### Database
- **SQLite** (Development) - Zero-config, file-based database
- **PostgreSQL** (Production ready) - Can migrate with minimal code changes

### Testing
- **Django TestCase** - Database-backed unit tests
- **APITestCase** - REST API integration tests
- **30 total tests** (22 auth + 8 inventory)

---

## Key Features

### Authentication & Authorization

**Staff Verification System:**
- Registration requires matching Staff table record (employee_id + email)
- Automatic verification on match
- Prevents unauthorised user registration

**JWT Cookie Authentication:**
- Access tokens (2-hour expiry)
- Refresh tokens (7-day expiry)
- Httponly + Secure + SameSite flags
- Automatic token refresh 

### Inventory Management

**CRUD Operations:**
- ✅ Create items with duplicate name prevention
- ✅ Read items with filtering support
- ✅ Update stock counts and product details
- ✅ Delete items with cascade handling

**Business Logic:**
- Unique product names (database constraint)
- Low stock alerts (signals trigger at count < 10)
- Category management with dynamic filtering
- Decimal price handling (10 digits, 2 decimal places)

### Profile Management
- Avatar upload via Cloudinary 
- Contact information editing (max 100 characters)
- Email updates with validation

---

## Getting Started

### Prerequisites

```bash
python3 --version  # Should be 3.14+
pip --version      # pip3 should be available
```

### Installation

```bash
# Navigate to backend directory
cd backend/

# Install dependencies
pip3 install -r requirements.txt
```

**requirements.txt:**
```
Django==6.0.2
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.3.1
python-decouple==3.8
```

### Environment Configuration

Create `.env` in `backend/` directory:

```env
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS Settings (React frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Email Settings (for low stock alerts)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Security Note:**
- Generate a new `SECRET_KEY` for production: `python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- Never commit `.env` to version control

### Database Setup

```bash
# Run migrations
python3 manage.py migrate

# Create superuser for admin panel access
python3 manage.py createsuperuser

# Add staff records (for user verification)
python3 manage.py shell
>>> from authentication.models import Staff
>>> Staff.objects.create(
...     employee_id='EMP001',
...     full_name='John Doe',
...     email='john@company.com'
... )
```

### Run Development Server

```bash
python3 manage.py runserver

# Server runs at: http://localhost:8000
# Admin panel at: http://localhost:8000/admin
# API docs at: http://localhost:8000/api/
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication Endpoints

#### Register New User
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@company.com",
  "password": "SecurePass123",
  "employee_id": "EMP001",
  "contact_info": "+1234567890"
}
```

**Validation Rules:**
- Password: Min 8 chars, uppercase, lowercase, number
- employee_id + email must match Staff table record
- Username must be unique

**Sets Cookies:**
- `access_token` (httponly, secure, samesite=Lax, max_age=7200s)
- `refresh_token` (httponly, secure, samesite=Lax, max_age=604800s)

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123"
}
```

**Response:** Returns user data + sets JWT cookies

#### Logout
```http
POST /api/auth/logout/
Cookie: access_token=...
```

**Response:** Deletes cookies (max_age=0)

#### Refresh Access Token
```http
POST /api/auth/refresh/
Cookie: refresh_token=...
```

**Response:** Issues new access token using valid refresh token

#### Get Current User
```http
GET /api/auth/me/
Cookie: access_token=...
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@company.com",
  "role": "staff",
  "is_staff_verified": true,
  "user_info": {
    "employee_id": "EMP001",
    "contact_info": "+1234567890",
    "avatar": "https://res.cloudinary.com/..."
  }
}
```

#### Update User Profile
```http
PATCH /api/auth/me/
Cookie: access_token=...
Content-Type: application/json

{
  "avatar": "https://res.cloudinary.com/new-avatar.jpg",
  "contact_info": "+44 7700 900123"
}
```

**Validation:**
- Avatar must be Cloudinary URL
- contact_info max 100 characters

---

### Inventory Endpoints

#### List All Items
```http
GET /api/items/
Cookie: access_token=...
```

**Required:** Authenticated + is_staff_verified=True

**Response:**
```json
[
  {
    "id": 1,
    "name": "Laptop",
    "description": "High-performance laptop",
    "category": "Electronics",
    "count": 10,
    "price": "999.99",
    "image": "https://res.cloudinary.com/..."
  }
]
```

#### Create Item
```http
POST /api/items/
Cookie: access_token=...
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

**Required Permission:** is_staff_verified=True

**Validation:**
- Name must be unique
- Price: max 10 digits, 2 decimal places
- Count: integer >= 0

#### Update Item (Partial)
```http
PATCH /api/items/1/
Cookie: access_token=...
Content-Type: application/json

{
  "count": 5
}
```

**Required Permission:** is_staff_verified=True

#### Delete Item
```http
DELETE /api/items/1/
Cookie: access_token=...
```

**Required Permission:** is_staff_verified=True

**Response:** 204 No Content

---

## 🧪 Testing

### Run All Tests
```bash
python3 manage.py test
```

**Output:**
```
Ran 30 tests in 13.5s
OK
```

### Run Specific Test Suites
```bash
# Authentication tests (22 tests)
python3 manage.py test authentication

# Inventory tests (8 tests)
python3 manage.py test inventory
```

### Test Coverage

**Authentication Tests:**
- User registration
- Login/logout JWT cookie handling
- Token refresh 
- Permission checks (IsStaffVerified)
- Cookie security (httponly, secure, max_age)

**Inventory Tests:**
- Item CRUD operations (create, read, update, delete)
- Unique name constraint
- Permission enforcement (unverified users blocked)
- Low stock signal triggers (count < 10)

---

### Permission System

**Custom Permission Class:**
```python
# permissions.py
class IsStaffVerified(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_staff_verified
        )
```

**Result:**
- Unverified users → 403 Forbidden
- Verified users → Access granted
- Enforced at API layer (cannot be bypassed by frontend)

### Input Validation

**Password Validation:**
```python
def validate_password(self, value):
    if len(value) < 8:
        raise ValidationError("Min 8 characters")
    if not any(c.isupper() for c in value):
        raise ValidationError("Must have uppercase letter")
    if not any(c.islower() for c in value):
        raise ValidationError("Must have lowercase letter")
    if not any(c.isdigit() for c in value):
        raise ValidationError("Must have number")
    return value
```

**Database Constraints:**
```python
class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)  - To prevent dupilcates
    price = models.DecimalField(max_digits=10, decimal_places=2)
```
---


### Automatic Verification on Registration

**Decision:** Set `is_staff_verified=True` immediately if Staff match found

**Rationale:**
- Better user experience (no waiting for admin)
- Staff table is the source of truth
- Admin time saved (no manual verification queue)
- Secure (only company employees can register)

**Alternative Considered:** Manual admin approval (rejected - unnecessary bottleneck as alternative found to check database for employee ID and email)


###  Signal-Based Low Stock Alerts

**Decision:** Use Django signals for low stock email notifications

**Rationale:**
- Decoupled from business logic (inventory views don't handle emails)
- Automatic triggers (no manual checks needed)
- Easy to disable (disconnect signal)
- Extensible (add more signals for other events)


---

## AI Statement

### Use of Generative AI Tools

This project was developed with assistance from **Claude Code (Anthropic)/ Windsurf** as a learning and development aid. AI tools were used throughout the development process, primarily for learning and understanding complex concepts included JWT auth/cookie handling, and helping with debugging and test creation. Finally, documentation was enhanced using AI assistance and aided solving linting issues prior to deployment.
It should be noted that all code was reviewed, clarified and understood before being committed.

Through video submission, details of code, architecture and concept implementation is proven. 


**Project Repository:** https://github.com/Chrissiefoley/ese-django-inventory-backend.git
**Frontend Repository:** https://github.com/Chrissiefoley/ese-react-inventory-frontend.git
