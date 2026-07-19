## Django and React instead of a full Next.js application

I used Django for the backend and React with Vite for the frontend instead of building the entire project in Next.js.

Next.js could handle both the UI and API layer, but Django was a better fit for the CSV processing, reconciliation rules, database models, migrations, and automated backend tests. React with Vite kept the frontend simple because the application only needed a small authenticated dashboard.

This also kept the responsibilities clear: Django handles data, security, reconciliation, and APIs, while React handles presentation.


## PostgreSQL in Docker instead of a separate local installation

I ran PostgreSQL in Docker instead of asking each developer to install and configure PostgreSQL directly on their computer.

A local PostgreSQL installation can behave differently across operating systems and may already use conflicting ports, users, or database settings. Docker gives the project a consistent database version and setup, and it can be started or removed with a few commands.


## Token authentication instead of session-based authentication

I used token authentication between the React frontend and Django API instead of Django session authentication.

Since the frontend and backend run as separate applications, tokens made the API flow easier to understand and test. Session authentication would require additional cookie and Cross-Site Request Forgery configuration.
