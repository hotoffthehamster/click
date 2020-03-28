# -*- coding: utf-8 -*-
import re

import click_hotoffthehamster


def test_other_command_invoke(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd, arg=42)

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg", type=click_hotoffthehamster.INT)
    def other_cmd(arg):
        click_hotoffthehamster.echo(arg)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "42\n"


def test_other_command_forward(runner):
    cli = click_hotoffthehamster.Group()

    @cli.command()
    @click_hotoffthehamster.option("--count", default=1)
    def test(count):
        click_hotoffthehamster.echo("Count: {:d}".format(count))

    @cli.command()
    @click_hotoffthehamster.option("--count", default=1)
    @click_hotoffthehamster.pass_context
    def dist(ctx, count):
        ctx.forward(test)
        ctx.invoke(test, count=42)

    result = runner.invoke(cli, ["dist"])
    assert not result.exception
    assert result.output == "Count: 1\nCount: 42\n"


def test_auto_shorthelp(runner):
    @click_hotoffthehamster.group()
    def cli():
        pass

    @cli.command()
    def short():
        """This is a short text."""

    @cli.command()
    def special_chars():
        """Login and store the token in ~/.netrc."""

    @cli.command()
    def long():
        """This is a long text that is too long to show as short help
        and will be truncated instead."""

    result = runner.invoke(cli, ["--help"])
    assert (
        re.search(
            r"Usage: cli \[OPTIONS\] COMMAND \[ARGS\]\.\.\.\n\n\s*"
            r"Options:\n\s+"
            r"--help\s+Show this message and exit\.\n\n\s*"
            r"Commands:\n\s+"
            r"long\s+This is a long text that is too long to show as short help"
            r"\.\.\.\n\s+"
            r"short\s+This is a short text\.\n\s+"
            r"special-chars\s+Login and store the token in ~/.netrc\.\s*",
            result.output,
        )
        is not None
    )


def test_no_args_is_help(runner):
    @click_hotoffthehamster.command(no_args_is_help=True)
    def cli():
        pass

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output


def test_default_maps(runner):
    @click_hotoffthehamster.group()
    def cli():
        pass

    @cli.command()
    @click_hotoffthehamster.option("--name", default="normal")
    def foo(name):
        click_hotoffthehamster.echo(name)

    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": "changed"}})

    assert not result.exception
    assert result.output == "changed\n"


