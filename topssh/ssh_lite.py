#!/usr/bin/env python3
# -*- coding=utf-8 -*-

from typing import Any

from fabric import Connection
from invoke import Responder
from invoke.runners import Result

from .base import BaseSSH


class SSH(BaseSSH):
    watchers = []

    def __init__(
        self,
        host: str = "",
        user: Any = None,
        password: Any = None,
        port: int = 22,
        **kwargs: Any,
    ) -> None:
        super().__init__(host, user, password, port, **kwargs)

    @property
    def is_connected(self) -> bool:
        return self.conn.is_connected

    def get_watcher(self, pattern: str, response: str) -> Responder:
        return Responder(pattern, response)

    def add_watcher(self, pattern: str, response: str) -> None:
        self.watchers.append(self.get_watcher(pattern, response))

    def add_sudo_watcher(self, pattern: str = r"\[sudo\] password", password: str = "") -> None:
        self.add_watcher(pattern, f"{password or self.password}\n")

    def connect(self, host: str = "", **kwargs) -> None:
        conn_kw = dict(password=kwargs.pop("password", None) or self.password, banner_timeout=60)
        if timeout := kwargs.pop("timeout", None):
            conn_kw.update(timeout=timeout)

        kw = dict(user=kwargs.pop("user", None) or self.user) | kwargs
        kw.setdefault("port", self.port)
        self.conn = Connection(host or self.host, connect_kwargs=conn_kw, **kw)
        self.open()

    def open(self) -> Any:
        return self.conn.open()

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    def run(self, cmd: str, watchers: Any = None, **kwargs: Any) -> str:
        if watchers is None:
            watchers = self.watchers

        kwargs.setdefault("hide", True)
        kwargs.setdefault("warn", True)
        kwargs.setdefault("echo", False)
        res = self.conn.run(cmd, pty=True, watchers=watchers, **kwargs)
        return self.append_buffer(res.stdout)

    def poweroff(self, **kwargs: Any) -> Any:
        return super().poweroff(warn=True, **kwargs)

    def _download(
        self,
        remote: str,
        local: Any = None,
        preserve_mode: bool = True,
        **kwargs: Any,
    ) -> None:
        self.conn.get(remote, local, preserve_mode)

    def _upload(
        self,
        local: str,
        remote: Any = None,
        preserve_mode: bool = True,
        **kwargs: Any,
    ) -> None:
        self.conn.put(local, remote, preserve_mode)

    def ping(self, host: str, args: str = "") -> Result:
        return super().ping(host, args)
