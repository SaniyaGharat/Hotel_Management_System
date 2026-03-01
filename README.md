# 🏨 Hotel Management System

A full-featured web-based Hotel Management System built with **Flask** and **MySQL** for managing hotel operations including rooms, reservations, services, housekeeping, billing, staff, and analytics.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| **Dashboard** | Real-time overview of total rooms, availability, today's check-ins/check-outs, and recent reservations |
| **Room Management** | Add, edit, and track rooms with types (Standard, Deluxe, Suite, Executive) and amenities (WiFi, TV, AC, minibar, jacuzzi, balcony) |
| **Reservations** | Create and manage guest bookings with double-booking prevention, check-in/check-out dates, guest details, and payment tracking |
| **Services** | Manage hotel services (Room Service, Spa, Airport Shuttle, Laundry) and assign service orders to guests |
| **Housekeeping** | Track and update room statuses (Available, Occupied, Maintenance) |
| **Billing** | Generate itemized bills with room charges + service costs, support for multiple payment methods |
| **Staff Management** | Full CRUD for hotel employees — roles (Manager, Receptionist, Housekeeping, Maintenance, Chef, Security), shifts, salary tracking |
| **Reports & Analytics** | Revenue metrics, occupancy rate, monthly revenue chart (Chart.js), room type distribution, reservation breakdown, guest ratings |
| **Guest Directory** | Searchable guest list with stay history, total visits, and spending totals |
| **Notifications** | In-app notification system with bell icon, unread badge, mark-as-read support |
| **Feedback** | Collect guest ratings (1–5) and comments per reservation |
| **Authentication** | Role-based login system (Admin, Receptionist, Staff) with session management |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Charts:** Chart.js
- **Auth:** Session-based with Werkzeug security

---

## 📋 Prerequisites

- **Python 3.8+**
- **MySQL Server 8.0+**

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SaniyaGharat/Hotel_Management_System.git
cd Hotel_Management_System
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit the `.env` file with your MySQL credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=hotel_management3
SECRET_KEY=your_secret_key
```

### 4. Create the Database

Run the SQL file to create the database, tables, and sample data:

```bash
mysql -u root -p < database.sql
```

This creates:
- `hotel_management3` database
- 9 tables: `users`, `rooms`, `reservations`, `services`, `service_orders`, `bills`, `feedback`, `staff`, `notifications`
- Sample data: 7 rooms, 4 services, 5 staff members, and a default admin user

### 5. Run the Application

```bash
python app.py
```

The app will start at **http://127.0.0.1:5000**

---

## 🔑 Default Login

| Field | Value |
|-------|-------|
| Email | `admin@hotel.com` |
| Password | `admin123` |

---

## 📁 Project Structure

```
hotel_management_system/
├── app.py              # Main Flask application (routes & logic)
├── database.sql        # Database schema & sample data
├── requirements.txt    # Python dependencies
├── .env                # Environment configuration
├── templates/          # HTML templates
│   ├── login.html
│   ├── index.html      # Dashboard
│   ├── rooms.html
│   ├── reservations.html
│   ├── services.html
│   ├── housekeeping.html
│   ├── billing.html
│   ├── feedback.html
│   ├── staff.html      # Staff Management
│   ├── reports.html    # Reports & Analytics
│   └── guests.html     # Guest Directory
├── static/
│   ├── css/
│   │   └── styles.css  # Application styles
│   └── js/
│       └── main.js     # Client-side JavaScript
└── README.md
```

---

## 📊 Database Schema

```
users ──────────────── Authentication & roles
rooms ──────────────── Room inventory & status
reservations ───────── Guest bookings (FK → rooms) with double-booking prevention
services ───────────── Available hotel services
service_orders ─────── Service requests (FK → reservations, services)
bills ──────────────── Payment records (FK → reservations)
feedback ───────────── Guest reviews (FK → reservations)
staff ─────────────── Employee records (name, role, shift, salary, status)
notifications ─────── In-app alerts (title, message, type, read status)
```

---

## 🔒 Key Validations

- **Double-booking prevention** — The system checks for overlapping date ranges before allowing a new reservation on any room. Cancelled and checked-out reservations are excluded.
- **Room status sync** — Room status automatically updates to "Occupied" on check-in and "Available" on check-out.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available for educational purposes.