from typing import Iterable, Sequence

from rich._win32_console import LegacyWindowsTerm, WindowsCoordinates
from rich.segment import ControlCode, ControlType, Segment


def legacy_windows_render(buffer: Iterable[Segment], term: LegacyWindowsTerm) -> None:
    for segment in buffer:
        text, style, control = segment

        if not control:
            if style:
                term.write_styled(text, segment.style)
            else:
                term.write_text(text)
        else:
            control_codes: Sequence[ControlCode] = control
            for control_code in control_codes:
                control_type = control_code[0]
                if control_type == ControlType.CURSOR_MOVE_TO:
                    _, x, y = control_code
                    term.move_cursor_to(WindowsCoordinates(row=y - 1, col=x - 1))
                elif control_type == ControlType.CARRIAGE_RETURN:
                    term.write_text("\r")
                elif control_type == ControlType.HOME:
                    term.move_cursor_to(WindowsCoordinates(0, 0))
                elif control_type == ControlType.CURSOR_UP:
                    term.move_cursor_up()
                elif control_type == ControlType.CURSOR_DOWN:
                    term.move_cursor_down()
                elif control_type == ControlType.CURSOR_FORWARD:
                    term.move_cursor_forward()
                elif control_type == ControlType.CURSOR_BACKWARD:
                    term.move_cursor_backward()
                elif control_type == ControlType.HIDE_CURSOR:
                    term.hide_cursor()
                elif control_type == ControlType.SHOW_CURSOR:
                    term.show_cursor()
                elif control_type == ControlType.ERASE_IN_LINE:
                    _, mode = control_code
                    if mode == 0:
                        term.erase_end_of_line()
                    elif mode == 1:
                        # TODO
                        term.erase_start_of_line()
                    elif mode == 2:
                        term.erase_line()
