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

    def open_sftp(self) -> paramiko.sftp_client.SFTPClient:
        if not self.sftp:
            self.sftp = self.transport.open_sftp_client()

    def connect(self, host: str = "", **kwargs) -> None:
        port = kwargs.get("port")
        self.transport = paramiko.Transport((host or self.host, port or self.port))
        self.transport.set_keepalive(kwargs.get("keep_alive", 30))
        self.transport.connect(
            username=kwargs.get("user") or self.user,
            password=kwargs.get("password") or self.password,
        )
        if not self.transport.is_authenticated():
            raise NeedAuthException("You need pass the authencation first")

        self.conn = self.transport.open_session(timeout=kwargs.get("timeout"))
        self.conn.get_pty(term=kwargs.get("term", "vt220"), width=kwargs.get("width", 800))
        self.conn.invoke_shell()
        self.conn.set_combine_stderr(True)
        time.sleep(0.1)

    def read_buffer(self, encoding: str = "utf-8") -> str:
        buffers = []
        time.sleep(0.1)
        while self.conn.recv_ready():
            buffers.append(self.conn.recv(1024))

        buf = b"".join(buffers).decode(encoding, "ignore") if buffers else ""
        return self.append_buffer(buf)

    def clear_buffer(self) -> None:
        """ignore output"""
        time.sleep(0.1)
        while self.conn.recv_ready():
            self.conn.recv(1024)

    def patch_output(self) -> None:
        self.add_timestamp_to_ps1()
        self.update_aliases()

    def add_timestamp_to_ps1(self) -> str:
        self.run("echo add timestamps to prompt")
        return self.run(r'''PS1="\[[\$(date +'%F %T.%6N')\]] \u@\h:\w$ "''')

    def update_aliases(self) -> str:
        return self.run("alias ls=ls {0}; alias grep=grep {0}".format("--color=never"))

    def open(self, *args: Any, **kwargs: Any) -> None:
        return self.connect(*args, **kwargs)

    def close(self) -> None:
        if self.conn:
            self.conn.close()

        if self.transport:
            self.transport.close()

    def run(self, cmd: str, **kwargs: Any) -> str:
        outputs = []
        self.send(cmd, **kwargs)
        timeout = kwargs.get("timeout")
        encoding = kwargs.get("encoding", "utf-8")
        start_ts = time.monotonic()
        while True:
            time.sleep(0.01)
            if self.conn.exit_status_ready():
                break

            if timeout and (time.monotonic() - start_ts) > timeout:
                break

            if output := self.read_buffer(encoding):
                outputs.append(output)
                if output.strip().endswith(("$", "#")):
                    break

                if "sudo" in output and "password" in output:
                    self.send(self.password)

        # read again in case that $/# in output
        if output := self.read_buffer(encoding):
            outputs.append(output)

        return "".join(outputs)

    def send(self, cmd: str, end: str = "\n", **kwargs: Any) -> int:
        sent = self.conn.send(f"{cmd}{end}")
        time.sleep(0.1)
        return sent

    def _download(self, remote: str, local: str | None = None, **kwargs: Any) -> None:
        self.open_sftp()
        self.sftp.get(remote, local)

    def _upload(self, local: str, remote: str | None = None, **kwargs: Any) -> None:
        self.open_sftp()
        self.sftp.put(local, remote)
