## 0. Prequisites

This section assumes the reader is starting from a new computer and may not already have Python, Node.js, Docker, PostgreSQL, Git, or Visual Studio Code installed.

### Install the prerequisites

Install the following tools before cloning the project.

#### Visual Studio Code

Install Visual Studio Code from the official Visual Studio Code website.

Recommended VS Code extensions:

- Python
- Pylance
- ESLint
- Prettier
- Docker
- PostgreSQL

#### Git

Install Git from the official Git website.

Verify the installation:

```bash
git --version
```
You should see a Git version number.

#### Python

Install Python 3.12 or later from the official Python website.

On Windows, use:
```
python --version
```
Verify pip:
```
python3 -m pip --version
```
On Windows:
```
python -m pip --version
```

#### Node.js and npm

Install the current Node.js Long-Term Support version from the official Node.js website.

npm is installed automatically with Node.js.

Verify both:

```
node --version
npm --version
```
#### Docker Desktop

Install Docker Desktop.

Docker Desktop provides:

Docker Engine
Docker Compose
the PostgreSQL container used by this project

Start Docker Desktop before running any Docker commands.

Verify Docker:
```
docker --version
docker compose version
```
You do not need to install PostgreSQL separately. PostgreSQL runs inside Docker.

#### Clone the repository

Open a terminal and run:
```
git clone <repository-url>
cd adosx-project
```
Open Visual Studio Code manually and select:

File → Open Folder → adosx-project

#### Create the backend environment file

From the project root, copy the example environment file:
```
cp .env.example .env
```
On Windows Command Prompt:
```
copy .env.example .env
```
The .env file contains the local PostgreSQL configuration used by Docker and Django.

Make sure that the file name is .env

#### Start PostgreSQL with Docker

Make sure Docker Desktop is running.

From the project root, run:

```bash
docker compose up -d
```
```
docker compose ps
```
You should see the PostgreSQL service with a status such as:
```
running
```
#### Create a Python virtual environment

A virtual environment keeps this project's Python packages separate from other Python projects.

From the project root:

On macOS or Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```
On Windows PowerShell:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```
On Windows Command Prompt:
```
python -m venv .venv
.venv\Scripts\activate
```
After activation, the terminal should begin with:

(.venv)

Verify the active Python path:

On macOS or Linux:
```
which python
```
On Windows:
```
where python
```
The path should point to the .venv folder inside this project.

Install the backend Python packages

Upgrade pip:
```
python -m pip install --upgrade pip
```
Install all backend dependencies:
```
pip install -r backend/requirements.txt
```
The backend uses the following packages:
```
asgiref==3.12.1
Django==6.0.7
django-cors-headers==4.9.0
djangorestframework==3.17.1
numpy==2.5.1
pandas==3.0.3
psycopg==3.3.4
psycopg-binary==3.3.4
psycopg2-binary==2.9.12
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
six==1.17.0
sqlparse==0.5.5
```
Verify the installations:
```
python -m django --version
python -m pip show djangorestframework
python -m pip show django-cors-headers
python -m pip show psycopg
python -m pip show pandas
```
Verify the main packages:
```
python -m django --version
python -m pip show djangorestframework django-cors-headers psycopg pandas
```
Run the database migrations

Move into the backend directory:
```
cd backend
```
Apply the Django migrations:
```
python manage.py migrate
```
Check the Django configuration:
```
python manage.py check
```
Expected output:
```
System check identified no issues
```
Load and reconcile the CSV files

From the backend directory, run:
```
python manage.py reconcile_csvs \
  ../sample-data/system_a.csv \
  ../sample-data/system_b.csv
```
On Windows Command Prompt, use one line:
```
python manage.py reconcile_csvs ../sample-data/system_a.csv ../sample-data/system_b.csv
```
This command loads both CSV files, normalizes dirty record_ref values, compares System A and System B, ignores valid split entries, and stores the actionable exceptions.


#### Create the demonstration organizations and users

From the backend directory, open the Django shell:
```
python manage.py shell
```
Paste the following code:
```
from django.contrib.auth import get_user_model

from tenants.models import Organization
from users.models import UserProfile


User = get_user_model()


org_a, _ = Organization.objects.get_or_create(
    org_id="ORG-A",
    defaults={"name": "Organization A"},
)

org_b, _ = Organization.objects.get_or_create(
    org_id="ORG-B",
    defaults={"name": "Organization B"},
)


user_a, _ = User.objects.get_or_create(
    username="USER-A",
)

user_a.set_password("test-password-a")  #add your password here
user_a.save()


user_b, _ = User.objects.get_or_create(
    username="USER-B",
)

user_b.set_password("test-password-b")   #add your password here
user_b.save()


UserProfile.objects.update_or_create(
    user=user_a,
    defaults={"organization": org_a},
)

UserProfile.objects.update_or_create(
    user=user_b,
    defaults={"organization": org_b},
)
```
Exit the shell:
```
exit()
```

Demo credentials:
```
Username: USER-A
Password: test-password-a
Organization: ORG-A
Username: USER-B
Password: test-password-b
Organization: ORG-B
```
Username matching is case-insensitive. For example, user-a, User-A, and USER-A all resolve to the stored username USER-A.
### 1. how to run the application

#### Start the Django backend

