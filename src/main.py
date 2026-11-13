import click

from cli.outbox import outbox


@click.group()
def cli() -> None:
    pass


cli.add_command(outbox)


if __name__ == "__main__":
    cli()
