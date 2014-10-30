from pytest import raises
import mock

from retrypy import retry


class CallCounter(object):
    def __init__(self, calls=0, errors=0):
        self.calls = calls
        self.errors = errors

    def __eq__(self, other):
        return other.calls == self.calls and other.errors == self.errors


def get_dummy_func(raise_count=4):
    counter = CallCounter()

    def func(*args, **kwargs):
        counter.calls += 1
        if counter.errors < raise_count:
            counter.errors += 1
            raise Exception('Test Error {count}'.format(count=counter.errors))
        return counter, args, kwargs
    return func


def test_func_with_no_args():
    result = retry.call(get_dummy_func(0))
    assert result == (CallCounter(1, 0), (), {})


def test_retry_func_with_no_args():
    result = retry.call(get_dummy_func())
    assert result == (CallCounter(5, 4), (), {})


def test_func_that_raises_too_many_time_raises():
    with raises(Exception) as e:
        retry.call(get_dummy_func(50))
    assert str(e.value) == 'Test Error 5'


def test_func_that_passes_check_does_not_raise():
    result = retry.call(
        get_dummy_func(),
        check=lambda e, c: True,
    )
    assert result == (CallCounter(5, 4), (), {})


def test_func_that_fails_check_raises():
    with raises(Exception) as e:
        retry.call(
            get_dummy_func(5),
            check=lambda e, c: not str(e).endswith('3'),
        )
    assert str(e.value) == 'Test Error 3'


def test_func_that_raises_wrong_exception_type_should_raise():
    with raises(Exception) as e:
        retry.call(
            get_dummy_func(5),
            exceptions=[TypeError],
        )
    assert str(e.value) == 'Test Error 1'


def test_func_with_positional_arg():
    assert retry.call(lambda x: x, args=['bar']) == 'bar'


def test_retry_func_with_postional_arg():
    result = retry.call(get_dummy_func(), args=['foo'])
    assert result == (CallCounter(5, 4), ('foo',), {})


def test_func_with_kwargs():
    result = retry.call(get_dummy_func(0), kwargs={'foo': 'bar'})
    assert result == (CallCounter(1), (), {'foo': 'bar'})


def test_retry_func_with_kwarg():
    result = retry.call(get_dummy_func(), kwargs={'foo': 'bar'})
    assert result == (CallCounter(5, 4), (), {'foo': 'bar'})


def test_decorated_func_with_no_args():
    func = get_dummy_func(0)

    @retry.decorate()
    def foo():
        return func()

    assert foo() == (CallCounter(1, 0), (), {})


def test_retry_decorated_func_with_no_args():
    func = get_dummy_func()

    @retry.decorate()
    def foo():
        return func()

    assert foo() == (CallCounter(5, 4), (), {})


def test_decorated_func_with_positional_arg():
    func = get_dummy_func(0)

    @retry.decorate()
    def foo(arg):
        return func(arg)

    assert foo('arg') == (CallCounter(1, 0), ('arg',), {})


def test_retry_decorated_func_with_positional_arg():
    func = get_dummy_func()

    @retry.decorate()
    def foo(arg):
        return func(arg)

    assert foo('arg') == (CallCounter(5, 4), ('arg',), {})


def test_decorated_func_with_kwargs():
    func = get_dummy_func(0)

    @retry.decorate()
    def foo(**kwargs):
        return func(**kwargs)

    assert foo(foo='bar') == (CallCounter(1), (), {'foo': 'bar'})


def test_retry_decorated_func_with_kwargs():
    func = get_dummy_func()

    @retry.decorate()
    def foo(**kwargs):
        return func(**kwargs)

    assert foo(foo='bar') == (CallCounter(5, 4), (), {'foo': 'bar'})


def test_retry_wrapped_func_with_kwargs():
    func = get_dummy_func()

    func = retry.wrap(get_dummy_func())

    assert func(foo='bar') == (CallCounter(5, 4), (), {'foo': 'bar'})


def test_decorated_func_that_raises_too_many_time_raises():
    func = get_dummy_func(50)

    @retry.decorate()
    def foo():
        return func()

    with raises(Exception) as e:
        foo()
    assert str(e.value) == 'Test Error 5'


def test_decorated_func_that_raises_wrong_exception_type_should_raise():
    func = get_dummy_func(50)

    @retry.decorate(TypeError)
    def foo():
        return func()

    with raises(Exception) as e:
        foo()
    assert str(e.value) == 'Test Error 1'


@mock.patch('retrypy.retry.sleep')
def test_retry_with_wait_function(mock_sleep):
    retry.call(get_dummy_func(), wait=lambda n: n)
    mock_sleep.assert_called_with(3)
