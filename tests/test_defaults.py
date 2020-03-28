import click_hotoffthehamster


def test_basic_defaults(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--foo", default=42, type=click_hotoffthehamster.FLOAT
    )
    def cli(foo):
        assert type(foo) is float
        click_hotoffthehamster.echo("FOO:[{}]".format(foo))

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "FOO:[42.0]" in result.output


def test_multiple_defaults(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--foo", default=[23, 42], type=click_hotoffthehamster.FLOAT, multiple=True
    )
    def cli(foo):
        for item in foo:
            assert type(item) is float
            click_hotoffthehamster.echo(item)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["23.0", "42.0"]


def test_nargs_plus_multiple(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--arg",
        default=((1, 2), (3, 4)),
        nargs=2,
        multiple=True,
        type=click_hotoffthehamster.INT,
    )
    def cli(arg):
        for item in arg:
            click_hotoffthehamster.echo("<{0[0]:d}|{0[1]:d}>".format(item))

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["<1|2>", "<3|4>"]
