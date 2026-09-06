# Jjuza DB

**Jjuza DB** is a command-line tool for generating realistic fake data for Microsoft SQL Server databases.

It analyzes your database schema, discovers relationships between tables, determines a safe generation order, generates realistic data using Faker, and inserts the records inside a transaction.

The goal is simple:

> **Populate a development or testing database with realistic data without manually creating records.**

---

## ✨ Features

- 🗄️ **SQL Server support**
- 🔍 **Automatic database schema inspection**
- 🔗 **Foreign key relationship detection**
- 🧠 **Dependency-aware table generation**
- 🧪 **Realistic fake data using Faker**
- 🔑 **Foreign key values generated from existing generated records**
- 🔄 **Many-to-many / pivot table support**
- ♻️ **Unique value generation**
- 📊 **Interactive Rich progress display**
- 👀 **Generation preview before making changes**
- 💾 **Transactional inserts**
- ↩️ **Automatic rollback when generation fails**
- 🆔 **UUID generation**
- 📏 **String length awareness**
- ⚡ **Maximum of 20 records per generation**
- 📦 **Standalone executable releases**
- 🐍 **Python is not required for released executables**

---

## 🧠 How It Works

Jjuza DB doesn't simply generate random records independently for each table.

It first analyzes the database structure.

For example:

```text
users
  │
  ├── profiles
  │
  └── orders
        │
        └── order_items
```

If you request:

```text
order_items → 20 records
```

Jjuza DB understands that `order_items` depends on `orders`, which depends on `users`.

It therefore generates the required parent records first:

```text
users
  ↓
orders
  ↓
order_items
```

This prevents foreign key violations during insertion.

---

## 🔄 Generation Flow

```text
Select database table
        ↓
Select number of records
        ↓
Inspect table schema
        ↓
Discover relationships
        ↓
Build generation plan
        ↓
Show generation preview
        ↓
Confirm
        ↓
BEGIN TRANSACTION
        ↓
Generate dependencies
        ↓
Generate target records
        ↓
COMMIT
```

If something goes wrong:

```text
Generation error
      ↓
ROLLBACK
      ↓
Database remains unchanged
```

---

## 📦 Installation

### Option 1 — Standalone Executable

The recommended way for users is to download the executable from the project's GitHub Releases.

No Python installation is required.

Download the executable for your operating system:

```text
jjuza-db
jjuza-db.exe
```

Then run it from your terminal.

### Option 2 — Python

If you are developing Jjuza DB or want to run it directly from source, Python 3.10+ is required.

Clone the repository:

```bash
git clone https://github.com/<your-username>/jjuza-db.git
cd jjuza-db
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

#### macOS / Linux

```bash
source .venv/bin/activate
```

#### Windows

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run Jjuza DB:

```bash
python -m jjuza_db
```

---

## 🛠️ Requirements

Jjuza DB currently targets:

- Microsoft SQL Server
- Python 3.10+ when running from source
- Microsoft SQL Server ODBC Driver
- A SQL Server database accessible from the machine running Jjuza DB

The standalone executable includes the Python runtime and Python dependencies, but the SQL Server ODBC driver must still be installed on the system.

---

## 🔌 Database Configuration

Jjuza DB accepts a SQLAlchemy SQL Server connection string

Example:

```env
jjuza-db --connection="mssql+pyodbc://sa:password@127.0.0.1:1444/jjuza_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
```

This stores the connection flag in the config of the project so that when u want to perform data generation on the same database, you just call `jjuza-db` command:

```bash
CONNECTION="mssql+pyodbc://sa:password@127.0.0.1:1444/jjuza_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
```

> **Never commit your connection string or database credentials to Git.**

For local development, use an environment file that is excluded from Git.

---

## 🚀 Usage

Start Jjuza DB:

```bash
jjuza-db
```

The CLI will guide you through the process.

### 1. Select a table

Jjuza DB displays the available tables and allows you to select the table you want to populate.

### 2. Choose the number of records

For v1, generation is limited to **20 records per table** .

For example:

```text
How many records?
❯
```

### 3. Schema Analysis

Jjuza DB inspects the selected table and identifies:

- Columns
- Data types
- Primary keys
- Foreign keys
- Nullable columns
- Identity columns
- Default values
- Unique columns
- Composite unique constraints
- String length limits

### 4. Relationship Analysis

Foreign key relationships are analyzed to determine which tables must be generated first.

For example:

```text
orders.user_id → users.id
```

means:

```text
users
  ↓
