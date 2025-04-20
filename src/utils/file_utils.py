from __future__ import annotations
import os
from typing import List, Optional, Any
from src.utils.log.manager import get_logger

class FileUtils:
    """
    通用文件操作工具类，支持读写、删除、遍历等常用操作。
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """
        读取文本文件内容。
        Args:
            path: 文件路径
            encoding: 编码
        Returns:
            str: 文件内容
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取失败
        """
        self.logger.debug(f"读取文本文件: {path}")
        if not os.path.exists(path):
            self.logger.error(f"文件不存在: {path}")
            raise FileNotFoundError(f"文件不存在: {path}")
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        return content

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """
        写入文本内容到文件。
        Args:
            path: 文件路径
            content: 写入内容
            encoding: 编码
        Raises:
            IOError: 写入失败
        """
        self.logger.debug(f"写入文本到文件: {path}")
        with open(path, "w", encoding=encoding) as f:
            f.write(content)

    def read_lines(self, path: str, encoding: str = "utf-8") -> List[str]:
        """
        读取文本文件所有行。
        Args:
            path: 文件路径
            encoding: 编码
        Returns:
            List[str]: 文件行列表
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取失败
        """
        self.logger.debug(f"读取文件所有行: {path}")
        if not os.path.exists(path):
            self.logger.error(f"文件不存在: {path}")
            raise FileNotFoundError(f"文件不存在: {path}")
        with open(path, "r", encoding=encoding) as f:
            lines = f.readlines()
        return [line.rstrip('\n') for line in lines]

    def append_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """
        追加文本内容到文件。
        Args:
            path: 文件路径
            content: 追加内容
            encoding: 编码
        Raises:
            IOError: 写入失败
        """
        self.logger.debug(f"追加文本到文件: {path}")
        with open(path, "a", encoding=encoding) as f:
            f.write(content)

    def remove_file(self, path: str) -> None:
        """
        删除文件。
        Args:
            path: 文件路径
        Raises:
            FileNotFoundError: 文件不存在
            OSError: 删除失败
        """
        self.logger.debug(f"删除文件: {path}")
        if not os.path.exists(path):
            self.logger.warning(f"文件不存在: {path}")
            raise FileNotFoundError(f"文件不存在: {path}")
        os.remove(path)

    def list_files(self, directory: str, suffix: Optional[str] = None) -> List[str]:
        """
        列出目录下所有文件（可选后缀过滤）。
        Args:
            directory: 目录路径
            suffix: 文件后缀（如'.txt'）
        Returns:
            List[str]: 文件路径列表
        Raises:
            NotADirectoryError: 目录不存在
        """
        self.logger.debug(f"列出目录下所有文件: {directory}, 后缀: {suffix}")
        if not os.path.isdir(directory):
            self.logger.error(f"目录不存在: {directory}")
            raise NotADirectoryError(f"目录不存在: {directory}")
        files = []
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isfile(full_path) and (suffix is None or entry.endswith(suffix)):
                files.append(full_path)
        return files

    def file_exists(self, path: str) -> bool:
        """
        检查文件是否存在。
        Args:
            path: 文件路径
        Returns:
            bool: 是否存在
        """
        exists = os.path.exists(path)
        self.logger.debug(f"文件是否存在: {path} -> {exists}")
        return exists