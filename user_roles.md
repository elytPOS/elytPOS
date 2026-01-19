# 🔐 User Roles & Permissions

elytPOS employs a granular **Role-Based Access Control (RBAC)** system to ensure security and operational efficiency. Each user is assigned one of three specific roles, each with a defined set of permissions.

---

## 📋 Role Matrix

| Feature | Staff | Manager | Admin |
| :--- | :---: | :---: | :---: |
| **Billing & Invoicing** | ✅ | ✅ | ✅ |
| **Product Search** | ✅ | ✅ | ✅ |
| **Integrated Calculator** | ✅ | ✅ | ✅ |
| **Sales History (View)** | ✅ | ✅ | ✅ |
| **Customer Master** | ❌ | ✅ | ✅ |
| **Item Master (Inventory)** | ❌ | ✅ | ✅ |
| **Purchase Management** | ❌ | ✅ | ✅ |
| **Scheme Management** | ❌ | ✅ | ✅ |
| **UOM & Language Master** | ❌ | ✅ | ✅ |
| **User Management** | ❌ | ❌ | ✅ |
| **Printer Settings** | ❌ | ❌ | ✅ |
| **Database Maintenance** | ❌ | ❌ | ✅ |
| **Recycle Bin Access** | ❌ | ❌ | ✅ |

---

## 👤 Role Descriptions

### 🛠️ Admin
The **Admin** has unrestricted access to the entire system. This role is responsible for core configuration, managing other users, adjusting printer settings, and performing database maintenance (backups, purges, etc.).

### 🏢 Manager
The **Manager** is designed for supervisors who need to manage inventory and business logic. They can add/edit products, manage promotional schemes, record purchases from suppliers, and maintain the customer database. They *cannot* access system settings or user management.

### 🧑‍💼 Staff
The **Staff** role is optimized for front-line cashiers. Access is restricted to essential sales functions: creating bills, searching for products, viewing transaction history, and using the built-in calculator. This ensures a focused and secure environment for daily operations.

---

<p align="center">
  © 2026 Mohammed Adnan. All rights reserved.
</p>
