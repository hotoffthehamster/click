# -*- coding: utf-8 -*-
import os
import uuid

import click_hotoffthehamster


def test_basic_functionality(runner):
    @click_hotoffthehamster.command()
    def cli():
        """Hello World!"""
        click_hotoffthehamster.echo("I EXECUTED")

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert "Hello World!" in result.output
    assert "Show this message and exit." in result.output
    assert result.exit_code == 0
    assert "I EXECUTED" not in result.output

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "I EXECUTED" in result.output
    assert result.exit_code == 0


def test_repr():
    @click_hotoffthehamster.command()
    def command():
        pass

    @click_hotoffthehamster.group()
    def group():
        pass

    @group.command()
    def subcommand():
        pass

    assert repr(command) == "<Command command>"
    assert repr(group) == "<Group group>"
    assert repr(subcommand) == "<Command subcommand>"


def test_return_values():
    @click_hotoffthehamster.command()
    def cli():
        return 42

    with cli.make_context("foo", []) as ctx:
        rv = cli.invoke(ctx)
        assert rv == 42


def test_basic_group(runner):
    @click_hotoffthehamster.group()
    def cli():
        """This is the root."""
        click_hotoffthehamster.echo("ROOT EXECUTED")

    @cli.command()
    def subcommand():
        """This is a subcommand."""
        click_hotoffthehamster.echo("SUBCOMMAND EXECUTED")

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert "COMMAND [ARGS]..." in result.output
    assert "This is the root" in result.output
    assert "This is a subcommand." in result.output
    assert result.exit_code == 0
    assert "ROOT EXECUTED" not in result.output

    result = runner.invoke(cli, ["subcommand"])
    assert not result.exception
    assert result.exit_code == 0
    assert "ROOT EXECUTED" in result.output
    assert "SUBCOMMAND EXECUTED" in result.output


def test_basic_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", default="no value")
    def cli(foo):
        click_hotoffthehamster.echo(u"FOO:[{}]".format(foo))

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "FOO:[no value]" in result.output

    result = runner.invoke(cli, ["--foo=42"])
    assert not result.exception
    assert "FOO:[42]" in result.output

    result = runner.invoke(cli, ["--foo"])
    assert result.exception
    assert "--foo option requires an argument" in result.output

    result = runner.invoke(cli, ["--foo="])
    assert not result.exception
    assert "FOO:[]" in result.output

    result = runner.invoke(cli, [u"--foo=\N{SNOWMAN}"])
    assert not result.exception
    assert u"FOO:[\N{SNOWMAN}]" in result.output


def test_int_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", default=42)
    def cli(foo):
        click_hotoffthehamster.echo("FOO:[{}]".format(foo * 2))

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "FOO:[84]" in result.output

    result = runner.invoke(cli, ["--foo=23"])
    assert not result.exception
    assert "FOO:[46]" in result.output

    result = runner.invoke(cli, ["--foo=bar"])
    assert result.exception
    assert "Invalid value for '--foo': bar is not a valid integer" in result.output


def test_uuid_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--u",
        default="ba122011-349f-423b-873b-9d6a79c688ab",
        type=click_hotoffthehamster.UUID,
    )
    def cli(u):
        assert type(u) is uuid.UUID
        click_hotoffthehamster.echo("U:[{}]".format(u))

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "U:[ba122011-349f-423b-873b-9d6a79c688ab]" in result.output

    result = runner.invoke(cli, ["--u=821592c1-c50e-4971-9cd6-e89dc6832f86"])
    assert not result.exception
    assert "U:[821592c1-c50e-4971-9cd6-e89dc6832f86]" in result.output

    result = runner.invoke(cli, ["--u=bar"])
    assert result.exception
    assert "Invalid value for '--u': bar is not a valid UUID value" in result.output


def test_float_option(runner):
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

    result = runner.invoke(cli, ["--foo=23.5"])
    assert not result.exception
    assert "FOO:[23.5]" in result.output

    result = runner.invoke(cli, ["--foo=bar"])
    assert result.exception
    assert "Invalid value for '--foo': bar is not a valid float" in result.output


def test_boolean_option(runner):
    for default in True, False:

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.option("--with-foo/--without-foo", default=default)
        def cli(with_foo):
            click_hotoffthehamster.echo(with_foo)

        result = runner.invoke(cli, ["--with-foo"])
        assert not result.exception
        assert result.output == "True\n"
        result = runner.invoke(cli, ["--without-foo"])
        assert not result.exception
        assert result.output == "False\n"
        result = runner.invoke(cli, [])
        assert not result.exception
        assert result.output == "{}\n".format(default)

    for default in True, False:

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.option("--flag", is_flag=True, default=default)
        def cli(flag):
            click_hotoffthehamster.echo(flag)

        result = runner.invoke(cli, ["--flag"])
        assert not result.exception
        assert result.output == "{}\n".format(not default)
        result = runner.invoke(cli, [])
        assert not result.exception
        assert result.output == "{}\n".format(default)


