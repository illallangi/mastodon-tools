import click
from json import dumps
from tabulate import tabulate

from mastodon_tools.swimmer import MastodonSwimmer


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
        "MastodonSwimmer": MastodonSwimmer(
            email=mastodon_user,
        ),
    }


@cli.command()
@click.pass_context
@click.option(
    "--json",
    is_flag=True,
)
def swims(
    ctx: click.Context,
    json: bool,
):
    if json:
        click.echo(
            dumps(
                {
                    "swims": ctx.obj["MastodonSwimmer"].swims,
                    "statistics": ctx.obj["MastodonSwimmer"].statistics,
                },
                indent=2,
            ),
        )
        return

    swims = ctx.obj["MastodonSwimmer"].swims
    swims.append(
        {
            "date": "Total",
            "distance": ctx.obj["MastodonSwimmer"].statistics["total_distance"],
        },
    )
    swims.append(
        {
            "date": "Remaining",
            "distance": ctx.obj["MastodonSwimmer"].statistics["remaining_distance"],
        },
    )
    swims.append(
        {
            "date": "Remaining Days",
            "distance": ctx.obj["MastodonSwimmer"].statistics["remaining_days"],
        },
    )
    swims.append(
        {
            "date": "Required Average",
            "distance": ctx.obj["MastodonSwimmer"].statistics[
                "required_average_distance"
            ],
            "laps": ctx.obj["MastodonSwimmer"].statistics["required_average_laps"],
        },
    )

    click.echo(
        tabulate(
            swims,
            headers="keys",
        ),
    )


if __name__ == "__main__":
    cli()
