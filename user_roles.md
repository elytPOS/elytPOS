# 🔐 User Roles & Permissions

elytPOS employs a flexible **Role-Based Access Control (RBAC)** system. While users are assigned a primary role (Admin, Manager, Staff), **individual permissions can be customized** for each user, providing complete control over system access.

---

## 📋 Permission Categories

The system controls access through the following granular permissions:

| Permission Flag | Description |
| :--- | :--- |
| **Billing & Sales** | Create invoices, access the main billing screen. |
| **View Reports** | Access Sales History and Day Book. |
| **Manage Inventory** | Add/Edit items, UOMs, and Languages. Access Recycle Bin. |
| **Manage Customers** | Add/Edit customer details. |
| **Manage Purchases** | Record purchase invoices and view purchase history. |
| **Manage Schemes** | Create and modify promotional schemes. |
| **Manage Users** | Add/Edit system users and assign permissions (Admin only). |
| **System Settings** | Configure Printer and Company details (Admin only). |
| **Database Ops** | Perform backups, restore, and maintenance (Admin only). |

---

## 👤 Role Presets

When creating a user, selecting a role automatically applies a standard set of permissions. You can then fine-tune these checkboxes manually.

### 🛠️ Admin
*   **Default:** All Permissions Enabled.
*   **Focus:** Full system control, configuration, and user management.

### 🏢 Manager
*   **Default:** Billing, Reports, Inventory, Customers, Purchases, Schemes.
*   **Excluded:** User Management, System Settings, Database Ops.
*   **Focus:** Business operations and inventory management.

### 🧑‍💼 Staff
*   **Default:** Billing, Reports.
*   **Excluded:** All Master data management and Admin functions.
*   **Focus:** Fast and secure checkout operations.

---

<p align="center">
  © 2026 Mohammed Adnan. All rights reserved.
</p>
