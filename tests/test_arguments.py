# -*- coding: utf-8 -*-
import sys

import pytest

import click_hotoffthehamster
from click_hotoffthehamster._compat import PY2
from click_hotoffthehamster._compat import text_type


def test_nargs_star(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("src", nargs=-1)
    @click_hotoffthehamster.argument("dst")
    def copy(src, dst):
        click_hotoffthehamster.echo("src={}".format("|".join(src)))
        click_hotoffthehamster.echo("dst={}".format(dst))

    result = runner.invoke(copy, ["foo.txt", "bar.txt", "dir"])
    assert not result.exception
    assert result.output.splitlines() == ["src=foo.txt|bar.txt", "dst=dir"]


def test_nargs_default(runner):
    with pytest.raises(TypeError, match="nargs=-1"):

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.argument("src", nargs=-1, default=42)
        def copy(src):
            pass


def test_nargs_tup(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("name", nargs=1)
    @click_hotoffthehamster.argument("point", nargs=2, type=click_hotoffthehamster.INT)
    def copy(name, point):
        click_hotoffthehamster.echo("name={}".format(name))
        click_hotoffthehamster.echo("point={0[0]}/{0[1]}".format(point))

    result = runner.invoke(copy, ["peter", "1", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["name=peter", "point=1/2"]


def test_nargs_tup_composite(runner):
    variations = [
        dict(type=(str, int)),
        dict(type=click_hotoffthehamster.Tuple([str, int])),
        dict(nargs=2, type=click_hotoffthehamster.Tuple([str, int])),
        dict(nargs=2, type=(str, int)),
    ]

    for opts in variations:

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.argument("item", **opts)
        def copy(item):
            click_hotoffthehamster.echo("name={0[0]} id={0[1]:d}".format(item))

        result = runner.invoke(copy, ["peter", "1"])
        assert not result.exception
        assert result.output.splitlines() == ["name=peter id=1"]


def test_nargs_err(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("x")
    def copy(x):
        click_hotoffthehamster.echo(x)

    result = runner.invoke(copy, ["foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(copy, ["foo", "bar"])
    assert result.exit_code == 2
    assert "Got unexpected extra argument (bar)" in result.output


def test_bytes_args(runner, monkeypatch):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg")
    def from_bytes(arg):
        assert isinstance(
            arg, text_type
        ), "UTF-8 encoded argument should be implicitly converted to Unicode"

    # Simulate empty locale environment variables
    if PY2:
        monkeypatch.setattr(sys.stdin, "encoding", "ANSI_X3.4-1968")
        monkeypatch.setattr(sys, "getfilesystemencoding", lambda: "ANSI_X3.4-1968")
        monkeypatch.setattr(sys, "getdefaultencoding", lambda: "ascii")
    else:
        monkeypatch.setattr(sys.stdin, "encoding", "utf-8")
        monkeypatch.setattr(sys, "getfilesystemencoding", lambda: "utf-8")
        monkeypatch.setattr(sys, "getdefaultencoding", lambda: "utf-8")

    runner.invoke(
        from_bytes,
        [u"Something outside of ASCII range: 林".encode("UTF-8")],
        catch_exceptions=False,
    )


def test_file_args(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("input", type=click_hotoffthehamster.File("rb"))
    @click_hotoffthehamster.argument("output", type=click_hotoffthehamster.File("wb"))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

    with runner.isolated_filesystem():
        result = runner.invoke(inout, ["-", "hello.txt"], input="Hey!")
        assert result.output == ""
        assert result.exit_code == 0
        with open("hello.txt", "rb") as f:
            assert f.read() == b"Hey!"

        result = runner.invoke(inout, ["hello.txt", "-"])
        assert result.output == "Hey!"
        assert result.exit_code == 0


def test_path_args(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument(
        "input", type=click_hotoffthehamster.Path(dir_okay=False, allow_dash=True)
    )
    def foo(input):
        click_hotoffthehamster.echo(input)

    result = runner.invoke(foo, ["-"])
    assert result.output == "-\n"
    assert result.exit_code == 0


def test_file_atomics(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument(
        "output", type=click_hotoffthehamster.File("wb", atomic=True)
    )
    def inout(output):
        output.write(b"Foo bar baz\n")
        output.flush()
        with open(output.name, "rb") as f:
            old_content = f.read()
            assert old_content == b"OLD\n"

    with runner.isolated_filesystem():
        with open("foo.txt", "wb") as f:
            f.write(b"OLD\n")
        result = runner.invoke(inout, ["foo.txt"], input="Hey!", catch_exceptions=False)
        assert result.output == ""
        assert result.exit_code == 0
        with open("foo.txt", "rb") as f:
            assert f.read() == b"Foo bar baz\n"


def test_stdout_default(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument(
        "output", type=click_hotoffthehamster.File("w"), default="-"
    )
    def inout(output):
        output.write("Foo bar baz\n")
        output.flush()

    result = runner.invoke(inout, [])
    assert not result.exception
    assert result.output == "Foo bar baz\n"


def test_nargs_envvar(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--arg", nargs=2)
    def cmd(arg):
        click_hotoffthehamster.echo("|".join(arg))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "foo bar"}
    )
    assert not result.exception
    assert result.output == "foo|bar\n"

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--arg", envvar="X", nargs=2)
    def cmd(arg):
        click_hotoffthehamster.echo("|".join(arg))

    result = runner.invoke(cmd, [], env={"X": "foo bar"})
    assert not result.exception
    assert result.output == "foo|bar\n"


def test_empty_nargs(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg", nargs=-1)
    def cmd(arg):
        click_hotoffthehamster.echo("arg:{}".format("|".join(arg)))

    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert result.output == "arg:\n"

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg", nargs=-1, required=True)
    def cmd2(arg):
        click_hotoffthehamster.echo("arg:{}".format("|".join(arg)))

    result = runner.invoke(cmd2, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG...'" in result.output


def test_missing_arg(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("arg")
    def cmd(arg):
        click_hotoffthehamster.echo("arg:{}".format(arg))

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG'." in result.output


def test_missing_argument_string_cast():
    ctx = click_hotoffthehamster.Context(click_hotoffthehamster.Command(""))

    with pytest.raises(click_hotoffthehamster.MissingParameter) as excinfo:
        click_hotoffthehamster.Argument(["a"], required=True).full_process_value(
            ctx, None
        )

    assert str(excinfo.value) == "missing parameter: a"


def test_implicit_non_required(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("f", default="test")
    def cli(f):
        click_hotoffthehamster.echo(f)

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "test\n"


def test_eat_options(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("-f")
    @click_hotoffthehamster.argument("files", nargs=-1)
    def cmd(f, files):
        for filename in files:
            click_hotoffthehamster.echo(filename)
        click_hotoffthehamster.echo(f)

    result = runner.invoke(cmd, ["--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", ""]

    result = runner.invoke(cmd, ["-f", "-x", "--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", "-x"]


def test_nargs_star_ordering(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("a", nargs=-1)
    @click_hotoffthehamster.argument("b")
    @click_hotoffthehamster.argument("c")
    def cmd(a, b, c):
        for arg in (a, b, c):
            click_hotoffthehamster.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c"])
    assert result.output.splitlines() == ["(u'a',)" if PY2 else "('a',)", "b", "c"]


def test_nargs_specified_plus_star_ordering(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("a", nargs=-1)
    @click_hotoffthehamster.argument("b")
    @click_hotoffthehamster.argument("c", nargs=2)
    def cmd(a, b, c):
        for arg in (a, b, c):
            click_hotoffthehamster.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c", "d", "e", "f"])
    assert result.output.splitlines() == [
        "(u'a', u'b', u'c')" if PY2 else "('a', 'b', 'c')",
        "d",
        "(u'e', u'f')" if PY2 else "('e', 'f')",
    ]


def test_defaults_for_nargs(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("a", nargs=2, type=int, default=(1, 2))
    def cmd(a):
        x, y = a
        click_hotoffthehamster.echo(x + y)

    result = runner.invoke(cmd, [])
    assert result.output.strip() == "3"

    result = runner.invoke(cmd, ["3", "4"])
    assert result.output.strip() == "7"

    result = runner.invoke(cmd, ["3"])
    assert result.exception is not None
    assert "argument a takes 2 values" in result.output


def test_multiple_param_decls_not_allowed(runner):
    with pytest.raises(TypeError):

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.argument("x", click_hotoffthehamster.Choice(["a", "b"]))
        def copy(x):
            click_hotoffthehamster.echo(x)