def test_boolean_conversion(runner):
    for default in True, False:

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.option("--flag", default=default, type=bool)
        def cli(flag):
            click_hotoffthehamster.echo(flag)

        for value in "true", "t", "1", "yes", "y":
            result = runner.invoke(cli, ["--flag", value])
            assert not result.exception
            assert result.output == "True\n"

        for value in "false", "f", "0", "no", "n":
            result = runner.invoke(cli, ["--flag", value])
            assert not result.exception
            assert result.output == "False\n"

        result = runner.invoke(cli, [])
        assert not result.exception
        assert result.output == "{}\n".format(default)


def test_file_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--file", type=click_hotoffthehamster.File("w"))
    def input(file):
        file.write("Hello World!\n")

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--file", type=click_hotoffthehamster.File("r"))
    def output(file):
        click_hotoffthehamster.echo(file.read())

    with runner.isolated_filesystem():
        result_in = runner.invoke(input, ["--file=example.txt"])
        result_out = runner.invoke(output, ["--file=example.txt"])

    assert not result_in.exception
    assert result_in.output == ""
    assert not result_out.exception
    assert result_out.output == "Hello World!\n\n"


def test_file_lazy_mode(runner):
    do_io = False

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--file", type=click_hotoffthehamster.File("w"))
    def input(file):
        if do_io:
            file.write("Hello World!\n")

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--file", type=click_hotoffthehamster.File("r"))
    def output(file):
        pass

    with runner.isolated_filesystem():
        os.mkdir("example.txt")

        do_io = True
        result_in = runner.invoke(input, ["--file=example.txt"])
        assert result_in.exit_code == 1

        do_io = False
        result_in = runner.invoke(input, ["--file=example.txt"])
        assert result_in.exit_code == 0

        result_out = runner.invoke(output, ["--file=example.txt"])
        assert result_out.exception

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--file", type=click_hotoffthehamster.File("w", lazy=False)
    )
    def input_non_lazy(file):
        file.write("Hello World!\n")

    with runner.isolated_filesystem():
        os.mkdir("example.txt")
        result_in = runner.invoke(input_non_lazy, ["--file=example.txt"])
        assert result_in.exit_code == 2
        assert (
            "Invalid value for '--file': Could not open file: example.txt"
            in result_in.output
        )


def test_path_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "-O",
        type=click_hotoffthehamster.Path(file_okay=False, exists=True, writable=True),
    )
    def write_to_dir(o):
        with open(os.path.join(o, "foo.txt"), "wb") as f:
            f.write(b"meh\n")

    with runner.isolated_filesystem():
        os.mkdir("test")

        result = runner.invoke(write_to_dir, ["-O", "test"])
        assert not result.exception

        with open("test/foo.txt", "rb") as f:
            assert f.read() == b"meh\n"

        result = runner.invoke(write_to_dir, ["-O", "test/foo.txt"])
        assert "is a file" in result.output

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("-f", type=click_hotoffthehamster.Path(exists=True))
    def showtype(f):
        click_hotoffthehamster.echo("is_file={}".format(os.path.isfile(f)))
        click_hotoffthehamster.echo("is_dir={}".format(os.path.isdir(f)))

    with runner.isolated_filesystem():
        result = runner.invoke(showtype, ["-f", "xxx"])
        assert "does not exist" in result.output

        result = runner.invoke(showtype, ["-f", "."])
        assert "is_file=False" in result.output
        assert "is_dir=True" in result.output

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("-f", type=click_hotoffthehamster.Path())
    def exists(f):
        click_hotoffthehamster.echo("exists={}".format(os.path.exists(f)))

    with runner.isolated_filesystem():
        result = runner.invoke(exists, ["-f", "xxx"])
        assert "exists=False" in result.output

        result = runner.invoke(exists, ["-f", "."])
        assert "exists=True" in result.output


