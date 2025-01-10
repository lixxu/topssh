#!/usr/bin/env python3
# -*- coding=utf-8 -*-

import time
from typing import Any

import paramiko

from .base import BaseSSH


class NeedAuthException(BaseException):
    pass


class SSH(BaseSSH):
    sftp = None
    transport = None

    def __init__(
        self,
        host: str = "",
        user: str | None = None,
        password: str | None = None,
        port: int = 22,
        **kwargs: Any,
    ) -> None:
        super().__init__(host, user, password, port, **kwargs)

    @property
    def is_connected(self) -> bool:
        return self.transport.active if self.transport else False

    def get_bufsize(self, **kwargs: Any) -> int:
        return kwargs.get("bufsize", self._kwargs.get("bufsize", 1024))

    def open_sftp(self) -> paramiko.sftp_client.SFTPClient:
        if not self.sftp:
            self.sftp = self.transport.open_sftp_client()

    def connect(self, host: str = "", **kwargs) -> None:
        port = kwargs.get("port")
        self.transport = paramiko.Transport((host or self.host, port or self.port))
        self.transport.set_keepalive(kwargs.get("keep_alive", 30))
        self.transport.connect(
            username=kwargs.get("user") or self.user,  # type: ignore
            password=kwargs.get("password") or self.password,
        )
        if not self.transport.is_authenticated():
            raise NeedAuthException("You need pass the authencation first")

        self.conn = self.transport.open_session(timeout=kwargs.get("timeout"))
        self.conn.get_pty(term=kwargs.get("term", "vt220"), width=kwargs.get("width", 800))
        self.conn.invoke_shell()
        self.conn.set_combine_stderr(True)
        time.sleep(0.1)

    def fetch_buffer(self, bufsize: int = 0) -> list:
        buffers = []
        time.sleep(0.1)
        bufsize = bufsize or self.get_bufsize()
        while self.conn.recv_ready():
            time.sleep(0.01)
            buffers.append(self.conn.recv(bufsize))

        return buffers

    def read_buffer(self, encoding: str = "utf-8", bufsize: int = 0) -> str:
        buffers = self.fetch_buffer(bufsize)
        buf = b"".join(buffers).decode(encoding, "ignore") if buffers else ""
        if text := self.strip_styles(buf):
            self.append_buffer(text, False)

        return text

    def clear_buffer(self, bufsize: int = 0) -> None:
        """ignore output"""
        self.fetch_buffer(bufsize)

    def patch_output(self, **kwargs: Any) -> None:
        self.add_timestamp_to_ps1(**kwargs)
        self.update_aliases()
        self.set_encoding()

    def set_encoding(self) -> None:
        return self.run("export LC_ALL=C.UTF-8")

    def show_system_info(self) -> None:
        cmds = ["who am i", "ip a", "uptime", "df -h", "uname -a", "cat /etc/*release"]
        self.run("; echo && ".join(cmds))

    def add_timestamp_to_ps1(self, **kwargs: Any) -> str:
        # self.run("echo add timestamps to prompt")
        cmd = r"""PS1="\[[\$(date +'%F %T.%6N')\]] \u@\h:\w"""
        if kwargs.get("new_line_prompt", False):
            cmd += r"\n"

        return self.run(cmd + '$ "')

    def update_aliases(self) -> str:
        return self.run("alias ls=ls {0}; alias grep=grep {0}".format("--color=never"))

    def open(self, *args: Any, **kwargs: Any) -> None:
        return self.connect(*args, **kwargs)

    def close(self) -> None:
        if self.conn:
            self.conn.close()

        if self.transport:
            self.transport.close()

    def safe_close(self) -> None:
        """close without exception"""
        try:
            self.close()
        except Exception:
            pass

    def send_ignore(self) -> None:
        self.transport.send_ignore()

    def set_keepalive(self, interval: int = 0) -> None:
        self.transport.set_keepalive(interval)

    def run(self, cmd: str, **kwargs: Any) -> str:
        self.send(cmd, **kwargs)

        outputs = []

        # capture expect for user input
        expect_captured = False
        expect = kwargs.get("expect") or ""
        expects = [expect] if expect and isinstance(expect, str) else expect

        last_seen = time.monotonic()  # last active time
        timeout = kwargs.get("timeout")

        bufsize = self.get_bufsize(**kwargs)
        encoding = kwargs.get("encoding", self._kwargs.get("encoding", "utf-8"))
        # for long response
        soft_timeout = kwargs.get("soft_timeout", self._kwargs.get("soft_timeout", True))
        while True:
            time.sleep(0.01)
            if self.conn.exit_status_ready():
                break

            if timeout and (time.monotonic() - last_seen) > timeout:
                break

            if output := self.read_buffer(encoding, bufsize):
                if soft_timeout:
                    # connection still alive as can still read buffer
                    last_seen = time.monotonic()

                outputs.append(output)
                if output.strip().endswith(("$", "#")):
                    break

                for exp in expects:
                    if exp in output:
                        expect_captured = True
                        break

                if expect_captured:
                    break

                if "sudo" in output and "password" in output:
                    self.send(self.password)  # type: ignore

        # read again in case that $/# in output
        if output := self.read_buffer(encoding, bufsize):
            outputs.append(output)

        return "".join(outputs)

    def send(self, cmd: str, end: str = "\n", **kwargs: Any) -> int:
        sent = self.conn.send(f"{cmd}{end}")  # type: ignore
        time.sleep(0.1)
        return sent

    def _download(self, remote: str, local: str | None = None, **kwargs: Any) -> None:
        self.open_sftp()
        self.sftp.get(remote, local, **kwargs)  # type: ignore

    def _upload(self, local: str, remote: str | None = None, **kwargs: Any) -> None:
        self.open_sftp()
        self.sftp.put(local, remote, **kwargs)  # type: ignore
