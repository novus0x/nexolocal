########## Modules ##########
import subprocess

########## Auto Migrate ##########
def auto_migrate():
    print("Generating migration...")
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", "auto"], check=False)

    print("Applying migration...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    print("Auto-migrations completed.")
