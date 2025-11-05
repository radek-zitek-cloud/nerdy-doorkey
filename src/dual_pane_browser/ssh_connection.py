"""SSH connection management for remote file browsing."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Optional, List, Tuple
import stat as stat_module
import paramiko


class SSHConnection:
    """Manages an SSH connection and SFTP session."""

    def __init__(self, hostname: str, port: int = 22, username: Optional[str] = None):
        """Initialize SSH connection parameters.

        Args:
            hostname: Remote host address
            port: SSH port (default 22)
            username: SSH username (defaults to current user)
        """
        self.hostname = hostname
        self.port = port
        self.username = username or os.getenv("USER", "user")
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self._connected = False

    def connect(self, password: Optional[str] = None, key_filename: Optional[str] = None) -> None:
        """Establish SSH connection.

        Args:
            password: Password for authentication (optional)
            key_filename: Path to private key file (optional)

        Raises:
            Exception: If connection fails
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.hostname,
            "port": self.port,
            "username": self.username,
        }

        if password:
            connect_kwargs["password"] = password
        elif key_filename:
            connect_kwargs["key_filename"] = key_filename

        self.client.connect(**connect_kwargs)
        self.sftp = self.client.open_sftp()
        self._connected = True

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.client:
            self.client.close()
            self.client = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected and self.client is not None and self.sftp is not None

    def list_directory(self, path: str) -> List[Tuple[str, paramiko.SFTPAttributes]]:
        """List directory contents.

        Args:
            path: Remote directory path

        Returns:
            List of (name, attributes) tuples

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")

        entries = []
        for attr in self.sftp.listdir_attr(path):
            entries.append((attr.filename, attr))
        return entries

    def stat(self, path: str) -> paramiko.SFTPAttributes:
        """Get file/directory attributes.

        Args:
            path: Remote path

        Returns:
            File attributes

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        return self.sftp.stat(path)

    def is_dir(self, path: str) -> bool:
        """Check if path is a directory.

        Args:
            path: Remote path

        Returns:
            True if directory, False otherwise
        """
        try:
            attrs = self.stat(path)
            return stat_module.S_ISDIR(attrs.st_mode or 0)
        except:
            return False

    def exists(self, path: str) -> bool:
        """Check if path exists.

        Args:
            path: Remote path

        Returns:
            True if exists, False otherwise
        """
        try:
            self.stat(path)
            return True
        except:
            return False

    def get_file(self, remote_path: str, local_path: str) -> None:
        """Download file from remote to local.

        Args:
            remote_path: Remote file path
            local_path: Local destination path

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        self.sftp.get(remote_path, local_path)

    def put_file(self, local_path: str, remote_path: str) -> None:
        """Upload file from local to remote.

        Args:
            local_path: Local file path
            remote_path: Remote destination path

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        self.sftp.put(local_path, remote_path)

    def remove(self, path: str) -> None:
        """Remove a file.

        Args:
            path: Remote file path

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        self.sftp.remove(path)

    def rmdir(self, path: str) -> None:
        """Remove a directory.

        Args:
            path: Remote directory path

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        self.sftp.rmdir(path)

    def rename(self, old_path: str, new_path: str) -> None:
        """Rename a file or directory.

        Args:
            old_path: Current path
            new_path: New path

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        self.sftp.rename(old_path, new_path)

    def mkdir(self, path: str) -> None:
        """Create a directory.

        Args:
            path: Remote directory path

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        self.sftp.mkdir(path)

    def open(self, path: str, mode: str = "r") -> paramiko.SFTPFile:
        """Open a remote file.

        Args:
            path: Remote file path
            mode: File mode (r, w, a, etc.)

        Returns:
            SFTP file object

        Raises:
            IOError: If operation fails
        """
        if not self.is_connected or not self.sftp:
            raise IOError("Not connected to remote host")
        return self.sftp.open(path, mode)

    def __str__(self) -> str:
        """String representation of connection."""
        return f"{self.username}@{self.hostname}:{self.port}"

    def __repr__(self) -> str:
        """Developer representation of connection."""
        return f"SSHConnection({self.username}@{self.hostname}:{self.port}, connected={self.is_connected})"


__all__ = ["SSHConnection"]
