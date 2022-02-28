from unittest.mock import call, create_autospec

import pytest

from rich._win32_console import LegacyWindowsTerm, WindowsCoordinates
from rich._windows_renderer import legacy_windows_render
from rich.segment import ControlType, Segment
from rich.style import Style


@pytest.fixture
def legacy_term_mock():
    return create_autospec(LegacyWindowsTerm)


def test_text_only(legacy_term_mock):
    text = "Hello, world!"
    buffer = [Segment(text)]
    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.write_text.assert_called_once_with(text)


def test_text_multiple_segments(legacy_term_mock):
    buffer = [Segment("Hello, "), Segment("world!")]
    legacy_windows_render(buffer, legacy_term_mock)

    assert legacy_term_mock.write_text.call_args_list == [
        call("Hello, "),
        call("world!"),
    ]


def test_text_with_style(legacy_term_mock):
    text = "Hello, world!"
    style = Style.parse("black on red")
    buffer = [Segment(text, style)]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.write_styled.assert_called_once_with(text, style)


def test_control_cursor_move_to(legacy_term_mock):
    buffer = [Segment("", None, [(ControlType.CURSOR_MOVE_TO, 20, 30)])]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.move_cursor_to.assert_called_once_with(
        WindowsCoordinates(row=29, col=19)
    )


def test_control_carriage_return(legacy_term_mock):
    buffer = [Segment("", None, [(ControlType.CARRIAGE_RETURN,)])]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.write_text.assert_called_once_with("\r")


def test_control_home(legacy_term_mock):
    buffer = [Segment("", None, [(ControlType.HOME,)])]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.move_cursor_to.assert_called_once_with(WindowsCoordinates(0, 0))


def test_control_cursor_up(legacy_term_mock):
    buffer = [Segment("", None, [(ControlType.CURSOR_UP,)])]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.move_cursor_up.assert_called_once_with()


def test_control_erase_to_end_of_line(legacy_term_mock):
    buffer = [Segment("", None, [(ControlType.ERASE_IN_LINE, 0)])]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.erase_end_of_line.assert_called_once_with()


# def test_control_erase_to_start_of_line(legacy_term_mock):
#     buffer = [Segment("", None, [(ControlType.ERASE_IN_LINE, 1)])]
#
#     legacy_windows_render(buffer, legacy_term_mock)
#
#     legacy_term_mock.erase_start_of_line.assert_called_once_with()


def test_control_erase_whole_line(legacy_term_mock):
    buffer = [Segment("", None, [(ControlType.ERASE_IN_LINE, 2)])]

    legacy_windows_render(buffer, legacy_term_mock)

    legacy_term_mock.erase_line.assert_called_once_with()
