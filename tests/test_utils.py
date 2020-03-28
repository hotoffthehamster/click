import os
import stat
import sys

import pytest

import click_hotoffthehamster._termui_impl
import click_hotoffthehamster.utils
from click_hotoffthehamster._compat import WIN


def test_echo(runner):
    with runner.isolation() as outstreams:
        click_hotoffthehamster.echo(u"\N{SNOWMAN}")
        click_hotoffthehamster.echo(b"\x44\x44")
        click_hotoffthehamster.echo(42, nl=False)
        click_hotoffthehamster.echo(b"a", nl=False)
        click_hotoffthehamster.echo("\x1b[31mx\x1b[39m", nl=False)
        bytes = outstreams[0].getvalue().replace(b"\r\n", b"\n")
        assert bytes == b"\xe2\x98\x83\nDD\n42ax"

    # If we are in Python 2, we expect that writing bytes into a string io
    # does not do anything crazy.  In Python 3
    if sys.version_info[0] == 2:
        import StringIO

        sys.stdout = x = StringIO.StringIO()
        try:
            click_hotoffthehamster.echo("\xf6")
        finally:
            sys.stdout = sys.__stdout__
        assert x.getvalue() == "\xf6\n"

    # And in any case, if wrapped, we expect bytes to survive.
    @click_hotoffthehamster.command()
    def cli():
        click_hotoffthehamster.echo(b"\xf6")

    result = runner.invoke(cli, [])
    assert result.stdout_bytes == b"\xf6\n"

    # Ensure we do not strip for bytes.
    with runner.isolation() as outstreams:
        click_hotoffthehamster.echo(bytearray(b"\x1b[31mx\x1b[39m"), nl=False)
        assert outstreams[0].getvalue() == b"\x1b[31mx\x1b[39m"


def test_echo_custom_file():
    import io

    f = io.StringIO()
    click_hotoffthehamster.echo(u"hello", file=f)
    assert f.getvalue() == u"hello\n"


@pytest.mark.parametrize(
    ("styles", "ref"),
    [
        ({"fg": "black"}, "\x1b[30mx y\x1b[0m"),
        ({"fg": "red"}, "\x1b[31mx y\x1b[0m"),
        ({"fg": "green"}, "\x1b[32mx y\x1b[0m"),
        ({"fg": "yellow"}, "\x1b[33mx y\x1b[0m"),
        ({"fg": "blue"}, "\x1b[34mx y\x1b[0m"),
        ({"fg": "magenta"}, "\x1b[35mx y\x1b[0m"),
        ({"fg": "cyan"}, "\x1b[36mx y\x1b[0m"),
        ({"fg": "white"}, "\x1b[37mx y\x1b[0m"),
        ({"bg": "black"}, "\x1b[40mx y\x1b[0m"),
        ({"bg": "red"}, "\x1b[41mx y\x1b[0m"),
        ({"bg": "green"}, "\x1b[42mx y\x1b[0m"),
        ({"bg": "yellow"}, "\x1b[43mx y\x1b[0m"),
        ({"bg": "blue"}, "\x1b[44mx y\x1b[0m"),
        ({"bg": "magenta"}, "\x1b[45mx y\x1b[0m"),
        ({"bg": "cyan"}, "\x1b[46mx y\x1b[0m"),
        ({"bg": "white"}, "\x1b[47mx y\x1b[0m"),
        ({"blink": True}, "\x1b[5mx y\x1b[0m"),
        ({"underline": True}, "\x1b[4mx y\x1b[0m"),
        ({"bold": True}, "\x1b[1mx y\x1b[0m"),
        ({"dim": True}, "\x1b[2mx y\x1b[0m"),
    ],
)
def test_styling(styles, ref):
    assert click_hotoffthehamster.style("x y", **styles) == ref
    assert click_hotoffthehamster.unstyle(ref) == "x y"


@pytest.mark.parametrize(("text", "expect"), [("\x1b[?25lx y\x1b[?25h", "x y")])
def test_unstyle_other_ansi(text, expect):
    assert click_hotoffthehamster.unstyle(text) == expect


