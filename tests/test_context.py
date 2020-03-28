# -*- coding: utf-8 -*-
import pytest

import click_hotoffthehamster
from click_hotoffthehamster.core import ParameterSource


def test_ensure_context_objects(runner):
    class Foo(object):
        def __init__(self):
            self.title = "default"

    pass_foo = click_hotoffthehamster.make_pass_decorator(Foo, ensure=True)

    @click_hotoffthehamster.group()
    @pass_foo
    def cli(foo):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click_hotoffthehamster.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "default\n"


def test_get_context_objects(runner):
    class Foo(object):
        def __init__(self):
            self.title = "default"

    pass_foo = click_hotoffthehamster.make_pass_decorator(Foo, ensure=True)

    @click_hotoffthehamster.group()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = "test"

    @cli.command()
    @pass_foo
    def test(foo):
        click_hotoffthehamster.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_get_context_objects_no_ensuring(runner):
    class Foo(object):
        def __init__(self):
            self.title = "default"

    pass_foo = click_hotoffthehamster.make_pass_decorator(Foo)

    @click_hotoffthehamster.group()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = "test"

    @cli.command()
    @pass_foo
    def test(foo):
        click_hotoffthehamster.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_get_context_objects_missing(runner):
    class Foo(object):
        pass

    pass_foo = click_hotoffthehamster.make_pass_decorator(Foo)

    @click_hotoffthehamster.group()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click_hotoffthehamster.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert result.exception is not None
    assert isinstance(result.exception, RuntimeError)
    assert (
        "Managed to invoke callback without a context object of type"
        " 'Foo' existing" in str(result.exception)
    )


def test_multi_enter(runner):
    called = []

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        def callback():
            called.append(True)

        ctx.call_on_close(callback)

        with ctx:
            pass
        assert not called

    result = runner.invoke(cli, [])
    assert result.exception is None
    assert called == [True]


def test_global_context_object(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        assert click_hotoffthehamster.get_current_context() is ctx
        ctx.obj = "FOOBAR"
        assert click_hotoffthehamster.get_current_context().obj == "FOOBAR"

    assert click_hotoffthehamster.get_current_context(silent=True) is None
    runner.invoke(cli, [], catch_exceptions=False)
    assert click_hotoffthehamster.get_current_context(silent=True) is None


def test_context_meta(runner):
    LANG_KEY = "{}.lang".format(__name__)

    def set_language(value):
        click_hotoffthehamster.get_current_context().meta[LANG_KEY] = value

    def get_language():
        return click_hotoffthehamster.get_current_context().meta.get(LANG_KEY, "en_US")

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        assert get_language() == "en_US"
        set_language("de_DE")
        assert get_language() == "de_DE"

    runner.invoke(cli, [], catch_exceptions=False)


def test_context_pushing():
    rv = []

    @click_hotoffthehamster.command()
    def cli():
        pass

    ctx = click_hotoffthehamster.Context(cli)

    @ctx.call_on_close
    def test_callback():
        rv.append(42)

    with ctx.scope(cleanup=False):
        # Internal
        assert ctx._depth == 2

    assert rv == []

    with ctx.scope():
        # Internal
        assert ctx._depth == 1

    assert rv == [42]


def test_pass_obj(runner):
    @click_hotoffthehamster.group()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.obj = "test"

    @cli.command()
    @click_hotoffthehamster.pass_obj
    def test(obj):
        click_hotoffthehamster.echo(obj)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_close_before_pop(runner):
    called = []

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.obj = "test"

        @ctx.call_on_close
        def foo():
            assert click_hotoffthehamster.get_current_context().obj == "test"
            called.append(True)

        click_hotoffthehamster.echo("aha!")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "aha!\n"
    assert called == [True]


def test_make_pass_decorator_args(runner):
    """
    Test to check that make_pass_decorator doesn't consume arguments based on
    invocation order.
    """

    class Foo(object):
        title = "foocmd"

    pass_foo = click_hotoffthehamster.make_pass_decorator(Foo)

    @click_hotoffthehamster.group()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.obj = Foo()

    @cli.command()
    @click_hotoffthehamster.pass_context
    @pass_foo
    def test1(foo, ctx):
        click_hotoffthehamster.echo(foo.title)

    @cli.command()
    @pass_foo
    @click_hotoffthehamster.pass_context
    def test2(ctx, foo):
        click_hotoffthehamster.echo(foo.title)

    result = runner.invoke(cli, ["test1"])
    assert not result.exception
    assert result.output == "foocmd\n"

    result = runner.invoke(cli, ["test2"])
    assert not result.exception
    assert result.output == "foocmd\n"


def test_exit_not_standalone():
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.exit(1)

    assert cli.main([], "test_exit_not_standalone", standalone_mode=False) == 1

    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    def cli(ctx):
        ctx.exit(0)

    assert cli.main([], "test_exit_not_standalone", standalone_mode=False) == 0


def test_parameter_source_default(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    @click_hotoffthehamster.option("-o", "--option", default=1)
    def cli(ctx, option):
        click_hotoffthehamster.echo(ctx.get_parameter_source("option"))

    rv = runner.invoke(cli)
    assert rv.output.rstrip() == ParameterSource.DEFAULT


def test_parameter_source_default_map(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    @click_hotoffthehamster.option("-o", "--option", default=1)
    def cli(ctx, option):
        click_hotoffthehamster.echo(ctx.get_parameter_source("option"))

    rv = runner.invoke(cli, default_map={"option": 1})
    assert rv.output.rstrip() == ParameterSource.DEFAULT_MAP


def test_parameter_source_commandline(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    @click_hotoffthehamster.option("-o", "--option", default=1)
    def cli(ctx, option):
        click_hotoffthehamster.echo(ctx.get_parameter_source("option"))

    rv = runner.invoke(cli, ["-o", "1"])
    assert rv.output.rstrip() == ParameterSource.COMMANDLINE
    rv = runner.invoke(cli, ["--option", "1"])
    assert rv.output.rstrip() == ParameterSource.COMMANDLINE


def test_parameter_source_environment(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    @click_hotoffthehamster.option("-o", "--option", default=1)
    def cli(ctx, option):
        click_hotoffthehamster.echo(ctx.get_parameter_source("option"))

    rv = runner.invoke(cli, auto_envvar_prefix="TEST", env={"TEST_OPTION": "1"})
    assert rv.output.rstrip() == ParameterSource.ENVIRONMENT


def test_parameter_source_environment_variable_specified(runner):
    @click_hotoffthehamster.command()
    @click_hotoffthehamster.pass_context
    @click_hotoffthehamster.option("-o", "--option", default=1, envvar="NAME")
    def cli(ctx, option):
        click_hotoffthehamster.echo(ctx.get_parameter_source("option"))

    rv = runner.invoke(cli, env={"NAME": "1"})
    assert rv.output.rstrip() == ParameterSource.ENVIRONMENT


def test_validate_parameter_source():
    with pytest.raises(ValueError):
        ParameterSource.validate("NOT_A_VALID_PARAMETER_SOURCE")
