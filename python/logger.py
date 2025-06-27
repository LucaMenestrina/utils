#! /usr/bin/env python

__author__ = "Luca Menestrina"
__date__ = ""
__license__ = "MIT"
__maintainer__ = "Luca Menestrina"
__version__ = "20250627"
__deprecated__ = False

import logging
import warnings
import os
import sys
import inspect
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Literal
import threading
import json

DATE_TAG = datetime.now().strftime("%Y%m%d")
TIME_TAG = datetime.now().strftime("%H%M%S")
DATETIME_TAG = f"{DATE_TAG}{TIME_TAG}"

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    _COLORAMA_AVAILABLE = True
except ImportError:
    _COLORAMA_AVAILABLE = False

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

DEFAULT_LOG_FOLDER = "logs"

class logger():
    """
    A customizable logger class supporting console and file logging with runtime level changes,
    optional colorized console output, and structured JSON logging capability.
    """
    __instances = {}
    __lock = threading.Lock()

    def __init__(
        self,
        name: str,
        folder: str = DEFAULT_LOG_FOLDER,
        filemode: Literal["a", "w"] = "a",
        messagefmt: str = "%(asctime)s # %(levelname)s # %(message)s",
        datefmt: Optional[str] = "%Y-%m-%d %H:%M:%S",
        console_level: Optional[LogLevel] = "INFO",
        file_level: Optional[LogLevel] = "DEBUG",
        use_color: bool = False,
        json_log: bool = False,
        max_bytes: int = 5 * 1024 * 1024,
    ):
        """
        Initialize a named logger with handlers for console and rotating file output.

        Args:
            name: Name of the logger, also used as part of the logfile name.
            folder: Directory for log files.
            filemode: File mode for logging, either 'a' (append) or 'w' (overwrite).
            messagefmt: Log message format.
            datefmt: Date format for log timestamps.
            console_level: Logging level for console output.
            file_level: Logging level for file output.
            use_color: Whether to colorize console output (requires colorama).
            json_log: Enable structured JSON log format in file handler.
            max_bytes: Maximum size per rotating log file.
        """
        with logger.__lock:
            # If already initialized, compare configs
            if hasattr(self, "_initialized") and self._initialized:
                frame = inspect.currentframe()
                args_passed = {
                    k: v for k, v in frame.f_locals.items()
                    if k in self.__configs
                }

                mismatches = {
                    k: (args_passed[k], self.__configs[k])
                    for k in args_passed
                    if args_passed[k] != self.__configs[k]
                }

                if mismatches:
                    mismatch_str = ", ".join(
                        f"{k}: requested={v[0]!r}, existing={v[1]!r}"
                        for k, v in mismatches.items()
                    )
                    warnings.warn(
                        f"Logger '{self.name}:{self.folder}' already instantiated with different settings: "
                        f"{mismatch_str}. New values will be ignored.",
                        RuntimeWarning,
                    )
                return

            # Save config on first init
            self.__configs = self.__capture_config()

            self._initialized = True

            self.name = name
            self.folder = folder
            if not os.path.isdir(self.folder):
                os.makedirs(self.folder)
            self.filemode = filemode
            self.use_color = use_color and _COLORAMA_AVAILABLE
            self.json_log = json_log

            self._logger_name = f"{name}:{os.path.abspath(folder)}"
            self.logger = logging.getLogger(self._logger_name)
            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = False

            formatter = logging.Formatter(messagefmt, datefmt)

            if console_level:
                ch = logging.StreamHandler(sys.stdout)
                ch.setLevel(console_level.upper())
                ch.setFormatter(self._color_formatter(formatter) if self.use_color else formatter)
                self.logger.addHandler(ch)

            if file_level:
                self._log_filename = os.path.join(self.folder, f"{name}.log")
                fh = RotatingFileHandler(
                    self._log_filename,
                    mode=filemode,
                    maxBytes=max_bytes,
                    backupCount=9999,
                    encoding="utf-8"
                )
                fh.setLevel(file_level.upper())
                fh.setFormatter(self._json_formatter() if json_log else formatter)
                self.logger.addHandler(fh)

    def _get_context(self):
        stack = inspect.stack()
        for frame in stack:
            mod = inspect.getmodule(frame.frame)
            if mod and mod.__name__ != __name__:
                # External caller
                filename = os.path.basename(frame.filename)
                func = frame.function
                if func == "<module>":
                    func = "main"
                return f"{filename}:{func}"
            elif frame.function not in {"debug", "info", "warning", "error", "critical", "_format_message", "_get_context"}:
                # Fallback: skip internal logger functions
                filename = os.path.basename(frame.filename)
                func = frame.function
                if func == "<module>":
                    func = "main"
                return f"{filename}:{func}"
        return "unknown:unknown"

    def _format_message(self, msg: str) -> str:
        return f"[{self._get_context()}] {msg}"

    def _append_traceback(self, msg: str) -> str:
        tb = traceback.format_exc()
        # Only include if it"s a real exception (not just a call)
        if tb and "NoneType: None" not in tb and "SystemExit" not in tb and "raise SystemExit" not in tb:
            msg += "\n" + tb
        else:
            # Extract one level above the logger method
            stack = inspect.stack()
            for frame in stack[1:]:
                if frame.function not in ("debug", "info", "warning", "error", "critical", "_append_traceback"):
                    filename = os.path.basename(frame.filename)
                    function = frame.function if frame.function != "<module>" else "main"
                    lineno = frame.lineno
                    msg += f"\nTrace: {filename}:{function}:{lineno}"
                    break
        return msg

    def _color_formatter(self, base_formatter: logging.Formatter) -> logging.Formatter:
        class ColorizingFormatter(logging.Formatter):
            COLOR_MAP = {
                "DEBUG": Fore.CYAN,
                "INFO": Fore.GREEN,
                "WARNING": Fore.YELLOW,
                "ERROR": Fore.RED,
                "CRITICAL": Fore.MAGENTA
            }

            def format(self, record):
                levelname = record.levelname
                if levelname in self.COLOR_MAP:
                    record.levelname = self.COLOR_MAP[levelname] + levelname + Style.RESET_ALL
                return base_formatter.format(record)

        return ColorizingFormatter(base_formatter._fmt, base_formatter.datefmt)

    def _json_formatter(self) -> logging.Formatter:
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                payload = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "name": record.name,
                    "module": record.module,
                    "function": record.funcName,
                    "message": record.getMessage()
                }
                return json.dumps(payload, indent=4)

        return JsonFormatter()

    def debug(self, msg: str):
        self.logger.debug(self._format_message(msg))

    def info(self, msg: str):
        self.logger.info(self._format_message(msg))

    def warning(self, msg: str):
        msg = self._append_traceback(msg)
        self.logger.warning(self._format_message(msg))

    def error(self, msg: str):
        msg = self._append_traceback(msg)
        self.logger.error(self._format_message(msg))

    def critical(self, msg: str):
        msg = self._append_traceback(msg)
        self.logger.critical(self._format_message(msg))
        raise SystemExit(f"CRITICAL ERROR: {msg}")

    def setLevel(self, console: Optional[LogLevel] = None, file: Optional[LogLevel] = None):
        """
        Dynamically update the log level for console and/or file handlers.
        """
        for handler in self.logger.handlers:
            if console and isinstance(handler, logging.StreamHandler):
                handler.setLevel(console.upper())
            elif file and isinstance(handler, (logging.FileHandler, RotatingFileHandler)):
                handler.setLevel(file.upper())

    def disable(self):
        """
        Disable all logging output from this logger.
        """
        self.logger.disabled = True

    def enable(self):
        """
        Re-enable logging output from this logger.
        """
        self.logger.disabled = False

    def __new__(cls, name: str, folder: str = DEFAULT_LOG_FOLDER, *args, **kwargs):
        """
        Implements a per-configuration singleton pattern based on (name, folder).

        This method ensures that only one logger instance is created for each unique
        combination of logger name and output folder. If an instance with the same
        key already exists, it is returned; otherwise, a new one is created.

        Args:
            name (str): Logger name (used to retrieve the logger and name the logfile).
            folder (str): Folder where log files will be stored.
            *args: Additional positional arguments for the constructor.
            **kwargs: Additional keyword arguments for the constructor.

        Returns:
            logger: A singleton instance corresponding to the (name, folder) pair.
        """
        logger_name = f"{name}:{os.path.abspath(folder)}"

        with cls.__lock:
            if logger_name in cls.__instances:
                return cls.__instances[logger_name]
            instance = super().__new__(cls)
            cls.__instances[logger_name] = instance

        return instance
    
    def __capture_config(self):
        sig = inspect.signature(self.__init__)
        frame = inspect.currentframe()
        call_args = frame.f_back.f_locals  # the caller's local vars

        # Capture only actual init arguments (excluding 'self')
        configs = {
            param: call_args[param]
            for param in sig.parameters
            if param != "self" and param in call_args
        }
        return configs
    
    @property
    def configs(self):
        return self.__configs