def test_choice_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--method", type=click_hotoffthehamster.Choice(["foo", "bar", "baz"])
    )
    def cli(method):
        click_hotoffthehamster.echo(method)

    result = runner.invoke(cli, ["--method=foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(cli, ["--method=meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--method': invalid choice: meh."
        " (choose from foo, bar, baz)" in result.output
    )

    result = runner.invoke(cli, ["--help"])
    assert "--method [foo|bar|baz]" in result.output


def test_datetime_option_default(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--start_date", type=click_hotoffthehamster.DateTime()
    )
    def cli(start_date):
        click_hotoffthehamster.echo(start_date.strftime("%Y-%m-%dT%H:%M:%S"))

    result = runner.invoke(cli, ["--start_date=2015-09-29"])
    assert not result.exception
    assert result.output == "2015-09-29T00:00:00\n"

    result = runner.invoke(cli, ["--start_date=2015-09-29T09:11:22"])
    assert not result.exception
    assert result.output == "2015-09-29T09:11:22\n"

    result = runner.invoke(cli, ["--start_date=2015-09"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--start_date':"
        " invalid datetime format: 2015-09."
        " (choose from %Y-%m-%d, %Y-%m-%dT%H:%M:%S, %Y-%m-%d %H:%M:%S)"
    ) in result.output

    result = runner.invoke(cli, ["--help"])
    assert (
        "--start_date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]" in result.output
    )


def test_datetime_option_custom(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--start_date", type=click_hotoffthehamster.DateTime(formats=["%A %B %d, %Y"])
    )
    def cli(start_date):
        click_hotoffthehamster.echo(start_date.strftime("%Y-%m-%dT%H:%M:%S"))

    result = runner.invoke(cli, ["--start_date=Wednesday June 05, 2010"])
    assert not result.exception
    assert result.output == "2010-06-05T00:00:00\n"


def test_int_range_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--x", type=click_hotoffthehamster.IntRange(0, 5))
    def cli(x):
        click_hotoffthehamster.echo(x)

    result = runner.invoke(cli, ["--x=5"])
    assert not result.exception
    assert result.output == "5\n"

    result = runner.invoke(cli, ["--x=6"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--x': 6 is not in the valid range of 0 to 5.\n"
        in result.output
    )

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--x", type=click_hotoffthehamster.IntRange(0, 5, clamp=True)
    )
    def clamp(x):
        click_hotoffthehamster.echo(x)

    result = runner.invoke(clamp, ["--x=5"])
    assert not result.exception
    assert result.output == "5\n"

    result = runner.invoke(clamp, ["--x=6"])
    assert not result.exception
    assert result.output == "5\n"

    result = runner.invoke(clamp, ["--x=-1"])
    assert not result.exception
    assert result.output == "0\n"


def test_float_range_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--x", type=click_hotoffthehamster.FloatRange(0, 5))
    def cli(x):
        click_hotoffthehamster.echo(x)

    result = runner.invoke(cli, ["--x=5.0"])
    assert not result.exception
    assert result.output == "5.0\n"

    result = runner.invoke(cli, ["--x=6.0"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--x': 6.0 is not in the valid range of 0 to 5.\n"
        in result.output
    )

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--x", type=click_hotoffthehamster.FloatRange(0, 5, clamp=True)
    )
    def clamp(x):
        click_hotoffthehamster.echo(x)

    result = runner.invoke(clamp, ["--x=5.0"])
    assert not result.exception
    assert result.output == "5.0\n"

    result = runner.invoke(clamp, ["--x=6.0"])
    assert not result.exception
    assert result.output == "5\n"

    result = runner.invoke(clamp, ["--x=-1.0"])
    assert not result.exception
    assert result.output == "0\n"


def test_required_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", required=True)
    def cli(foo):
        click_hotoffthehamster.echo(foo)

    result = runner.invoke(cli, [])
    assert result.exit_code == 2
    assert "Missing option '--foo'" in result.output


def test_evaluation_order(runner):
    called = []

    def memo(ctx, param, value):
        called.append(value)
        return value

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option(
        "--missing", default="missing", is_eager=False, callback=memo
    )
    @click_hotoffthehamster.option(
        "--eager-flag1", flag_value="eager1", is_eager=True, callback=memo
    )
    @click_hotoffthehamster.option(
        "--eager-flag2", flag_value="eager2", is_eager=True, callback=memo
    )
    @click_hotoffthehamster.option(
        "--eager-flag3", flag_value="eager3", is_eager=True, callback=memo
    )
    @click_hotoffthehamster.option(
        "--normal-flag1", flag_value="normal1", is_eager=False, callback=memo
    )
    @click_hotoffthehamster.option(
        "--normal-flag2", flag_value="normal2", is_eager=False, callback=memo
    )
    @click_hotoffthehamster.option(
        "--normal-flag3", flag_value="normal3", is_eager=False, callback=memo
    )
    def cli(**x):
        pass

    result = runner.invoke(
        cli,
        [
            "--eager-flag2",
            "--eager-flag1",
            "--normal-flag2",
            "--eager-flag3",
            "--normal-flag3",
            "--normal-flag3",
            "--normal-flag1",
            "--normal-flag1",
        ],
    )
    assert not result.exception
    assert called == [
        "eager2",
        "eager1",
        "eager3",
        "normal2",
        "normal3",
        "normal1",
        "missing",
    ]


def test_hidden_option(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--nope", hidden=True)
    def cli(nope):
        click_hotoffthehamster.echo(nope)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--nope" not in result.output


def test_hidden_command(runner):
    @click_hotoffthehamster.group()
    def cli():
        pass

    @cli.command(hidden=True)
    def nope():
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "nope" not in result.output


def test_hidden_group(runner):
    @click_hotoffthehamster.group()
    def cli():
        pass

    @cli.group(hidden=True)
    def subgroup():
        pass

    @subgroup.command()
    def nope():
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "subgroup" not in result.output
    assert "nope" not in result.output
