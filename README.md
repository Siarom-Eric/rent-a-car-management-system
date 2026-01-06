# Rent-a-Car Management System

## 📌 Overview
This project is a desktop-based rent-a-car management system developed as an academic project.  
It focuses on managing vehicles, clients, reservations and payment methods, supported by an SQLite database and a graphical user interface built with Tkinter.

The system simulates real-world rent-a-car operations by combining persistent data storage, business rules for fleet availability and maintenance, and visual dashboards.

---

## 🎯 Project Goals
- Centralize the management of vehicles, clients and reservations
- Control vehicle availability based on reservations and maintenance status
- Provide operational and financial insights through dashboards
- Automate alerts for upcoming vehicle maintenance and inspections

---

## 🧩 Core Features

### CRUD Management
- Vehicles
- Clients
- Reservations
- Users
- Payment methods

### User Authentication
- User login
- User registration  
*(No role-based access; all users have the same permissions)*

### Data Export
- Export data to:
  - CSV
  - Excel
- Supported entities:
  - Vehicles
  - Clients
  - Reservations
  - Payment methods

---

## 📊 Dashboard & Reports
The initial dashboard is displayed immediately after user login and includes:

- Currently rented vehicles and remaining reservation days
- Recently registered clients
- Available vehicles grouped by type and category
- Monthly reservations and total financial value
- Vehicles with upcoming:
  - Maintenance (within 15 days)
  - Mandatory inspection (within 15 days)

---

## ⚙️ Business Rules
- Vehicles marked as **under maintenance** become unavailable for rental
- Automatic maintenance alert shown as a **popup**:
  - Triggered **5 days before** the next scheduled maintenance date
  - Displayed when the user logs in and the dashboard loads
- Vehicle availability is determined by:
  - Active reservations
  - Maintenance status

---

## 🗄️ Database Design
The system uses an **SQLite** relational database.

### Main Tables
- Users
- Vehicles
- Clients
- Reservations
- Payment Methods

### Vehicle Data Includes
- Brand and model
- Category and vehicle type
- Transmission
- Passenger capacity
- Daily rental price
- Vehicle image path
- Dates of:
  - Last maintenance
  - Next scheduled maintenance
  - Last mandatory inspection

> Database structure and tables are created and managed directly through the application logic (no standalone SQL script files).

---

## 🖥️ User Interface
The application is a **desktop-only system** built with **Tkinter**, providing:
- Windows, buttons and form-based interfaces
- Data entry and management screens
- Integrated dashboard view

### UI Enhancements
- **Tkcalendar** for intuitive and user-friendly date selection widgets
- **Matplotlib** for charts and graphical reports displayed in the dashboard

---

## 🧰 Technologies Used
- **Python**
- **Tkinter** (GUI)
- **Matplotlib** (Charts and dashboards)
- **Tkcalendar** (Date selection widgets)
- **SQLite** (Relational database)
- CSV / Excel export utilities

**Development environment:**  
PyCharm

---

## 🚀 Project Status
Completed academic project.

Potential future improvements:
- Role-based access control
- Improved validation and error handling
- Migration to a web-based application
- REST API integration
- Cloud deployment

---

## 👤 Author
Eric Morais