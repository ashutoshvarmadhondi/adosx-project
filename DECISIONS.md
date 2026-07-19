# Decisions

## 1. Django and React instead of a full Next.js application

**Decision:** Use Django for the backend and React with Vite for the frontend.

**Rejected alternative:** Build the complete application in Next.js.

**Reason:** Django was a better fit for CSV processing, database models, migrations, reconciliation logic, and backend testing, while React kept the dashboard simple.

---

## 2. PostgreSQL in Docker instead of a separate local installation

**Decision:** Run PostgreSQL using Docker Compose.

**Rejected alternative:** Ask each developer to install and configure PostgreSQL directly on their computer.

**Reason:** Docker provides the same database version and configuration across different machines and avoids local port or setup conflicts.

---

## 3. Token authentication instead of session authentication

**Decision:** Use token authentication between the React frontend and Django API.

**Rejected alternative:** Use Django session and cookie-based authentication.

**Reason:** Tokens were simpler for two separately running applications and avoided additional cookie and CSRF configuration.

---

## 4. Reconciliation logic in a service layer

**Decision:** Keep CSV parsing, normalization, and reconciliation rules in separate service files.

**Rejected alternative:** Write the reconciliation logic directly inside Django API views.

**Reason:** Separating the business logic made it easier to test and kept the API views focused on requests and responses.

---

## 5. Management command instead of a CSV upload screen

**Decision:** Run CSV ingestion and reconciliation through a Django management command.

**Rejected alternative:** Build a frontend upload page with background processing.

**Reason:** A command-line workflow was enough for the assignment and allowed more time to focus on reconciliation accuracy and tenant isolation.
