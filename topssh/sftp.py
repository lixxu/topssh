#!/usr/bin/env python3
# -*- coding=utf-8 -*-

from pathlib import Path
from typing import Any

import paramiko


class SFTP:
    def __init__(
        self, host: str = "", user: str = "", password: str = "", port: int = 22, **kwargs: Any
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.password = password
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

    @classmethod
    def get_remote_path(cls, path: str) -> str:
        return f"/{path}".replace("//", "/").replace("//", "/")

    def walkfiles(self, root_dir: str = "/", max_depth: int = 0) -> tuple:
        def walking(top_dir: str) -> tuple:
            dirs, files = [], []
            for fd in self.listdir(top_dir):
                path = f"{top_dir}/{fd}"
                if str(self.sftp.stat(path)).startswith("d"):  # a folder
                    p = Path(path.removeprefix(root_dir).removeprefix("/"))
                    if not (max_depth and len(p.parts) > max_depth):
                        dirs_, files_ = walking(path)
                        dirs.extend([path] + dirs_)
                        files.extend(files_)

                else:
                    files.append(path)

            return dirs, files

        return walking(root_dir)

    def upload_files(self, local_files: list, remote_dir: str = "/", filename_maps: dict = {}) -> None:
        for local_file in local_files:
            filename = Path(local_file).name
            remote_file = f"{remote_dir}/{filename_maps.get(filename, filename)}"
            self.put(local_file, self.get_remote_path(remote_file))

    def get_size(self, remote_file: str) -> int:
        return self.stat(remote_file).st_size
