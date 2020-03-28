# -*- coding: utf-8 -*-
import click_hotoffthehamster


def test_basic_functionality(runner):
    @click_hotoffthehamster.command()
    def cli():
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.

        \b
        This is
        a paragraph
        without rewrapping.

        \b
        1
         2
          3

        And this is a paragraph
        that will be rewrapped again.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  First paragraph.",
        "",
        "  This is a very long second paragraph and not correctly",
        "  wrapped but it will be rewrapped.",
        "",
        "  This is",
        "  a paragraph",
        "  without rewrapping.",
        "",
        "  1",
        "   2",
        "    3",
        "",
        "  And this is a paragraph that will be rewrapped again.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_wrapping_long_options_strings(runner):
    @click_hotoffthehamster.group()
    def cli():
        """Top level command
        """

    @cli.group()
    def a_very_long():
        """Second level
        """

    @a_very_long.command()
    @click_hotoffthehamster.argument("first")
    @click_hotoffthehamster.argument("second")
    @click_hotoffthehamster.argument("third")
    @click_hotoffthehamster.argument("fourth")
    @click_hotoffthehamster.argument("fifth")
    @click_hotoffthehamster.argument("sixth")
    def command():
        """A command.
        """

    # 54 is chosen as a length where the second line is one character
    # longer than the maximum length.
    result = runner.invoke(cli, ["a-very-long", "command", "--help"], terminal_width=54)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli a-very-long command [OPTIONS] FIRST SECOND",
        "                               THIRD FOURTH FIFTH",
        "                               SIXTH",
        "",
        "  A command.",
    ]


def test_wrapping_long_command_name(runner):
    @click_hotoffthehamster.group()
    def cli():
        """Top level command
        """

    @cli.group()
    def a_very_very_very_long():
        """Second level
        """

    @a_very_very_very_long.command()
    @click_hotoffthehamster.argument("first")
    @click_hotoffthehamster.argument("second")
    @click_hotoffthehamster.argument("third")
    @click_hotoffthehamster.argument("fourth")
    @click_hotoffthehamster.argument("fifth")
    @click_hotoffthehamster.argument("sixth")
    def command():
        """A command.
        """

    result = runner.invoke(
        cli, ["a-very-very-very-long", "command", "--help"], terminal_width=54
    )
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli a-very-very-very-long command ",
        "           [OPTIONS] FIRST SECOND THIRD FOURTH FIFTH",
        "           SIXTH",
        "",
        "  A command.",
    ]


def test_formatting_empty_help_lines(runner):
    @click_hotoffthehamster.command()
    def cli():
        """Top level command

        """

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  Top level command",
        "",
        "",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_formatting_usage_error(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg")
    def cmd(arg):
        click_hotoffthehamster.echo("arg:{}".format(arg))

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "Try 'cmd --help' for help.",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_usage_error_metavar_missing_arg(runner):
    """
    :author: @r-m-n
    Including attribution to #612
    """

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg", metavar="metavar")
    def cmd(arg):
        pass

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] metavar",
        "Try 'cmd --help' for help.",
        "",
        "Error: Missing argument 'metavar'.",
    ]


def test_formatting_usage_error_metavar_bad_arg(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument(
        "arg", type=click_hotoffthehamster.INT, metavar="metavar"
    )
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["3.14"])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] metavar",
        "Try 'cmd --help' for help.",
        "",
        "Error: Invalid value for 'metavar': 3.14 is not a valid integer",
    ]


def test_formatting_usage_error_nested(runner):
    @click_hotoffthehamster.group()
    def cmd():
        pass

    @cmd.command()
    @click_hotoffthehamster.argument("bar")
    def foo(bar):
        click_hotoffthehamster.echo("foo:{}".format(bar))

    result = runner.invoke(cmd, ["foo"])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd foo [OPTIONS] BAR",
        "Try 'cmd foo --help' for help.",
        "",
        "Error: Missing argument 'BAR'.",
    ]


def test_formatting_usage_error_no_help(runner):
    @click_hotoffthehamster.command(add_help_option=False)
    @click_hotoffthehamster.argument("arg")
    def cmd(arg):
        click_hotoffthehamster.echo("arg:{}".format(arg))

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_usage_custom_help(runner):
    @click_hotoffthehamster.command(context_settings=dict(help_option_names=["--man"]))
    @click_hotoffthehamster.argument("arg")
    def cmd(arg):
        click_hotoffthehamster.echo("arg:{}".format(arg))

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "Try 'cmd --man' for help.",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_custom_type_metavar(runner):
    class MyType(click_hotoffthehamster.ParamType):
        def get_metavar(self, param):
            return "MY_TYPE"

    @click_hotoffthehamster.command("foo")
    @click_hotoffthehamster.help_option()
    @click_hotoffthehamster.argument("param", type=MyType())
    def cmd(param):
        pass

    result = runner.invoke(cmd, "--help")
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS] MY_TYPE",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_truncating_docstring(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.
        \f

        :param click_hotoffthehamster.core.Context ctx: Click context.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  First paragraph.",
        "",
        "  This is a very long second paragraph and not correctly",
        "  wrapped but it will be rewrapped.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_global_show_default(runner):
    @click_hotoffthehamster.command(context_settings=dict(show_default=True))
    @click_hotoffthehamster.option(
        "-f", "in_file", default="out.txt", help="Output file name"
    )
    def cli():
        pass

    result = runner.invoke(cli, ["--help"],)
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "Options:",
        "  -f TEXT  Output file name  [default: out.txt]",
        "  --help   Show this message and exit.  [default: False]",
    ]


def test_formatting_usage_multiline_option_padding(runner):
    @click_hotoffthehamster.command("foo")
    @click_hotoffthehamster.option(
        "--bar", help="This help message will be padded if it wraps."
    )
    def cli():
        pass

    result = runner.invoke(cli, "--help", terminal_width=45)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS]",
        "",
        "Options:",
        "  --bar TEXT  This help message will be",
        "              padded if it wraps.",
        "",
        "  --help      Show this message and exit.",
    ]


def test_formatting_usage_no_option_padding(runner):
    @click_hotoffthehamster.command("foo")
    @click_hotoffthehamster.option(
        "--bar", help="This help message will be padded if it wraps."
    )
    def cli():
        pass

    result = runner.invoke(cli, "--help", terminal_width=80)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS]",
        "",
        "Options:",
        "  --bar TEXT  This help message will be padded if it wraps.",
        "  --help      Show this message and exit.",
    ]
