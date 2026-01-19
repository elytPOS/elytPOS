# 🌍 Multi-Language Support

elytPOS is designed to be globally accessible, featuring a robust multi-language translation engine specifically for receipt printing. This allows businesses to provide receipts in the local language of their customers while maintaining internal records in their primary operating language.

---

## 🚀 How it Works

The multi-language system operates through a **Language Master** and a **Translation Engine**.

1.  **Define Languages**: Admins/Managers can add any language (e.g., Hindi, Arabic, Spanish) via the **Language Master**.
2.  **Translate Products**: For each language, you can provide translated names for your inventory.
3.  **On-the-Fly Selection**: When saving a bill, the system prompts the operator to select the desired printing language.
4.  **Instant Transformation**: The receipt is generated using the translated names for all items that have a translation available, defaulting to the original name if no translation exists.

---

## 📋 Management Workflow

### 1. Adding a Language
Navigate to `Administration > Language Master`. Here you can define:
- **Language Name**: (e.g., Hindi)
- **Language Code**: (e.g., hi)

### 2. Managing Translations
Once a language is added, use the **Manage Translations** button next to it. This opens a dedicated interface where you can:
- Search for any product in your inventory.
- Enter the name of the product in the target language.
- Save translations individually.

### 3. Printing
Upon clicking **Save (F2)** on the billing screen:
- A dialog will appear listing all configured languages.
- Selecting a language will immediately apply those translations to the generated PDF receipt.
- All totals, shop details, and headers remain consistent, ensuring financial accuracy.

---

## 🛠️ Technical Details

Translations are stored in the `product_translations` table in PostgreSQL, linked to both the `products` and `languages` tables. This relational approach ensures that:
- Deleting a product automatically cleans up its translations.
- Deleting a language removes all associated translated data.
- Inventory search remains fast as translations are only loaded during the printing phase.

---

<p align="center">
  © 2026 Mohammed Adnan. All rights reserved.
</p>
