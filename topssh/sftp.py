#!/usr/bin/env python3
# -*- coding=utf-8 -*-

from typing import Any

import paramiko


class SFTP:
    def __init__(
        self, host: str = "", user: str = "", password: str = "", port: int = 22, **kwargs: Any
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.kw = kwargs.copy()

    def connect(self, **kwargs: Any) -> None:
        host = kwargs.get("host") or self.host
        port = kwargs.get("port") or self.port
        user = kwargs.get("user") or self.user
        password = kwargs.get("password") or self.password
        self.transport = paramiko.Transport((host, port))
        self.transport.connect(username=user, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def close(self) -> None:
        for obj in (self.sftp, self.transport):
            try:
                obj.close()
            except Exception:
                pass

    def __getattr__(self, name: str) -> Any:
        """
        Delegate all unknown attributes to the sftp object.
        """
        return getattr(self.sftp, name)

    def walkfiles(self, root_dir: str = "/") -> tuple:
        dirs, files = [], []
        for fd in self.listdir(root_dir):
            full_path = f"{root_dir}/{fd}"
            st = str(self.sftp.stat(full_path))
            if st.startswith("d"):  # a folder
                dirs.append(full_path)
                dirs_, files_ = self.walkfiles(dirs[-1])
                dirs.extend(dirs_)
                files.extend(files_)
            else:
                files.append(full_path)

        return dirs, files
