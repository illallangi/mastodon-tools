import click
from json import dumps
from tabulate import tabulate

from mastodon_tools.user import MastodonUser


@click.group
@click.pass_context
@click.option(
    "--mastodon-user",
    type=click.STRING,
    envvar="MASTODON_USER",
    help="Mastodon User",
    required=True,
)
def cli(
    ctx: click.Context,
    mastodon_user: str,
):
    ctx.obj = {
        "MastodonUser": MastodonUser(
            email=mastodon_user,
        ),
    }


@cli.command()
@click.pass_context
@click.option(
    "--json",
    is_flag=True,
)
def statuses(
    ctx: click.Context,
    json: bool,
):
    if json:
        click.echo(
            dumps(
                {
                    "statuses": ctx.obj["MastodonUser"].statuses,
                },
                indent=2,
            ),
        )
        return

    statuses = ctx.obj["MastodonUser"].statuses

    click.echo(
        tabulate(
            [
                {
                    "id": status["id"],
                    "created_at": status["created_at"],
                    "content": status["content"],
                }
                for status in statuses.values()
            ],
            headers="keys",
        ),
    )


if __name__ == "__main__":
    cli()