orders
```

### 5. Generation Preview

Before modifying the database, Jjuza DB shows what it intends to generate.

Example:

```text
Generation Preview

┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Table        ┃ Type       ┃ Records ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
│ users        │ DEPENDENCY │      50 │
│ profiles     │ TARGET     │      50 │
└──────────────┴────────────┴─────────┘

Relationships

  profiles.user_id → users.id
  Constraint: UNIQUE
  Required parents: 50

Total records: 100

⚠ No database changes have been made.

? Proceed with generation?
❯ Yes
  No
```

### 6. Generation

Once confirmed, records are generated and inserted.

Progress is displayed in the terminal:

```text
Generating data...

users        ████████████████████ 20/20
profiles     ████████████████████ 20/20

✓ Transaction committed successfully.
```

---

## 🔗 Foreign Key Support

Jjuza DB uses generated parent records when populating foreign key columns.

For example:

```text
users
-----
id

orders
------
id
user_id → users.id
```

If Jjuza DB generates:

```text
users
1
2
3
```

then generated orders can reference those IDs:

```text
orders

id    user_id
1     2
2     1
3     3
4     2
```

This keeps generated relationships valid.

---

## 🔄 Many-to-Many Relationships

Pivot tables are also supported.

For example:

```text
users
-----
id

groups
------
id

user_groups
-----------
user_id
group_id
```

Jjuza DB generates the parent records first:

```text
users
groups
```

and then generates combinations for:

```text
user_groups
```

When a composite uniqueness constraint exists, duplicate combinations are avoided.

Example:

```text
user_id | group_id
--------|---------
1       | 2
1       | 3
2       | 1
2       | 3
```

The same pair will not be generated twice.

---

## 🆔 UUID Support

Jjuza DB can generate UUID values for application-generated UUID primary keys.

For example, a Django model such as:

```python
id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False,
)
```

may be stored in SQL Server as:

```text
CHAR(32)
```

Jjuza DB can recognize this pattern and generate appropriate UUID values.

---

## 🔑 Primary Keys

Jjuza DB distinguishes between database-generated and application-generated primary keys.

Database-generated keys such as SQL Server `IDENTITY` columns are allowed to be generated by the database.

Application-generated IDs, such as UUIDs, can be generated by Jjuza DB.

Composite primary keys that also act as foreign keys can use IDs from their parent tables.

---

## 🧪 Fake Data Generation

Jjuza DB uses [Faker](https://faker.readthedocs.io/) to generate realistic values.

Examples include:

```text
first_name
last_name
email
phone
address
city
country
date
datetime
integer
decimal
float
boolean
UUID
```

Column names are also used to improve generated values.

For example:

```text
email
```

is more likely to receive:

```text
john.doe@example.com
```

than a completely random string.

---

## 🔐 Transaction Safety

Database changes are performed inside a transaction.

Conceptually:

```text
BEGIN TRANSACTION

Generate users
Generate profiles
Generate orders

        ↓

      SUCCESS
        ↓
     COMMIT
```

If generation fails:

```text
BEGIN TRANSACTION

Generate users
Generate profiles
        ↓
      ERROR
        ↓
    ROLLBACK
