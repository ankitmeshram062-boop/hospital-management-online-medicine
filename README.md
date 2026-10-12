# Hospital Management & Online Medicine Store

## 1. Install
Python 3.11+ and MySQL are recommended.

## 2. Create database
Open MySQL Workbench and run `database.sql`.

## 3. Configure
The local defaults in `config.py` connect to MySQL on `localhost` as `root`.
Override them with `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and
`DB_PASSWORD` environment variables if your local MySQL settings differ.

## 4. Install packages
Windows:
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

## 5. Run
    python app.py

Open:
    http://127.0.0.1:5000

## Deploy to Render
This is a Flask application with a MySQL database; it cannot be deployed as a
static Netlify site without removing the database-backed features. The included
`render.yaml` configures a Render web service. Render does not provide this
project's MySQL database, so create a hosted MySQL database separately.

1. Push the project to a GitHub repository. Keep `venv/` and `.env` out of Git;
   the included `.gitignore` excludes them.
2. Create a hosted MySQL database and run `database.sql` against it.
3. In Render, create a Blueprint from the GitHub repository containing
   `render.yaml`.
4. When prompted, enter the database connection values for `DB_HOST`,
   `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. Render generates
   `SECRET_KEY` for the service.
5. Deploy the service. Open its `onrender.com` URL after the deployment
   succeeds.

For local development, `config.py` continues to use the local MySQL defaults.
Set `SECRET_KEY` and the `DB_*` environment variables in Render; do not put
hosted database credentials in source files.

## Admin
For security, do NOT put a plaintext admin password in the database.
After registering a normal account, promote it to admin in MySQL:
    USE hospital_ecommerce;
    UPDATE users SET role='admin' WHERE email='your-email@example.com';

Then log in again.

## Features
- Patient registration/login
- Doctor listing
- Appointment booking
- Medicine catalogue/search/filter
- Shopping cart
- Checkout and COD/demo payment selection
- Order history
- Admin dashboard
- Admin medicine management
- Admin order status management
- Admin appointment view

## Important
This is an academic project. It is not a production medical/pharmacy system. Real deployment needs secure authentication, CSRF protection, HTTPS, payment integration, prescription verification, audit logs, backups, and compliance with applicable laws.
