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
        self.silent = kwargs.get("silent", False)
        self.verbose = kwargs.get("verbose", False)
        self.kw = kwargs.copy()

    def connect(self, **kwargs: Any) -> Any:
        host = kwargs.get("host") or self.host
        port = kwargs.get("port") or self.port
        user = kwargs.get("user") or self.user
        password = kwargs.get("password") or self.password
        self.transport = paramiko.Transport((host, port))
        self.transport.connect(username=user, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        return self

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
        """returns: (dirs, files)"""

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

    def upload(self, local: Any, remote: Any, **kwargs: Any) -> tuple:
        fp = Path(local)
        filename = kwargs.pop("filename", "")
        remote_path = self.get_remote_path(f"{remote}/{filename or fp.name}")
        if fp.exists():
            try:
                self.sftp.put(str(fp), remote_path)
                return True, True
            except Exception as ex:
                return False, str(ex)

        return False, "local file not exists"

    def upload_from_string(self, text: Any, remote: Any, **kwargs: Any) -> tuple:
        filename = kwargs.pop("filename", "")
        if filename:
            remote = f"{remote}/{filename}"

        try:
            with self.sftp.open(self.get_remote_path(remote), "w") as fo:
                fo.write(f"{text}")

            return True, None
        except Exception as ex:
            return False, str(ex)

    def upload_files(self, local_files: list, remote_dir: str = "/", filename_maps: dict = {}) -> None:
        for local_file in local_files:
            filename = Path(local_file).name
            remote_file = f"{remote_dir}/{filename_maps.get(filename, filename)}"
            self.sftp.put(local_file, self.get_remote_path(remote_file))

    def download(self, remote: Any, local: Any) -> tuple:
        try:
            self.sftp.get(str(remote), str(local))
            return True, None
        except Exception as ex:
            return False, str(ex)

    def download_to_list(self, remote: str) -> list:
        try:
            with self.sftp.open(remote) as fo:
                return fo.read().decode("utf-8", "ignore").splitlines()

        except Exception as ex:
            print(ex)
            return []

    def get_size(self, remote: str) -> int:
        try:
            return self.sftp.stat(remote).st_size
        except Exception:
            return -1

    def get_name(self, remote: str) -> str:
        return Path(remote).name

    def delete(self, remote: str) -> tuple:
        try:
            self.sftp.remove(remote)
            return True, None
        except Exception as ex:
            return False, str(ex)
