import os
import sys

import pytest

import click_hotoffthehamster
from click_hotoffthehamster._compat import PY2
from click_hotoffthehamster._compat import WIN
from click_hotoffthehamster.testing import CliRunner

# Use the most reasonable io that users would use for the python version.
if PY2:
    from cStringIO import StringIO as ReasonableBytesIO
else:
    from io import BytesIO as ReasonableBytesIO


def test_runner():
    @click_hotoffthehamster.command()
    def test():
        i = click_hotoffthehamster.get_binary_stream("stdin")
        o = click_hotoffthehamster.get_binary_stream("stdout")
        while 1:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input="Hello World!\n")
    assert not result.exception
    assert result.output == "Hello World!\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input="Hello World!\n")
    assert not result.exception
    assert result.output == "Hello World!\nHello World!\n"


def test_runner_with_stream():
    @click_hotoffthehamster.command()
    def test():
        i = click_hotoffthehamster.get_binary_stream("stdin")
        o = click_hotoffthehamster.get_binary_stream("stdout")
        while 1:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input=ReasonableBytesIO(b"Hello World!\n"))
    assert not result.exception
    assert result.output == "Hello World!\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input=ReasonableBytesIO(b"Hello World!\n"))
    assert not result.exception
    assert result.output == "Hello World!\nHello World!\n"


def test_prompts():
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", prompt=True)
    def test(foo):
        click_hotoffthehamster.echo("foo={}".format(foo))

    runner = CliRunner()
    result = runner.invoke(test, input="wau wau\n")
    assert not result.exception
    assert result.output == "Foo: wau wau\nfoo=wau wau\n"

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", prompt=True, hide_input=True)
    def test(foo):
        click_hotoffthehamster.echo("foo={}".format(foo))

    runner = CliRunner()
    result = runner.invoke(test, input="wau wau\n")
    assert not result.exception
    assert result.output == "Foo: \nfoo=wau wau\n"


def test_getchar():
    @click_hotoffthehamster.command()
    def continue_it():
        click_hotoffthehamster.echo(click_hotoffthehamster.getchar())

    runner = CliRunner()
    result = runner.invoke(continue_it, input="y")
    assert not result.exception
    assert result.output == "y\n"


def test_catch_exceptions():
    class CustomError(Exception):
        pass

    @click_hotoffthehamster.command()
    def cli():
        raise CustomError(1)

    runner = CliRunner()

    result = runner.invoke(cli)
    assert isinstance(result.exception, CustomError)
    assert type(result.exc_info) is tuple
    assert len(result.exc_info) == 3

    with pytest.raises(CustomError):
        runner.invoke(cli, catch_exceptions=False)

    CustomError = SystemExit

    result = runner.invoke(cli)
    assert result.exit_code == 1


@pytest.mark.skipif(WIN, reason="Test does not make sense on Windows.")
def test_with_color():
    @click_hotoffthehamster.command()
    def cli():
        click_hotoffthehamster.secho("hello world", fg="blue")

    runner = CliRunner()

    result = runner.invoke(cli)
    assert result.output == "hello world\n"
    assert not result.exception

    result = runner.invoke(cli, color=True)
    assert result.output == "{}\n".format(
        click_hotoffthehamster.style("hello world", fg="blue")
    )
    assert not result.exception


def test_with_color_but_pause_not_blocking():
    @click_hotoffthehamster.command()
    def cli():
        click_hotoffthehamster.pause()

    runner = CliRunner()
    result = runner.invoke(cli, color=True)
    assert not result.exception
    assert result.output == ""


def test_exit_code_and_output_from_sys_exit():
    # See issue #362
    @click_hotoffthehamster.command()
    def cli_string():
        click_hotoffthehamster.echo("hello world")
        sys.exit("error")

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli_string_ctx_exit(ctx):
        click_hotoffthehamster.echo("hello world")
        ctx.exit("error")

    @click_hotoffthehamster.command()
    def cli_int():
        click_hotoffthehamster.echo("hello world")
        sys.exit(1)

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli_int_ctx_exit(ctx):
        click_hotoffthehamster.echo("hello world")
        ctx.exit(1)

    @click_hotoffthehamster.command()
    def cli_float():
        click_hotoffthehamster.echo("hello world")
        sys.exit(1.0)

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli_float_ctx_exit(ctx):
        click_hotoffthehamster.echo("hello world")
        ctx.exit(1.0)

    @click_hotoffthehamster.command()
    def cli_no_error():
        click_hotoffthehamster.echo("hello world")

    runner = CliRunner()

    result = runner.invoke(cli_string)
    assert result.exit_code == 1
    assert result.output == "hello world\nerror\n"

    result = runner.invoke(cli_string_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\nerror\n"

    result = runner.invoke(cli_int)
    assert result.exit_code == 1
    assert result.output == "hello world\n"

    result = runner.invoke(cli_int_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\n"

    result = runner.invoke(cli_float)
    assert result.exit_code == 1
    assert result.output == "hello world\n1.0\n"

    result = runner.invoke(cli_float_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\n1.0\n"

    result = runner.invoke(cli_no_error)
    assert result.exit_code == 0
    assert result.output == "hello world\n"


def test_env():
    @click_hotoffthehamster.command()
    def cli_env():
        click_hotoffthehamster.echo("ENV={}".format(os.environ["TEST_CLICK_ENV"]))

    runner = CliRunner()

    env_orig = dict(os.environ)
    env = dict(env_orig)
    assert "TEST_CLICK_ENV" not in env
    env["TEST_CLICK_ENV"] = "some_value"
    result = runner.invoke(cli_env, env=env)
    assert result.exit_code == 0
    assert result.output == "ENV=some_value\n"

    assert os.environ == env_orig


def test_stderr():
    @click_hotoffthehamster.command()
    def cli_stderr():
        click_hotoffthehamster.echo("stdout")
        click_hotoffthehamster.echo("stderr", err=True)

    runner = CliRunner(mix_stderr=False)

    result = runner.invoke(cli_stderr)

    assert result.output == "stdout\n"
    assert result.stdout == "stdout\n"
    assert result.stderr == "stderr\n"

    runner_mix = CliRunner(mix_stderr=True)
    result_mix = runner_mix.invoke(cli_stderr)

    assert result_mix.output == "stdout\nstderr\n"
    assert result_mix.stdout == "stdout\nstderr\n"

    with pytest.raises(ValueError):
        result_mix.stderr

    @click_hotoffthehamster.command()
    def cli_empty_stderr():
        click_hotoffthehamster.echo("stdout")

    runner = CliRunner(mix_stderr=False)

    result = runner.invoke(cli_empty_stderr)

    assert result.output == "stdout\n"
    assert result.stdout == "stdout\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "args, expected_output",
    [
        (None, "bar\n"),
        ([], "bar\n"),
        ("", "bar\n"),
        (["--foo", "one two"], "one two\n"),
        ('--foo "one two"', "one two\n"),
    ],
)
def test_args(args, expected_output):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.option("--foo", default="bar")
    def cli_args(foo):
        click_hotoffthehamster.echo(foo)

    runner = CliRunner()
    result = runner.invoke(cli_args, args=args)
    assert result.exit_code == 0
    assert result.output == expected_output


def test_setting_prog_name_in_extra():
    @click_hotoffthehamster.command()
    def cli():
        click_hotoffthehamster.echo("ok")

    runner = CliRunner()
    result = runner.invoke(cli, prog_name="foobar")
    assert not result.exception
    assert result.output == "ok\n"
