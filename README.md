# 🎓 CGC Event Backend

> **Catalyst** — The official event management backend for CGC University Mohali.  
> A lightweight, production-ready REST API powering event discovery, admin control, and live deployments.

---

## 🚀 Live Deployment

| Environment | Status |
|---|---|
| Production | ✅ Active on [Render](https://render.com) |
| Deployments | 12+ successful releases |

---

## 🧬 How This Backend Evolved

This project grew **iteratively**, shaped by real requirements at each phase:

### 🪴 Phase 0 — Foundation
**Commit:** `Initial commit for Render deployment`

The project started with the bare minimum to get something live:
- `app.py` — Flask app skeleton
- `Procfile` — Render deployment config (`web: gunicorn app:app`)
- `requirements.txt` — Dependencies pinned for reproducibility
- Port forced to `8080` to comply with Render's hosting environment

> This phase was purely about **getting infrastructure right** before writing any business logic.

---

### 🏗️ Phase 1 — Core CRUD
**Commit:** `Phase 1: Add backend CRUD endpoints`

The first real feature phase. Full **Create / Read / Update / Delete** endpoints for events were built out:
- `GET /events` — Fetch all events
- `POST /events` — Create a new event
- `PUT /events/<id>` — Update event details
- `DELETE /events/<id>` — Remove an event

> The API became the backbone of the Catalyst frontend at this stage.

---

### 🔐 Phase 2 — Admin Layer & Smart Flags
**Commit:** `add super admin routes + is_featured + is_active`

The most significant evolution. Two categories of upgrades landed together:

**Super Admin Routes**
- Protected endpoints giving admins full control over the event lifecycle
- Separate route namespace for elevated permissions

**Event Flags**
| Flag | Purpose |
|---|---|
| `is_featured` | Marks events to be highlighted/promoted on the frontend |
| `is_active` | Controls whether an event is publicly visible |

> These flags gave the Catalyst Super Admin dashboard (the control panel) real power — admins can now curate what users see without touching the database directly.

---

## 🗂️ Project Structure

```
cgc-event-backend/
├── app.py              # Core Flask application — all routes and logic
├── requirements.txt    # Python dependencies
├── Procfile            # Render deployment entry point
└── .gitignore          # Standard Python ignores
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Flask |
| Server | Gunicorn |
| Hosting | Render |
| Version Control | GitHub |

---

## 🛠️ Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/karan0dev/cgc-event-backend.git
cd cgc-event-backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
python app.py
```

The API will be available at `http://localhost:8080`

---

## 📡 API Overview

### Public Routes
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events` | Get all active events |
| `GET` | `/events/<id>` | Get a single event |
| `GET` | `/events/featured` | Get featured events only |

### Admin Routes
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/events` | Create a new event |
| `PUT` | `/events/<id>` | Update event details |
| `DELETE` | `/events/<id>` | Delete an event |
| `PATCH` | `/events/<id>/feature` | Toggle `is_featured` |
| `PATCH` | `/events/<id>/active` | Toggle `is_active` |

> ⚠️ Admin routes are protected. Ensure proper authentication headers are sent.

---

## 🌱 Roadmap

- [ ] JWT-based authentication for admin routes
- [ ] Event categories & tags
- [ ] Image upload support (Cloudinary / S3)
- [ ] Pagination for event listings
- [ ] Email notifications for event updates

---

## 👤 Author

**Karandeep Singh** — [@karan0dev](https://github.com/karan0dev)  
CGC University Mohali

---

> Built with ☕ and deployed with 🚀 for the Catalyst event platform.