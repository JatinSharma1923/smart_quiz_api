
# Database Migrations

This project uses **Alembic** to manage SQLAlchemy database schema changes.

## Setup

Install Alembic if not already:

'''bash
pip install alembic
'''
Initialize Alembic:
'''bash
alembic init migrations
'''
Edit alembic.ini and env.py to connect to your DATABASE_URL.
