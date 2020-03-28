import click_hotoffthehamster


CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())


def test_option_normalization(runner):
    @click_hotoffthehamster.command(context_settings=CONTEXT_SETTINGS)
    @click_hotoffthehamster.option("--foo")
    @click_hotoffthehamster.option("-x")
    def cli(foo, x):
        click_hotoffthehamster.echo(foo)
        click_hotoffthehamster.echo(x)

    result = runner.invoke(cli, ["--FOO", "42", "-X", 23])
    assert result.output == "42\n23\n"


def test_choice_normalization(runner):
    @click_hotoffthehamster.command(context_settings=CONTEXT_SETTINGS)
    @click_hotoffthehamster.option(
        "--choice", type=click_hotoffthehamster.Choice(["Foo", "Bar"])
    )
    def cli(choice):
        click_hotoffthehamster.echo(choice)

    result = runner.invoke(cli, ["--CHOICE", "FOO"])
    assert result.output == "Foo\n"


def test_command_normalization(runner):
    @click_hotoffthehamster.group(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

    @cli.command()
    def foo():
        click_hotoffthehamster.echo("here!")

    result = runner.invoke(cli, ["FOO"])
    assert result.output == "here!\n"
