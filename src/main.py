import click

from cli.db import db
from cli.moderator import moderator
from cli.outbox import outbox


@click.group()
def cli() -> None:
    pass


cli.add_command(db)
cli.add_command(moderator)
cli.add_command(outbox)


if __name__ == "__main__":
    cli()