```

This prevents partially generated datasets from being left in the database.

---

## ⚠️ Current Limitations

Jjuza DB v1 intentionally keeps the generation engine relatively simple.

Current limitations include:

- SQL Server is the primary supported database.
- Maximum of 20 requested records per generation.
- Complex SQL `CHECK` constraints are not automatically interpreted.
- Some domain-specific validation rules may require future improvements.
- Advanced data dependencies may require additional intelligence in future versions.
- SQL Server's ODBC driver must be installed separately.
- Cyclic relationships require special handling and are not fully generalized in v1.

The goal of v1 is to provide a reliable foundation rather than attempt to solve every possible database-generation problem.

---

## 🏗️ Project Structure

```text
jjuza-db/
│
├── jjuza_db/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── schema.py
│   ├── planner.py
│   ├── generator.py
│   ├── inserter.py
│   └── ui.py
│
├── .github/
│   └── workflows/
│       └── release.yml
│
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore
```

### Module Responsibilities

| Module         | Responsibility                                 |
| -------------- | ---------------------------------------------- |
| `main.py`      | Application entry point                        |
| `config.py`    | Configuration and connection settings          |
| `database.py`  | Database connection and SQL Server interaction |
| `schema.py`    | Database schema inspection                     |
| `planner.py`   | Dependency analysis and generation order       |
| `generator.py` | Fake data generation                           |
| `inserter.py`  | Database inserts                               |
| `ui.py`        | Rich terminal interface                        |

---

## 📦 Building the Executable

Jjuza DB uses PyInstaller to create standalone executables.

Install PyInstaller:

```bash
pip install pyinstaller
```

Build locally:

```bash
pyinstaller --onefile --name jjuza-db jjuza_db/main.py
```

The executable will be placed in:

```text
dist/
└── jjuza-db
```

On Windows:

```text
dist/
└── jjuza-db.exe
```

---

## 🚀 Releases

Standalone builds are produced through GitHub Actions.

A release can contain builds for:

```text
Linux
macOS
Windows
```

For example:

```text
v0.1.0

Assets:
├── jjuza-db-linux.tar.gz
├──jjuza-db-macos.tar.gz
└──jjuza-db.exe
```

Users can download the appropriate executable without installing Python.

### macOS: "Apple could not verify..." warning

Since these builds aren't code-signed with an Apple Developer certificate, macOS will
block the binary the first time you try to run it, with a warning like:

> "jjuza-db" cannot be opened because Apple could not verify it is free of malware.

To run it anyway:

1. Extract the archive:

```bash
   tar -xzf jjuza-db-macos.tar.gz
```

2. Remove the quarantine attribute macOS adds to downloaded files:

```bash
   xattr -d com.apple.quarantine ./jjuza-db
```

3. Make it executable and run it:

```bash
   chmod +x ./jjuza-db
   ./jjuza-db
```

Alternatively, after extracting, right-click (or Control-click) `jjuza-db` in Finder,
choose **Open**, then confirm in the dialog that appears. This only works via
right-click — double-clicking will refuse to open it.

---

## 🤝 Contributing

Contributions are welcome.

To contribute:

1. Fork the repository.
2. Create a branch:

```bash
git checkout -b feature/my-feature
```

3. Make your changes.
4. Test your changes.
5. Commit:

```bash
git commit -m "Add my feature"
```

6. Push the branch:

```bash
git push origin feature/my-feature
```

7. Open a Pull Request.

---

## 🛣️ Roadmap

### v1

- [x] SQL Server schema inspection
- [x] Foreign key discovery
- [x] Dependency ordering
- [x] Fake data generation
- [x] UUID generation
- [x] Unique value handling
- [x] Many-to-many support
- [x] Transaction safety
- [x] Rich CLI interface
- [ ] Automatic first-time setup
- [ ] PyInstaller releases

### Future

Potential future improvements include:

- More database engines
- Better `CHECK` constraint handling
- Smarter domain-specific data generation
- More sophisticated cyclic dependency handling
- Configurable record limits
- Custom data-generation rules
- Seeded/reproducible generation
- Import/export generation configurations
- More advanced CLI commands

---

## 📄 License

This project is licensed under the MIT License.

See `LICENSE` for details.

---

## 👨‍💻 Author

**Kembos**

Jjuza DB is built to make creating realistic development and testing data faster, safer, and less tedious.

> **Generate less manually. Build more.**
