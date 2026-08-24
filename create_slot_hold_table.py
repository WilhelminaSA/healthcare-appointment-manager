from sqlalchemy import inspect

from backend.app import app
from database.database import db


with app.app_context():

    inspector = inspect(db.engine)

    tables = inspector.get_table_names()

    if "slot_holds" in tables:
        print("slot_holds table exists")

        columns = inspector.get_columns("slot_holds")

        print("\nColumns:")

        for column in columns:
            print(
                f"- {column['name']} "
                f"({column['type']})"
            )

    else:
        print("slot_holds table NOT found")