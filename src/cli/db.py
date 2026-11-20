import shutil
import subprocess
import sys

import click

from config import PROJECT_FOLDER
from core.db.util import write_db_url_alembic_ini


@click.group()
def db():
    """Manages the DB"""
    pass


@db.command(name="create")
def db_create():
    """Creates the Alembic configuration file."""
    fp = PROJECT_FOLDER / "alembic.ini"

    if fp.exists():
        click.echo("alembic.ini already exists")
        return

    try:
        write_db_url_alembic_ini()
        click.echo("Created alembic.ini successfully")
    except Exception as e:
        click.echo(f"Failed to create alembic.ini: {e}", err=True)
        sys.exit(1)


@db.command(name="upgrade")
def db_upgrade():
    """Upgrades the database to the latest migration."""
    fp = PROJECT_FOLDER / "alembic.ini"
    example_fp = PROJECT_FOLDER / "alembic.ini.example"

    if not fp.exists():
        if not example_fp.exists():
            raise FileNotFoundError(
                "Failed to find Alembic configuration file "
                "and the example configuration file"
            )

        try:
            shutil.copyfile(example_fp, fp)
            click.echo("Created alembic.ini from example")
        except OSError as e:
            click.echo(f"Failed to create alembic.ini: {e}", err=True)
            sys.exit(1)

    write_db_url_alembic_ini()

    try:
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            check=True,
            cwd=PROJECT_FOLDER,
        )
        click.echo("Database upgraded successfully")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error upgrading database: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)