From the backend directory:
```
python manage.py runserver
```
The backend should be available at:

http://127.0.0.1:8000

Keep this terminal running.


##### Install the frontend packages

Open a second terminal.

From the project root:
```
cd frontend
```
Install all frontend dependencies:
```
npm install
```
This installs the packages listed in package.json and package-lock.json, including React, TypeScript, Vite, React Router, Recharts, Lucide React, and ESLint.

Create the frontend environment file

From the frontend directory:
```
cp .env.example .env.local
```
On Windows Command Prompt:
```
copy .env.example .env.local
```
Confirm that .env.local contains
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```
Start the React frontend

From the frontend directory:
```
npm run dev
```
Vite should display a local URL, normally:
```
http://127.0.0.1:5173
```
Open that URL in a browser.

Both servers must remain running:
```
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

##### Load and reconcile the sample CSV files

From the backend directory, run:
```
python manage.py reconcile_csvs \
  ../sample-data/system_a.csv \
  ../sample-data/system_b.csv
```
On Windows Command Prompt, run the command on one line:
```
python manage.py reconcile_csvs ../sample-data/system_a.csv ../sample-data/system_b.csv
```
The command:

loads System A records
loads System B entries
normalizes dirty record_ref values
groups related System B entries
compares the two systems
ignores valid split entries that reconcile correctly
creates actionable exception records
assigns each exception to the appropriate organization through its location

After reconciliation, the sample data should produce organization-specific exceptions.

#### Run the backend tests

Make sure the Python virtual environment is active.

From the project root:
```
source .venv/bin/activate
cd backend
```
On Windows, activate the environment using the appropriate command shown earlier.

Run the complete backend test suite:
```
python manage.py test -v 2
```
Run only the PostgreSQL tenant-isolation tests:
```
python manage.py test reconciliation.tests.test_rls_isolation -v 2
```
Run the authentication tests:
```
python manage.py test users.tests.test_auth_api -v 2
```
The complete backend suite should finish successfully.

#### Run the frontend checks

From the frontend directory, run the ESLint check:
```
npm run lint
```
Create a production build:
```
npm run build
```
Both commands should finish without errors.

#### Stop the project

Stop the Django and React development servers by pressing:

Control + C

Stop the PostgreSQL container from the project root:

docker compose down

To remove the PostgreSQL data volume and rebuild the database from a completely clean state:

docker compose down -v

The -v option permanently removes the local container database data. Use it only when a complete reset is required.

# Tenant-Safe Reconciliation Exceptions

A narrow end-to-end reconciliation application that compares records from two CSV-based systems, identifies actionable disagreements, enforces organization isolation in PostgreSQL, and exposes the results through an authenticated API and React interface.

The application intentionally focuses on one complete feature:

> A user logs in, belongs to exactly one organization, and sees only the reconciliation exceptions belonging to that organization.



## 2. What I built

The application provides:

- CSV ingestion for System A, System B, and location metadata
- normalization of inconsistent `record_ref` values
- matching of System A records with one or more System B entries
- detection of actionable reconciliation exceptions
- exclusion of legitimate split entries that reconcile correctly
- PostgreSQL Row-Level Security for tenant isolation
- token-based authentication for two demonstration users
- an authenticated exceptions API
- filtering by reason code, record ID, and location ID
- a React dashboard with summary cards, visualizations, filters, and a table
- a grounded question endpoint that cites exception row identifiers
- refusal behavior for questions that cannot be answered from the visible data
- automated tests for reconciliation behavior, API behavior, authentication, and database-enforced tenant isolation

---

## Technology stack

### Backend

- Python
- Django
- Django REST Framework
- PostgreSQL
- PostgreSQL Row-Level Security
- Django REST Framework token authentication

### Frontend

- React
- TypeScript
- Vite
- React Router
- Recharts
- Lucide React

### Local infrastructure

- Docker Compose
- PostgreSQL container

---

## Project structure

```text
adosx-project/
├── backend/
│   ├── config/
│   ├── reconciliation/
│   │   ├── management/commands/reconcile_csvs.py
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── models.py
│   │   ├── qa_service.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   └── views.py
│   ├── tenants/
│   ├── users/
│   ├── manage.py
│   └── requirements.txt
├── docker/
│   └── postgres/init/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
├── sample-data/
│   ├── locations.csv
│   ├── system_a.csv
│   └── system_b.csv
├── compose.yaml
├── DECISIONS.md
└── README.md
```

## 3. What I deliberately did not build

I did not build:

- a file-upload screen for CSV ingestion
- background jobs or scheduled reconciliation
- user registration
- password reset
- multi-role authorization within an organization
- comments, assignments, or approval states
- audit-history screens
- deployment infrastructure
- a full admin portal
- secure HTTP-only cookie authentication

CSV ingestion is performed through a Django management command rather than a user-facing upload workflow.

Authentication is intentionally simple because the brief allowed a hardcoded pair of users with one organization each.



## 4. How I worked with the agent

I used ChatGPT to plan the project, compare architecture options, and break the work into smaller steps. It helped me with repetitive tasks such as API setup, test cases, React components, and documentation. I reviewed the generated code instead of using it directly. A few suggestions were wrong, especially around file replacements and when the tenant-filtered queryset was executed. I found those issues by running tests, checking API responses, and verifying the database results manually. 