def test_group_with_args(runner):
    @click_hotoffthehamster.group()
    @click_hotoffthehamster.argument("obj")
    def cli(obj):
        click_hotoffthehamster.echo("obj={}".format(obj))

    @cli.command()
    def move():
        click_hotoffthehamster.echo("move")

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output

    result = runner.invoke(cli, ["obj1"])
    assert result.exit_code == 2
    assert "Error: Missing command." in result.output

    result = runner.invoke(cli, ["obj1", "--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output

    result = runner.invoke(cli, ["obj1", "move"])
    assert result.exit_code == 0
    assert result.output == "obj=obj1\nmove\n"


def test_base_command(runner):
    import optparse

    @click_hotoffthehamster.group()
    def cli():
        pass

    class OptParseCommand(click_hotoffthehamster.BaseCommand):
        def __init__(self, name, parser, callback):
            click_hotoffthehamster.BaseCommand.__init__(self, name)
            self.parser = parser
            self.callback = callback

        def parse_args(self, ctx, args):
            try:
                opts, args = parser.parse_args(args)
            except Exception as e:
                ctx.fail(str(e))
            ctx.args = args
            ctx.params = vars(opts)

        def get_usage(self, ctx):
            return self.parser.get_usage()

        def get_help(self, ctx):
            return self.parser.format_help()

        def invoke(self, ctx):
            ctx.invoke(self.callback, ctx.args, **ctx.params)

    parser = optparse.OptionParser(usage="Usage: foo test [OPTIONS]")
    parser.add_option(
        "-f", "--file", dest="filename", help="write report to FILE", metavar="FILE"
    )
    parser.add_option(
        "-q",
        "--quiet",
        action="store_false",
        dest="verbose",
        default=True,
        help="don't print status messages to stdout",
    )

    def test_callback(args, filename, verbose):
        click_hotoffthehamster.echo(" ".join(args))
        click_hotoffthehamster.echo(filename)
        click_hotoffthehamster.echo(verbose)

    cli.add_command(OptParseCommand("test", parser, test_callback))

    result = runner.invoke(
        cli, ["test", "-f", "test.txt", "-q", "whatever.txt", "whateverelse.txt"]
    )
    assert not result.exception
    assert result.output.splitlines() == [
        "whatever.txt whateverelse.txt",
        "test.txt",
        "False",
    ]

    result = runner.invoke(cli, ["test", "--help"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo test [OPTIONS]",
        "",
        "Options:",
        "  -h, --help            show this help message and exit",
        "  -f FILE, --file=FILE  write report to FILE",
        "  -q, --quiet           don't print status messages to stdout",
    ]


def test_object_propagation(runner):
    for chain in False, True:

        @click_hotoffthehamster.group(chain=chain)
        @click_hotoffthehamster.option("--debug/--no-debug", default=False)
        @click_hotoffthehamster.pass_context
        def cli(ctx, debug):
            if ctx.obj is None:
                ctx.obj = {}
            ctx.obj["DEBUG"] = debug

        @cli.command()
        @click_hotoffthehamster.pass_context
        def sync(ctx):
            click_hotoffthehamster.echo(
                "Debug is {}".format("on" if ctx.obj["DEBUG"] else "off")
            )

        result = runner.invoke(cli, ["sync"])
        assert result.exception is None
        assert result.output == "Debug is off\n"


def test_other_command_invoke_with_defaults(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd)

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", type=click_hotoffthehamster.INT, default=42)
    @click_hotoffthehamster.pass_context
    def other_cmd(ctx, foo):
        assert ctx.info_name == "other-cmd"
        click_hotoffthehamster.echo(foo)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "42\n"


def test_invoked_subcommand(runner):
    @click_hotoffthehamster.group(invoke_without_command=True)
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click_hotoffthehamster.echo("no subcommand, use default")
            ctx.invoke(sync)
        else:
            click_hotoffthehamster.echo("invoke subcommand")

    @cli.command()
    def sync():
        click_hotoffthehamster.echo("in subcommand")

    result = runner.invoke(cli, ["sync"])
    assert not result.exception
    assert result.output == "invoke subcommand\nin subcommand\n"

    result = runner.invoke(cli)
    assert not result.exception
    assert result.output == "no subcommand, use default\nin subcommand\n"


def test_unprocessed_options(runner):
    @click_hotoffthehamster.command(context_settings=dict(ignore_unknown_options=True))
    @click_hotoffthehamster.argument(
        "args", nargs=-1, type=click_hotoffthehamster.UNPROCESSED
    )
    @click_hotoffthehamster.option("--verbose", "-v", count=True)
    def cli(verbose, args):
        click_hotoffthehamster.echo("Verbosity: {}".format(verbose))
        click_hotoffthehamster.echo("Args: {}".format("|".join(args)))

    result = runner.invoke(cli, ["-foo", "-vvvvx", "--muhaha", "x", "y", "-x"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Verbosity: 4",
        "Args: -foo|-x|--muhaha|x|y|-x",
    ]


def test_deprecated_in_help_messages(runner):
    @click_hotoffthehamster.command(deprecated=True)
    def cmd_with_help():
        """CLI HELP"""
        pass

    result = runner.invoke(cmd_with_help, ["--help"])
    assert "(DEPRECATED)" in result.output

    @click_hotoffthehamster.command(deprecated=True)
    def cmd_without_help():
        pass

    result = runner.invoke(cmd_without_help, ["--help"])
    assert "(DEPRECATED)" in result.output


def test_deprecated_in_invocation(runner):
    @click_hotoffthehamster.command(deprecated=True)
    def deprecated_cmd():
        pass

    result = runner.invoke(deprecated_cmd)
    assert "DeprecationWarning:" in result.output
