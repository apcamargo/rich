"""Light wrapper around the win32 Console API"""
import sys
import time
from ctypes.wintypes import BOOL, DWORD
from typing import NamedTuple
from typing.io import IO

from rich.color import ColorSystem
from rich.style import Style
from rich.text import Text

try:
    import ctypes
    from ctypes import LibraryLoader, Structure, Union, byref, wintypes

    if sys.platform == "win32":
        windll = LibraryLoader(ctypes.WinDLL)
    else:
        windll = None
        raise ImportError("Not windows")
except:
    windll = None
else:
    STDOUT = -11
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 4

    kernel32 = windll.kernel32
    COORD = wintypes._COORD

    class WindowsCoordinates(NamedTuple):
        """Coordinates in the Windows Console API are (y, x), not (x, y).
        This class is intended to prevent that confusion.
        Rows and columns are indexed from 0.
        This class can be used in place of wintypes._COORD in arguments and argtypes.
        """

        row: int
        col: int

        @classmethod
        def from_param(cls, value: "WindowsCoordinates") -> COORD:
            return COORD(value.col, value.row)

    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", wintypes.WORD),
            ("srWindow", wintypes.SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]

    class CONSOLE_CURSOR_INFO(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("bVisible", wintypes.BOOL)]

    _GetStdHandle = kernel32.GetStdHandle
    _GetStdHandle.argtypes = [
        wintypes.DWORD,
    ]
    _GetStdHandle.restype = wintypes.HANDLE

    def GetStdHandle(handle: int = STDOUT) -> wintypes.HANDLE:
        return _GetStdHandle(handle)

    _GetConsoleMode = kernel32.GetConsoleMode
    _GetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.LPDWORD]
    _GetConsoleMode.restype = wintypes.BOOL

    def GetConsoleMode(
        std_handle: wintypes.HANDLE, console_mode: wintypes.DWORD
    ) -> bool:
        return _GetConsoleMode(std_handle, console_mode)

    _FillConsoleOutputCharacterW = windll.kernel32.FillConsoleOutputCharacterW
    _FillConsoleOutputCharacterW.argtypes = [
        wintypes.HANDLE,
        ctypes.c_char,
        wintypes.DWORD,
        WindowsCoordinates,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _FillConsoleOutputCharacterW.restype = wintypes.BOOL

    def FillConsoleOutputCharacter(
        std_handle: wintypes.HANDLE,
        char: str,
        length: int,
        start: WindowsCoordinates,
    ) -> int:
        """Writes a character to the console screen buffer a specified number of times, beginning at the specified coordinates."""
        assert len(char) == 1
        char = ctypes.c_char(char.encode())
        length = wintypes.DWORD(length)
        num_written = wintypes.DWORD(0)
        x, y = start
        _FillConsoleOutputCharacterW(
            std_handle,
            char,
            length,
            WindowsCoordinates(row=y, col=x),
            byref(num_written),
        )
        return num_written.value

    _FillConsoleOutputAttribute = windll.kernel32.FillConsoleOutputAttribute
    _FillConsoleOutputAttribute.argtypes = [
        wintypes.HANDLE,
        wintypes.WORD,
        wintypes.DWORD,
        WindowsCoordinates,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _FillConsoleOutputAttribute.restype = wintypes.BOOL

    def FillConsoleOutputAttribute(
        std_handle: wintypes.HANDLE,
        attributes: int,
        length: int,
        start: WindowsCoordinates,
    ) -> int:
        length = wintypes.DWORD(length)
        attributes = wintypes.WORD(attributes)
        num_written = wintypes.DWORD(0)
        _FillConsoleOutputAttribute(
            std_handle, attributes, length, start, byref(num_written)
        )
        return num_written.value

    _SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
    _SetConsoleTextAttribute.argtypes = [
        wintypes.HANDLE,
        wintypes.WORD,
    ]
    _SetConsoleTextAttribute.restype = wintypes.BOOL

    def SetConsoleTextAttribute(
        std_handle: wintypes.HANDLE, attributes: wintypes.WORD
    ) -> bool:
        # TODO: Check the actual return types - it probably isn't a bool, will likely be wintypes.BOOL
        return _SetConsoleTextAttribute(std_handle, attributes)

    _GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
    _GetConsoleScreenBufferInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO),
    ]
    _GetConsoleScreenBufferInfo.restype = wintypes.BOOL

    def GetConsoleScreenBufferInfo(
        std_handle: wintypes.HANDLE,
    ) -> CONSOLE_SCREEN_BUFFER_INFO:
        console_screen_buffer_info = CONSOLE_SCREEN_BUFFER_INFO()
        _GetConsoleScreenBufferInfo(std_handle, byref(console_screen_buffer_info))
        return console_screen_buffer_info

    _SetConsoleCursorPosition = windll.kernel32.SetConsoleCursorPosition
    _SetConsoleCursorPosition.argtypes = [
        wintypes.HANDLE,
        WindowsCoordinates,
    ]
    _SetConsoleCursorPosition.restype = wintypes.BOOL

    def SetConsoleCursorPosition(
        std_handle: wintypes.HANDLE, coords: WindowsCoordinates
    ) -> bool:
        if coords.col < 0 or coords.row < 0:
            return False
        return _SetConsoleCursorPosition(std_handle, coords)

    _SetConsoleCursorInfo = windll.kernel32.SetConsoleCursorInfo
    _SetConsoleCursorInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(CONSOLE_CURSOR_INFO),
    ]
    _SetConsoleCursorInfo.restype = wintypes.BOOL

    def SetConsoleCursorInfo(
        std_handle: wintypes.HANDLE, cursor_info: CONSOLE_CURSOR_INFO
    ) -> wintypes.BOOL:
        return _SetConsoleCursorInfo(std_handle, byref(cursor_info))

    _SetConsoleTitle = windll.kernel32.SetConsoleTitleW
    _SetConsoleTitle.argtypes = [wintypes.LPCWSTR]
    _SetConsoleTitle.restype = wintypes.BOOL

    def SetConsoleTitle(title: str) -> wintypes.BOOL:
        return _SetConsoleTitle(title)

    class LegacyWindowsTerm:
        """This class allows interaction with the legacy Windows Console API. It should only be used in the context
        of environments where virtual terminal processing is not available. However, if it is used in a Windows environment,
        the entire API should work.

        Args:
            file (IO[str]): The file which the Windows Console API HANDLE is retrieved from, defaults to sys.stdout.
        """

        # Indices are ANSI color numbers, values are the corresponding Windows Console API color numbers
        ANSI_TO_WINDOWS = [
            0,  # black                      The Windows colours are defined in wincon.h as follows:
            4,  # red                         define FOREGROUND_BLUE            0x0001 -- 0000 0001
            2,  # green                       define FOREGROUND_GREEN           0x0002 -- 0000 0010
            6,  # yellow                      define FOREGROUND_RED             0x0004 -- 0000 0100
            1,  # blue                        define FOREGROUND_INTENSITY       0x0008 -- 0000 1000
            5,  # magenta                     define BACKGROUND_BLUE            0x0010 -- 0001 0000
            3,  # cyan                        define BACKGROUND_GREEN           0x0020 -- 0010 0000
            7,  # white                       define BACKGROUND_RED             0x0040 -- 0100 0000
            8,  # bright black (grey)         define BACKGROUND_INTENSITY       0x0080 -- 1000 0000
            12,  # bright red
            10,  # bright green
            14,  # bright yellow
            9,  # bright blue
            13,  # bright magenta
            11,  # bright cyan
            15,  # bright white
        ]

        def __init__(self, file: IO[str] = sys.stdout):
            self.file = file
            handle = GetStdHandle(STDOUT)
            self._handle = handle
            default_text = GetConsoleScreenBufferInfo(handle).wAttributes
            self._default_text = default_text

            self._default_fore = default_text & 7
            self._default_back = (default_text >> 4) & 7
            self._default_attrs = self._default_fore + self._default_back * 16

            self.write = file.write
            self.flush = file.flush

        @property
        def cursor_position(self) -> WindowsCoordinates:
            """Returns the current position of the cursor (0-based)"""
            coord: COORD = GetConsoleScreenBufferInfo(self._handle).dwCursorPosition
            return WindowsCoordinates(row=coord.Y, col=coord.X)

        @property
        def screen_size(self) -> WindowsCoordinates:
            """Returns the current size of the console screen buffer, in character columns and rows"""
            screen_size: COORD = GetConsoleScreenBufferInfo(self._handle).dwSize
            return WindowsCoordinates(row=screen_size.Y, col=screen_size.X)

        def write_text(self, text: str) -> None:
            """Write text directly to the terminal without any modification of styles"""
            self.write(text)
            self.flush()

        def write_styled(self, text: str, style: Style) -> None:
            """Write styled text to the terminal"""
            # TODO: Check for bold, bright, etc. inside the style
            if style.color:
                fore = style.color.downgrade(ColorSystem.WINDOWS).number
                fore = fore if fore is not None else 7  # Default to ANSI 7: White
                fore = self.ANSI_TO_WINDOWS[fore]
            else:
                fore = self._default_fore

            if style.bgcolor:
                back = style.bgcolor.downgrade(ColorSystem.WINDOWS).number
                back = back if back is not None else 0  # Default to ANSI 0: Black
                back = self.ANSI_TO_WINDOWS[back]
            else:
                back = self._default_back

            SetConsoleTextAttribute(
                self._handle, attributes=ctypes.c_ushort(fore + back * 16)
            )
            self.write_text(text)
            SetConsoleTextAttribute(self._handle, attributes=self._default_text)

        def move_cursor_to(self, new_position: WindowsCoordinates) -> None:
            """Set the position of the cursor"""
            SetConsoleCursorPosition(self._handle, new_position)

        def erase_line(self) -> None:
            """Erase all content on the line the cursor is currently located at"""
            screen_size = self.screen_size
            cursor_position = self.cursor_position
            cells_to_erase = screen_size.col
            start_coordinates = WindowsCoordinates(cursor_position.row, 0)
            FillConsoleOutputCharacter(
                self._handle, " ", cells_to_erase, start_coordinates
            )

        def erase_end_of_line(self) -> None:
            """Erase all content from the cursor position to the end of that line"""
            cursor_position = self.cursor_position
            cells_to_erase = self.screen_size.col - cursor_position.col
            FillConsoleOutputCharacter(
                self._handle, " ", cells_to_erase, cursor_position
            )

        def erase_start_of_line(self) -> None:
            """Erase all content from the cursor position to the start of that line"""
            cursor_position = self.cursor_position
            cells_to_erase = self.screen_size.col - cursor_position.col
            FillConsoleOutputCharacter(
                self._handle, " ", cells_to_erase, cursor_position
            )

        def move_cursor_up(self) -> None:
            """Move the cursor up a single cell"""
            cursor_position = self.cursor_position
            SetConsoleCursorPosition(
                self._handle,
                WindowsCoordinates(
                    row=cursor_position.row - 1, col=cursor_position.col
                ),
            )

        def move_cursor_down(self) -> None:
            """Move the cursor down a single cell"""
            cursor_position = self.cursor_position
            SetConsoleCursorPosition(
                self._handle,
                WindowsCoordinates(
                    row=cursor_position.row + 1,
                    col=cursor_position.col,
                ),
            )

        def move_cursor_forward(self) -> None:
            """Move the cursor forward a single cell. Wrap to the next line if required."""
            row, col = self.cursor_position
            if col == self.screen_size.col - 1:
                row += 1
                col = 0
            else:
                col += 1
            SetConsoleCursorPosition(self._handle, WindowsCoordinates(row=row, col=col))

        def move_cursor_backward(self) -> None:
            """Move the cursor backward a single cell. Wrap to the previous line if required."""
            row, col = self.cursor_position
            if col == 0:
                row -= 1
                col = self.screen_size.col - 1
            else:
                col -= 1
            SetConsoleCursorPosition(self._handle, WindowsCoordinates(row=row, col=col))

        def hide_cursor(self) -> None:
            """Hide the cursor"""
            blank_cursor = CONSOLE_CURSOR_INFO()
            blank_cursor.dwSize = 100
            blank_cursor.bVisible = 0
            SetConsoleCursorInfo(self._handle, blank_cursor)

        def show_cursor(self) -> None:
            """Show the cursor"""
            visible_cursor = CONSOLE_CURSOR_INFO()
            visible_cursor.dwSize = 100
            visible_cursor.bVisible = 1
            SetConsoleCursorInfo(self._handle, visible_cursor)

        def set_title(self, title: str) -> None:
            """Set the title of the terminal window"""
            assert len(title) < 255, "Console title must be less than 255 characters"
            _SetConsoleTitle(title)

    if __name__ == "__main__":
        handle = GetStdHandle()
        console_mode = wintypes.DWORD()
        GetConsoleMode(handle, console_mode)

        from rich.console import Console

        console = Console()

        term = LegacyWindowsTerm(console.file)
        term.set_title("Win32 Console Examples")

        style = Style(color="black", bgcolor="red")

        text = Text("Hello world!", style=style)
        console.print(text)
        console.print("[bold green]bold green!")
        console.print("[italic cyan]italic cyan!")
        console.print("[bold white on blue]bold white on blue!")
        console.print("[bold black on cyan]bold black on cyan!")
        term.hide_cursor()
        console.print("[black on green]black on green!")
        console.print("[blue on green]blue on green!")
        console.print("[white on black]white on black!")
        console.print("[black on white]black on white!")
        console.print("[#1BB152 on #DA812D]#1BB152 on #DA812D!")

        term.move_cursor_backward()
        term.move_cursor_backward()
        term.write_text("went back and wrapped up")
        time.sleep(1)
        term.move_cursor_down()
        term.write_text("now down")
        time.sleep(1)
        term.move_cursor_up()
        term.write_text("and up")
        time.sleep(1)
        term.show_cursor()
        term.move_cursor_down()
        term.write_text("and down")
        time.sleep(1)
        term.move_cursor_up()
        term.move_cursor_backward()
        term.move_cursor_backward()
        term.write_text("we went up and back 2")
        time.sleep(1)
        term.move_cursor_down()
        term.move_cursor_backward()
        term.move_cursor_backward()
        term.write_text("we went down and back 2")

        print("\n")
