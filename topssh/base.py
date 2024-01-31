#!/usr/bin/env python3
# -*- coding=utf-8 -*-

from pathlib import Path
from typing import Any

import term


class BaseSSH:
    conn = None

    def __init__(
        self,
        host: str = "",
        user: str | None = None,
        password: str | None = None,
        port: int = 22,
        **kwargs: Any,
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self._kwargs = kwargs
        self.echo_text = []  # keep all command output

    @property
    def is_connected(self) -> bool:
        return NotImplemented

    @classmethod
    def strip_styles(cls, text: str) -> str:
        return term.strip(text)

    def append_buffer(self, text: str) -> str:
        self.echo_text.append(self.strip_styles(text))
        return self.echo_text[-1]

    def connect(self, *args: Any, **kwargs: Any) -> None:
        return NotImplemented

    def add_sudo_watcher(self, *args: Any, **kwargs: Any) -> None:
        pass

    def open(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def close(self, *args: Any, **kwargs: Any) -> None:
        pass

    def run(self, cmd: str, **kwargs: Any) -> Any:
        return NotImplemented

    def reboot(self, **kwargs: Any) -> Any:
        return self.run("sudo reboot", **kwargs)

    def poweroff(self, **kwargs: Any) -> Any:
        return self.run("sudo poweroff", **kwargs)

    def shutdown(self, **kwargs: Any) -> Any:
        return self.poweroff(**kwargs)

    def _download(self, *args: Any, **kwargs: Any) -> None:
        pass

    def _upload(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get(self, remote: str, local: str | None = None, **kwargs: Any) -> None:
        if local and Path(local).is_dir():
            local = f"{local}/{remote.rsplit('/')[-1]}"

        self._download(remote, local, **kwargs)

    def put(
        self,
        local: str,
        remote: str | None = None,
        target_is_dir: bool = True,
        **kwargs: Any,
    ) -> None:
        if target_is_dir:
            remote = f"{remote}/{Path(local).name}"

        self._upload(local, remote, **kwargs)

    def ping(self, host: str, args: str = "") -> Any:
        return self.run(f"ping {args} {host}")