def test_filename_formatting():
    assert click_hotoffthehamster.format_filename(b"foo.txt") == "foo.txt"
    assert click_hotoffthehamster.format_filename(b"/x/foo.txt") == "/x/foo.txt"
    assert click_hotoffthehamster.format_filename(u"/x/foo.txt") == "/x/foo.txt"
    assert (
        click_hotoffthehamster.format_filename(u"/x/foo.txt", shorten=True) == "foo.txt"
    )

    # filesystem encoding on windows permits this.
    if not WIN:
        assert (
            click_hotoffthehamster.format_filename(b"/x/foo\xff.txt", shorten=True)
            == u"foo\ufffd.txt"
        )


def test_prompts(runner):
    @click_hotoffthehamster.command()
    def test():
        if click_hotoffthehamster.confirm("Foo"):
            click_hotoffthehamster.echo("yes!")
        else:
            click_hotoffthehamster.echo("no :(")

    result = runner.invoke(test, input="y\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: y\nyes!\n"

    result = runner.invoke(test, input="\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: \nno :(\n"

    result = runner.invoke(test, input="n\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: n\nno :(\n"

    @click_hotoffthehamster.command()
    def test_no():
        if click_hotoffthehamster.confirm("Foo", default=True):
            click_hotoffthehamster.echo("yes!")
        else:
            click_hotoffthehamster.echo("no :(")

    result = runner.invoke(test_no, input="y\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: y\nyes!\n"

    result = runner.invoke(test_no, input="\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: \nyes!\n"

    result = runner.invoke(test_no, input="n\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: n\nno :(\n"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
def test_prompts_abort(monkeypatch, capsys):
    def f(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("click_hotoffthehamster.termui.hidden_prompt_func", f)

    try:
        click_hotoffthehamster.prompt("Password", hide_input=True)
    except click_hotoffthehamster.Abort:
        click_hotoffthehamster.echo("Screw you.")

    out, err = capsys.readouterr()
    assert out == "Password: \nScrew you.\n"


def _test_gen_func():
    yield "a"
    yield "b"
    yield "c"
    yield "abc"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize("cat", ["cat", "cat ", "cat "])
@pytest.mark.parametrize(
    "test",
    [
        # We need lambda here, because pytest will
        # reuse the parameters, and then the generators
        # are already used and will not yield anymore
        ("just text\n", lambda: "just text"),
        ("iterable\n", lambda: ["itera", "ble"]),
        ("abcabc\n", lambda: _test_gen_func),
        ("abcabc\n", lambda: _test_gen_func()),
        ("012345\n", lambda: (c for c in range(6))),
    ],
)
def test_echo_via_pager(monkeypatch, capfd, cat, test):
    monkeypatch.setitem(os.environ, "PAGER", cat)
    monkeypatch.setattr(click_hotoffthehamster._termui_impl, "isatty", lambda x: True)

    expected_output = test[0]
    test_input = test[1]()

    click_hotoffthehamster.echo_via_pager(test_input)

    out, err = capfd.readouterr()
    assert out == expected_output


@pytest.mark.skipif(WIN, reason="Test does not make sense on Windows.")
def test_echo_color_flag(monkeypatch, capfd):
    isatty = True
    monkeypatch.setattr(click_hotoffthehamster._compat, "isatty", lambda x: isatty)

    text = "foo"
    styled_text = click_hotoffthehamster.style(text, fg="red")
    assert styled_text == "\x1b[31mfoo\x1b[0m"

    click_hotoffthehamster.echo(styled_text, color=False)
    out, err = capfd.readouterr()
    assert out == "{}\n".format(text)

    click_hotoffthehamster.echo(styled_text, color=True)
    out, err = capfd.readouterr()
    assert out == "{}\n".format(styled_text)

    isatty = True
    click_hotoffthehamster.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == "{}\n".format(styled_text)

    isatty = False
    click_hotoffthehamster.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == "{}\n".format(text)


@pytest.mark.skipif(WIN, reason="Test too complex to make work windows.")
def test_echo_writing_to_standard_error(capfd, monkeypatch):
    def emulate_input(text):
        """Emulate keyboard input."""
        if sys.version_info[0] == 2:
            from StringIO import StringIO
        else:
            from io import StringIO
        monkeypatch.setattr(sys, "stdin", StringIO(text))

    click_hotoffthehamster.echo("Echo to standard output")
    out, err = capfd.readouterr()
    assert out == "Echo to standard output\n"
    assert err == ""

    click_hotoffthehamster.echo("Echo to standard error", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Echo to standard error\n"

    emulate_input("asdlkj\n")
    click_hotoffthehamster.prompt("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin: "
    assert err == ""

    emulate_input("asdlkj\n")
    click_hotoffthehamster.prompt("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr: "

    emulate_input("y\n")
    click_hotoffthehamster.confirm("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin [y/N]: "
    assert err == ""

    emulate_input("y\n")
    click_hotoffthehamster.confirm("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr [y/N]: "

    monkeypatch.setattr(click_hotoffthehamster.termui, "isatty", lambda x: True)
    monkeypatch.setattr(click_hotoffthehamster.termui, "getchar", lambda: " ")

    click_hotoffthehamster.pause("Pause to stdout")
    out, err = capfd.readouterr()
    assert out == "Pause to stdout\n"
    assert err == ""

    click_hotoffthehamster.pause("Pause to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Pause to stderr\n"


def test_open_file(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("filename")
    def cli(filename):
        with click_hotoffthehamster.open_file(filename) as f:
            click_hotoffthehamster.echo(f.read())

        click_hotoffthehamster.echo("meep")

    with runner.isolated_filesystem():
        with open("hello.txt", "w") as f:
            f.write("Cool stuff")

        result = runner.invoke(cli, ["hello.txt"])
        assert result.exception is None
        assert result.output == "Cool stuff\nmeep\n"

        result = runner.invoke(cli, ["-"], input="foobar")
        assert result.exception is None
        assert result.output == "foobar\nmeep\n"


def test_open_file_ignore_errors_stdin(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.argument("filename")
    def cli(filename):
        with click_hotoffthehamster.open_file(filename, errors="ignore") as f:
            click_hotoffthehamster.echo(f.read())

    result = runner.invoke(cli, ["-"], input=os.urandom(16))
    assert result.exception is None


def test_open_file_respects_ignore(runner):
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("Hello world!")

        with click_hotoffthehamster.open_file(
            "test.txt", encoding="utf8", errors="ignore"
        ) as f:
            assert f.errors == "ignore"


def test_open_file_ignore_invalid_utf8(runner):
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"\xe2\x28\xa1")

        with click_hotoffthehamster.open_file(
            "test.txt", encoding="utf8", errors="ignore"
        ) as f:
            f.read()


def test_open_file_ignore_no_encoding(runner):
    with runner.isolated_filesystem():
        with open("test.bin", "wb") as f:
            f.write(os.urandom(16))

        with click_hotoffthehamster.open_file("test.bin", errors="ignore") as f:
            f.read()


@pytest.mark.skipif(WIN, reason="os.chmod() is not fully supported on Windows.")
@pytest.mark.parametrize("permissions", [0o400, 0o444, 0o600, 0o644])
def test_open_file_atomic_permissions_existing_file(runner, permissions):
    with runner.isolated_filesystem():
        with open("existing.txt", "w") as f:
            f.write("content")
        os.chmod("existing.txt", permissions)

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.argument("filename")
        def cli(filename):
            click_hotoffthehamster.open_file(filename, "w", atomic=True).close()

        result = runner.invoke(cli, ["existing.txt"])
        assert result.exception is None
        assert stat.S_IMODE(os.stat("existing.txt").st_mode) == permissions


@pytest.mark.skipif(WIN, reason="os.stat() is not fully supported on Windows.")
def test_open_file_atomic_permissions_new_file(runner):
    with runner.isolated_filesystem():

        @click_hotoffthehamster.command()
        @click_hotoffthehamster.argument("filename")
        def cli(filename):
            click_hotoffthehamster.open_file(filename, "w", atomic=True).close()

        # Create a test file to get the expected permissions for new files
        # according to the current umask.
        with open("test.txt", "w"):
            pass
        permissions = stat.S_IMODE(os.stat("test.txt").st_mode)

        result = runner.invoke(cli, ["new.txt"])
        assert result.exception is None
        assert stat.S_IMODE(os.stat("new.txt").st_mode) == permissions


def test_iter_keepopenfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        for e_line, a_line in zip(
            expected, click_hotoffthehamster.utils.KeepOpenFile(f)
        ):
            assert e_line == a_line.strip()


def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with click_hotoffthehamster.utils.LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf):
                assert e_line == a_line.strip()
