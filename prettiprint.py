# --- add to ConsoleConfig (new option) ---
@dataclass
class ConsoleConfig:
    theme: str = "dark"
    emoji: bool = True
    timestamps: bool = True
    verbosity: int = 1
    enable_tracebacks: bool = True
    message_spacing: Union[int, str] = 0  # NEW: spacer after messages (0 disables)


class ConsoleUtils:
    def __init__(
        self,
        theme: str = "dark",
        *,
        emoji: bool = True,
        timestamps: bool = True,
        verbosity: int = 1,
        enable_tracebacks: bool = True,
        custom_styles: Optional[dict] = None,
        message_spacing: Union[int, str] = 0,  # NEW
        emoji_gap: str = " ",                  # NEW: spacing between emoji and text
    ) -> None:
        if enable_tracebacks:
            install_rich_traceback(show_locals=False)

        theme_name = theme.lower()
        if theme_name not in _PRESET_THEMES:
            raise ValueError(
                f"Unknown theme '{theme}'. Choose from: {', '.join(_PRESET_THEMES)}"
            )
        merged = {**_PRESET_THEMES[theme_name], **(custom_styles or {})}

        self._console = Console(theme=Theme(merged), emoji=emoji, soft_wrap=False)
        self._styles = merged
        self._config = ConsoleConfig(
            theme=theme_name,
            emoji=emoji,
            timestamps=timestamps,
            verbosity=verbosity,
            enable_tracebacks=enable_tracebacks,
            message_spacing=message_spacing,  # NEW
        )
        self._emoji_gap = emoji_gap  # NEW

    # --- NEW: small internal helper to add consistent spacing after outputs ---
    def _after_print(self) -> None:
        if self._config.verbosity == 0:
            return
        if self._config.message_spacing:
            self.spacer(self._config.message_spacing)

    # --- NEW: helper to optionally prefix emoji with spacing ---
    def _prefix_emoji(self, emoji_char: str) -> str:
        # If config says no emoji, return empty prefix
        if not self._config.emoji:
            return ""
        # ensure a gap between emoji and message
        return f"{emoji_char}{self._emoji_gap}"

    # ---------- Messages ----------
    def success(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        prefix = self._prefix_emoji("✅")
        self._console.print(
            f"{prefix}[{self._styles['success']}]{message}[/{self._styles['success']}]"
        )
        self._after_print()  # NEW

    def info(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        prefix = self._prefix_emoji("ℹ️")
        self._console.print(
            f"{prefix}[{self._styles['info']}]{message}[/{self._styles['info']}]"
        )
        self._after_print()  # NEW

    def warning(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        prefix = self._prefix_emoji("⚠️")
        self._console.print(
            f"{prefix}[{self._styles['warning']}]{message}[/{self._styles['warning']}]"
        )
        self._after_print()  # NEW

    def error(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        prefix = self._prefix_emoji("❌")
        self._console.print(
            f"{prefix}[{self._styles['error']}]{message}[/{self._styles['error']}]"
        )
        self._after_print()  # NEW

    def event(self, message: str, level: str = "INFO") -> None:
        if self._config.verbosity == 0:
            return
        lvl = level.upper()

        # hide all events at verbosity 1
        if self._config.verbosity < 2:
            return

        # hide all DEBUG events at verbosity 2
        if self._config.verbosity < 3 and lvl == "DEBUG":
            return

        ts = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self._config.timestamps
            else ""
        )
        color = self._styles.get(f"event.{lvl}", self._styles["info"])
        prefix = f"[{ts}] {lvl:<7} " if ts else f"{lvl:<7} "
        self._console.print(f"[{color}]{prefix}[/]{message}")
        self._after_print()  # NEW

    # --- If you want the same “post spacing” for structural outputs too, add this ---
    def header(self, msg: str, *, style: Optional[str] = None) -> None:
        if self._config.verbosity == 0:
            return
        style = style or "bold cyan"
        self.spacer()
        self._console.rule(f"[{style}]{msg}[/]")
        self.spacer()
        self._after_print()  # optional (NEW)


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence, Union

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.traceback import install as install_rich_traceback
from rich.markdown import Markdown
from rich.tree import Tree
from rich.syntax import Syntax
from rich import box

# ---------- Theme Presets ----------
_PRESET_THEMES = {
    "dark": {
        "accent": "bold white on #3b82f6",
        "rule": "dim",
        "success": "bold green",
        "info": "bold cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "panel": "cyan",
        "header": "bold white on #0ea5e9",
        "table.header": "bold magenta",
        "key": "bold green",
        "value": "white",
        "code.border": "magenta",
        "event.INFO": "cyan",
        "event.SUCCESS": "green",
        "event.WARNING": "yellow",
        "event.ERROR": "red",
    },
    "light": {
        "accent": "bold black on #93c5fd",
        "rule": "grey66",
        "success": "green",
        "info": "blue",
        "warning": "dark_orange",
        "error": "red",
        "panel": "blue",
        "header": "bold black on #7dd3fc",
        "table.header": "bold purple",
        "key": "blue",
        "value": "black",
        "code.border": "purple",
        "event.INFO": "blue",
        "event.SUCCESS": "green",
        "event.WARNING": "dark_orange",
        "event.ERROR": "red",
    },
    "mono": {
        "accent": "reverse",
        "rule": "dim",
        "success": "bold",
        "info": "bold",
        "warning": "bold",
        "error": "bold",
        "panel": "white",
        "header": "reverse",
        "table.header": "bold",
        "key": "bold",
        "value": "white",
        "code.border": "white",
        "event.INFO": "white",
        "event.SUCCESS": "white",
        "event.WARNING": "white",
        "event.ERROR": "white",
    },
}


@dataclass
class ConsoleConfig:
    theme: str = "dark"
    emoji: bool = True
    timestamps: bool = True
    verbosity: int = 1
    enable_tracebacks: bool = True


class ConsoleUtils:
    """
    Instantiable Rich console helper with theming, styling, and verbosity
    """

    def __init__(
        self,
        theme: str = "dark",
        *,
        emoji: bool = True,
        timestamps: bool = True,
        verbosity: int = 1,
        enable_tracebacks: bool = True,
        custom_styles: Optional[dict] = None,
    ) -> None:
        if enable_tracebacks:
            install_rich_traceback(show_locals=False)

        theme_name = theme.lower()
        if theme_name not in _PRESET_THEMES:
            raise ValueError(
                f"Unknown theme '{theme}'. Choose from: {', '.join(_PRESET_THEMES)}"
            )
        merged = {**_PRESET_THEMES[theme_name], **(custom_styles or {})}

        self._console = Console(theme=Theme(merged), emoji=emoji, soft_wrap=False)
        self._styles = merged
        self._config = ConsoleConfig(
            theme=theme_name,
            emoji=emoji,
            timestamps=timestamps,
            verbosity=verbosity,
            enable_tracebacks=enable_tracebacks,
        )

    # ---------- Static-ish helpers ----------
    @staticmethod
    def mask_secret(secret: str, keep: int = 3, mask: str = "*") -> str:
        """
        Mask a secret by *keeping the first `keep` characters visible*
        and masking the remainder.
        """
        if not isinstance(secret, str):
            secret = str(secret)
        if keep <= 0:
            return mask * len(secret)
        if len(secret) <= keep:
            return secret
        return secret[:keep] + (mask * (len(secret) - keep))

    # ---------- Config ----------
    @property
    def console(self) -> Console:
        return self._console

    def set_theme(self, theme: str, custom_styles: Optional[dict] = None) -> None:
        name = theme.lower()
        if name not in _PRESET_THEMES:
            raise ValueError(
                f"Unknown theme '{theme}'. Choose from: {', '.join(_PRESET_THEMES)}"
            )
        merged = {**_PRESET_THEMES[name], **(custom_styles or {})}
        self._styles = merged
        self._console = Console(
            theme=Theme(merged), emoji=self._config.emoji, soft_wrap=False
        )
        self._config.theme = name

    def set_verbosity(self, level: int) -> None:
        self._config.verbosity = max(0, min(3, level))

    # ---------- Structure ----------
    def header(self, msg: str, *, style: Optional[str] = None) -> None:
        if self._config.verbosity == 0:
            return
        style = style or "bold cyan"
        self.spacer()
        self._console.rule(f"[{style}]{msg}[/]")
        self.spacer()

    def rule(
        self,
        label: str = "",
        *,
        label_style: Optional[str] = None,
        line_style: Optional[str] = None,
    ) -> None:
        if self._config.verbosity == 0:
            return

        # Default styles from theme if not provided
        label_style = label_style or "#cccccc"
        line_style = line_style or self._styles.get("rule", "dim")

        # If label present, apply styling
        if label:
            styled_label = f"[{label_style}]{label}[/{label_style}]"
            self._console.rule(styled_label, style=line_style)
        else:
            self._console.rule(style=line_style)

    def spacer(self, size: Union[int, str] = 1) -> None:
        """Add visual spacing between console elements.

        Args:
            size (int or str, optional): Number of lines to add, integer or keywords i.e., small=1, medium=2, large=3. Defaults to 1.
        """
        if size in ("small", "s"):
            lines = 1
        elif size in ("medium", "m"):
            lines = 2
        elif size in ("large", "l"):
            lines = 3
        else:
            lines = int(size)
        for _ in range(lines):
            self._console.print("")

    def panel(
        self,
        message: Union[str, Any],
        *,
        title: Optional[str] = None,
        style: Optional[str] = None,
        border_style: Optional[str] = None,
        box: Union[str, "box.Box", None] = None,
        expand: bool = False,
        padding: Optional[Union[int, tuple]] = None,
    ) -> None:
        """Render a Rich Panel with full control over border/content styles and layout

        Args:
            message (str or renderable object): Content to displayed within panel.

            title (str, optional): Optional title for the panel. Defaults to None.

            style (str, optional): Interior style for the panel (content/background). Defaults to None.

            border_style (str, optional): Style for border line and title (color, bold, etc.). Defaults to None.

            box (str or rich box object): Border shape from rich.box (e.g., ROUNDED, DOUBLE). Defaults to ROUNDED.

            expand (bool, optional): If True, panel expands to the available width. Defaults to False.

            padding (int or tuple, optional): Inner padding of 2 or 4 ints (e.g., 1, (1,3), (1,2,1,2)). Defaults to None.
        """
        if self._config.verbosity == 0:
            return
        panel_kwargs = {
            "title": title,
            "box": self._resolve_box(box),
            "expand": expand,
            "border_style": border_style or self._styles["panel"],
        }

        # Only set 'style' and 'padding' if explicitly provided (interior style)
        if style is not None:
            panel_kwargs["style"] = style

        if padding is not None:
            panel_kwargs["padding"] = padding

        self._console.print(Panel(message, **panel_kwargs))

    def markdown(self, text: str) -> None:
        if self._config.verbosity == 0:
            return
        self._console.print(Markdown(text))

    def code(
        self,
        code: str,
        language: str = "python",
        title: Optional[str] = None,
        wrap: bool = False,
    ) -> None:
        """Syntax-highlighted code block

        Args:
            code (str): Code to be displayed

            language (str, optional): Language code is in. Defaults to "python".

            title (str, optional): Optional title for the panel surrounding the code block. Defaults to None.

            wrap (bool, optional): If True, word wraps the code. Defaults to False.
        """
        if self._config.verbosity == 0:
            return
        syn = Syntax(code, language, line_numbers=True, word_wrap=wrap)
        self._console.print(
            Panel(
                syn,
                title=title,
                border_style=self._styles["code.border"],
                padding=(1, 0),
            )
        )

    # ---------- Messages ----------
    def success(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        self._console.print(
            f"✅ [{self._styles['success']}]{message}[/{self._styles['success']}]"
        )

    def info(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        self._console.print(
            f"ℹ️ [{self._styles['info']}]{message}[/{self._styles['info']}]"
        )

    def warning(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        self._console.print(
            f"⚠️ [{self._styles['warning']}]{message}[/{self._styles['warning']}]"
        )

    def error(self, message: str) -> None:
        if self._config.verbosity == 0:
            return
        self._console.print(
            f"❌ [{self._styles['error']}]{message}[/{self._styles['error']}]"
        )

    def event(self, message: str, level: str = "INFO") -> None:
        if self._config.verbosity == 0:
            return
        lvl = level.upper()

        # hide all events at verbosity 1
        if self._config.verbosity < 2:
            return

        # hide all DEBUG events at verbosity 2
        if self._config.verbosity < 3 and lvl == "DEBUG":
            return
        ts = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self._config.timestamps
            else ""
        )
        color = self._styles.get(f"event.{lvl}", self._styles["info"])
        prefix = f"[{ts}] {lvl:<7} " if ts else f"{lvl:<7} "
        self._console.print(f"[{color}]{prefix}[/]{message}")

    def print_exception(self) -> None:
        self._console.print_exception()

    # ---------- Data ----------
    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
        *,
        title: Optional[str] = None,
        header_style: Optional[str] = None,
        expand: bool = False,
        table_box: box.Box = box.ROUNDED,
    ) -> None:
        if self._config.verbosity == 0:
            return
        t = Table(
            title=title,
            header_style=header_style or self._styles["table.header"],
            expand=expand,
            box=table_box,
        )
        for h in headers:
            t.add_column(str(h))
        for row in rows:
            t.add_row(*[str(c) for c in row])
        self._console.print(t)

    def dictionary(
        self,
        data: Mapping[Any, Any],
        *,
        title: Optional[str] = None,
        expand: bool = True,
    ) -> None:
        """Render key-value mappings

        Args:
            data (Mapping): A collection of items where each item has a unique key and a corresponding value – e.g. a normal Python dictionary like
            ``{'name': 'Alice', 'age': 30}``. Any dict‑like object is accepted.

            title (str, optional): Optional title for the panel surrounding the data. Defaults to None.

            expand (bool, optional): If False, panel surrounding the data only occupies the width required by the data itself. Defaults to True.
        """
        if self._config.verbosity == 0:
            return
        grid = Table.grid(padding=(0, 1))
        grid.add_column("Key", style=self._styles["key"], justify="right")
        grid.add_column("Value", style=self._styles["value"])
        for k, v in data.items():
            grid.add_row(str(k), self._repr_value(v))
        self._console.print(
            Panel(grid, title=title, border_style=self._styles["panel"], expand=expand)
        )

    def json(self, data: Any, *, title: Optional[str] = None) -> None:
        if self._config.verbosity == 0:
            return
        self._console.print(
            Panel(JSON.from_data(data), title=title, border_style=self._styles["panel"])
        )

    def tree(self, obj: Any, *, title: str = "Structure") -> None:
        if self._config.verbosity == 0:
            return
        root = Tree(f"[{self._styles['info']}]{title}[/{self._styles['info']}]")
        self._add_to_tree(root, obj)
        self._console.print(root)

    def key_value(
        self,
        key: str,
        value: str,
        *,
        secret: bool = False,
        keep: int = 3,
        mask: str = "*",
    ) -> None:
        """
        Print 'key: value'
        If secret=True, masks value keeping first `keep` chars.
        """
        if self._config.verbosity == 0:
            return
        display = self.mask_secret(value, keep=keep, mask=mask) if secret else value
        self._console.print(
            f"[{self._styles['key']}]{key}[/]: [{self._styles['value']}]{display}[/]"
        )

    # ---------- Progress / Spinners ----------
    def status(self, text: str):
        return self._console.status(text)

    def progress(
        self,
        transient: bool = True,
        show_speed: bool = True,
        description: str = "",
    ) -> Progress:
        cols = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
        ]
        if show_speed:
            cols += [TimeElapsedColumn(), TimeRemainingColumn()]
        if description:
            cols[1] = TextColumn(f"[progress.description]{description}")
        return Progress(*cols, transient=transient, console=self._console)

    # ---------- Prompts ----------
    def prompt(self, message: str, *, password: bool = False) -> str:
        suffix = " (hidden)" if password else ""
        return self._console.input(f"[{self._styles['accent']}]{message}{suffix}[/] ")

    def confirm(self, message: str, default: bool = True) -> bool:
        hint = "Y/n" if default else "y/N"
        resp = (
            self._console.input(f"[{self._styles['accent']}]{message} [{hint}][/] ")
            .strip()
            .lower()
        )
        if not resp:
            return default
        return resp in {"y", "yes", "true", "1"}

    # ---------- Internals ----------
    def _repr_value(self, v: Any) -> str:
        if isinstance(v, (dict, list, tuple, set)):
            return f"[dim]{type(v).__name__}[/dim] {v}"
        return str(v)

    # ---------- Helpers ----------
    def _add_to_tree(self, node: Tree, obj: Any, name: Optional[str] = None) -> None:
        label = f"[bold]{name}[/bold]" if name is not None else ""
        if isinstance(obj, Mapping):
            branch = node if not label else node.add(label)
            for k, v in obj.items():
                self._add_to_tree(branch, v, name=str(k))
        elif isinstance(obj, (list, tuple, set)):
            branch = node.add(
                label or f"[bold]{type(obj).__name__}[/bold] ({len(obj)})"
            )
            for idx, item in enumerate(obj):
                self._add_to_tree(branch, item, name=str(idx))
        else:
            node.add(f"{label}: {obj}" if label else str(obj))

    def _resolve_box(self, box_like: Union[str, "box.Box", None]) -> "box.Box":
        """
        Accepts a rich.box.Box or a string like 'double', 'heavy', 'rounded', etc.
        Returns a rich.box.Box. Falls back to ROUNDED if unknown.
        """
        if box_like is None:
            return box.ROUNDED
        if isinstance(box_like, box.Box):
            return box_like

        # Normalize string: case-insensitive, allow spaces and hyphens
        key = str(box_like).strip().upper().replace("-", "_").replace(" ", "_")

        # Common names + synonyms
        mapping = {
            "ROUNDED": box.ROUNDED,
            "ROUND": box.ROUNDED,
            "SQUARE": box.SQUARE,
            "HEAVY": box.HEAVY,
            "THICK": box.HEAVY,
            "DOUBLE": box.DOUBLE,
            "ASCII": box.ASCII,
            "MINIMAL": box.MINIMAL,
            "MINIMAL_HEAVY": box.MINIMAL_HEAVY_HEAD,
            "MINIMAL_DOUBLE": box.MINIMAL_DOUBLE_HEAD,
            "SIMPLE": box.SIMPLE,
            "SIMPLE_HEAVY": box.SIMPLE_HEAVY,
            "SIMPLE_HEAD": box.SIMPLE_HEAD,
        }

        return mapping.get(key, box.ROUNDED)
