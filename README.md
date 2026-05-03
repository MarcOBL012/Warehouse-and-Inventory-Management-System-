# Warehouse and Inventory Management System

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-darkgreen.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)
![Pandas](https://img.shields.io/badge/Data-Pandas-blueviolet.svg)

A 100% offline desktop application designed for advanced inventory control using the **Weighted Average Cost** method. Developed in Python, this tool complies with the structure required by the **Peruvian Tax Authority (SUNAT - Table 12)** for recording operations, ensuring consistency between individual movements and consolidated monthly accounting closures.

## 🚀 Key Features

*   **Real-Time Dashboard:** Instant visualization of the consolidated total value of the inventory at the company level.
*   **Valued Kardex (Average Cost):** Line-by-line algorithmic calculation that revalues the average cost on every inbound movement (purchases, initial balances) and maintains the cost on outbound movements (sales, transfers).
*   **Consolidated Monthly Closure:** Allows filtering by Year/Month to "freeze" and consolidate the inventory of all items across all warehouses, yielding the Consolidated Stock and Global Average Cost.
*   **Multi-Warehouse Management:** Individual stock control by physical locations with support for direct transfers between them.
*   **Professional Excel Export:** Generation of detailed reports in `.xlsx` format (via Pandas and OpenPyXL) ready for accounting reviews or audits.
*   **Modern Dark UI:** Elegant graphical interface built with **CustomTkinter**, providing a native and professional user experience.

## 🛠️ Technologies Used

*   **Backend:** Python 3
*   **Frontend (GUI):** CustomTkinter (Modern Tkinter)
*   **Database:** SQLite (Embedded, 0 configuration)
*   **Data Processing:** Pandas
*   **Packaging:** PyInstaller (Standalone `.exe` generation)

## 📂 Project Structure

```text
📦 Gestion-Almacen-Sercoplus
 ┣ 📜 app.py               # Entry point and main GUI layout
 ┣ 📜 kardex_engine.py     # Logic engine using Pandas for Kardex and Cost calculations
 ┣ 📜 database.py          # SQLite structure definition (DDL Models)
 ┣ 📜 import_csv.py        # Script for bulk injection of real data (CSV)
 ┣ 📜 seed_data.py         # Random mock data generator
 ┣ 📜 inventario.db        # Local database (created automatically)
 ┗ 📜 README.md
```

## ⚙️ Installation and Usage (Development Mode)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Warehouse-and-Inventory-Management-System
   cd Warehouse-and-Inventory-Management-System

   ```
2. Install the required dependencies:
   ```bash
   pip install customtkinter pandas openpyxl
   ```
3. (Optional) If the database is empty, run the import script with your CSVs or the mock data generator:
   ```bash
   python import_csv.py
   ```
4. Start the application:
   ```bash
   python app.py
   ```

