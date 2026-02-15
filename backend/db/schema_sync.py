########## Modules ##########
import db.model

from sqlalchemy import inspect
from sqlalchemy.sql.ddl import DDL

from db.database import engine, Base

########## Helper ##########
def normalize_type(t: str) -> str:
    t = t.lower()

    if "timestamp" in t or "datetime" in t:
        return "datetime"

    if "numeric" in t or "decimal" in t:
        return "numeric"

    return t

########## Sync Schema ##########
def sync_schema():
    warnings = []

    with engine.begin() as conn:
        print("[SCHEMA] Creating missing tables (if any)")
        Base.metadata.create_all(bind=conn)

    inspector = inspect(engine)

    with engine.begin() as conn:

        model_tables = set(Base.metadata.tables.keys())
        db_tables = set(inspector.get_table_names())

        for db_table in db_tables:
            if db_table not in model_tables:
                warnings.append(
                    f"[EXTRA TABLE] {db_table} "
                    "(exists in DB but not in models)"
                )

        for table in Base.metadata.tables.values():
            if not inspector.has_table(table.name):
                continue 

            db_columns = {
                col["name"]: col for col in inspector.get_columns(table.name)
            }

            model_column_names = {c.name for c in table.columns}

            for db_column_name in db_columns.keys():
                if db_column_name not in model_column_names:
                    warnings.append(
                        f"[EXTRA COLUMN] {table.name}.{db_column_name} "
                        "(exists in DB but not in model)"
                    )

            for column in table.columns:
                if column.name not in db_columns:
                    if not column.nullable and column.default is None and column.server_default is None:
                        warnings.append(
                            f"[SKIP COLUMN] {table.name}.{column.name} "
                            "(NOT NULL without default)"
                        )
                        continue

                    column_ddl = column.type.compile(dialect=engine.dialect)

                    ddl = DDL(
                        f"ALTER TABLE {table.name} "
                        f"ADD COLUMN {column.name} {column_ddl}"
                    )

                    conn.execute(ddl)
                    print(f"[ADD COLUMN] {table.name}.{column.name}")

                else:
                    db_col = db_columns[column.name]

                    model_type = str(column.type)
                    db_type = str(db_col["type"])

                    if normalize_type(model_type) != normalize_type(db_type):
                        warnings.append(
                            f"[TYPE CHANGE] {table.name}.{column.name} "
                            f"DB={db_type} → MODEL={model_type}"
                        )

                    if column.nullable != db_col["nullable"]:
                        warnings.append(
                            f"[NULLABLE CHANGE] {table.name}.{column.name} "
                            f"DB={db_col['nullable']} → MODEL={column.nullable}"
                        )

    print("\n=== SCHEMA SYNC REPORT ===")
    if not warnings:
        print("[+] Schema is in sync")
    else:
        print("[!] Manual review required:")
        for w in warnings:
            print(" -", w)
    print("==========================\n")


if __name__ == "__main__":
    sync_schema()
