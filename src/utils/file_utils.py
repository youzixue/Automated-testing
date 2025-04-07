"""
文件操作辅助工具。

提供安全的文件读写、临时文件处理、路径处理等功能。
"""

import os
import shutil
import tempfile
import json
import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, TextIO, Callable, overload

import yaml

# 获取日志记录器
logger = logging.getLogger(__name__)


class FileUtils:
    """文件操作工具类。
    
    提供安全的文件操作方法，包括读写、复制、删除等功能。
    """
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """确保目录存在，如不存在则创建。
        
        Args:
            directory: 目录路径
            
        Returns:
            目录路径对象
            
        Raises:
            OSError: 创建目录失败
        """
        path = Path(directory)
        if not path.exists():
            logger.info(f"目录不存在，创建目录: {path}")
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"创建目录失败: {path}, 错误: {e}")
                raise
        return path
    
    @staticmethod
    def read_text(filepath: Union[str, Path], encoding: str = 'utf-8') -> str:
        """安全读取文本文件。
        
        Args:
            filepath: 文件路径
            encoding: 文件编码
            
        Returns:
            文件内容字符串
            
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取文件失败
        """
        logger.debug(f"读取文本文件: {filepath}")
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"文件未找到: {filepath}")
            raise
        except IOError as e:
            logger.error(f"读取文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def write_text(filepath: Union[str, Path], content: str, encoding: str = 'utf-8', 
                  create_dirs: bool = True) -> None:
        """安全写入文本文件。
        
        Args:
            filepath: 文件路径
            content: 文件内容
            encoding: 文件编码
            create_dirs: 是否自动创建父目录
            
        Raises:
            IOError: 写入文件失败
        """
        logger.debug(f"写入文本文件: {filepath}")
        path = Path(filepath)
        if create_dirs:
            FileUtils.ensure_directory(path.parent)
            
        try:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
        except IOError as e:
            logger.error(f"写入文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def read_binary(filepath: Union[str, Path]) -> bytes:
        """安全读取二进制文件。
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件二进制内容
            
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取文件失败
        """
        logger.debug(f"读取二进制文件: {filepath}")
        try:
            with open(filepath, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"文件未找到: {filepath}")
            raise
        except IOError as e:
            logger.error(f"读取文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def write_binary(filepath: Union[str, Path], content: bytes, 
                    create_dirs: bool = True) -> None:
        """安全写入二进制文件。
        
        Args:
            filepath: 文件路径
            content: 文件二进制内容
            create_dirs: 是否自动创建父目录
            
        Raises:
            IOError: 写入文件失败
        """
        logger.debug(f"写入二进制文件: {filepath}")
        path = Path(filepath)
        if create_dirs:
            FileUtils.ensure_directory(path.parent)
            
        try:
            with open(path, 'wb') as f:
                f.write(content)
        except IOError as e:
            logger.error(f"写入文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def read_json(filepath: Union[str, Path], encoding: str = 'utf-8') -> Any:
        """读取JSON文件。
        
        Args:
            filepath: 文件路径
            encoding: 文件编码
            
        Returns:
            解析后的JSON数据
            
        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON解析错误
            IOError: 读取文件失败
        """
        logger.debug(f"读取JSON文件: {filepath}")
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"文件未找到: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {filepath}, 错误: {e}")
            raise
        except IOError as e:
            logger.error(f"读取JSON文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def write_json(filepath: Union[str, Path], data: Any, encoding: str = 'utf-8', 
                  indent: int = 2, ensure_ascii: bool = False,
                  create_dirs: bool = True) -> None:
        """写入JSON文件。
        
        Args:
            filepath: 文件路径
            data: 要保存的数据
            encoding: 文件编码
            indent: 缩进空格数
            ensure_ascii: 是否确保ASCII编码
            create_dirs: 是否自动创建父目录
            
        Raises:
            TypeError: 数据无法序列化为JSON
            IOError: 写入文件失败
        """
        logger.debug(f"写入JSON文件: {filepath}")
        path = Path(filepath)
        if create_dirs:
            FileUtils.ensure_directory(path.parent)
            
        try:
            with open(path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        except TypeError as e:
            logger.error(f"数据无法序列化为JSON: {filepath}, 错误: {e}")
            raise
        except IOError as e:
            logger.error(f"写入JSON文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def read_yaml(filepath: Union[str, Path], encoding: str = 'utf-8') -> Any:
        """读取YAML文件。
        
        Args:
            filepath: 文件路径
            encoding: 文件编码
            
        Returns:
            解析后的YAML数据
            
        Raises:
            ImportError: 未安装PyYAML
            FileNotFoundError: 文件不存在
            yaml.YAMLError: YAML解析错误
            IOError: 读取文件失败
        """
        logger.debug(f"读取YAML文件: {filepath}")
        try:
            import yaml # Check import here
        except ImportError:
            logger.error("未安装PyYAML，无法读取YAML文件。请运行: pip install pyyaml")
            raise ImportError("未安装PyYAML，请运行: pip install pyyaml")

        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"文件未找到: {filepath}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误: {filepath}, 错误: {e}")
            raise
        except IOError as e:
            logger.error(f"读取YAML文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def write_yaml(filepath: Union[str, Path], data: Any, encoding: str = 'utf-8',
                  create_dirs: bool = True) -> None:
        """写入YAML文件。
        
        Args:
            filepath: 文件路径
            data: 要保存的数据
            encoding: 文件编码
            create_dirs: 是否自动创建父目录
            
        Raises:
            ImportError: 未安装PyYAML
            TypeError: 数据无法序列化为YAML
            IOError: 写入文件失败
        """
        logger.debug(f"写入YAML文件: {filepath}")
        try:
            import yaml # Check import here
        except ImportError:
            logger.error("未安装PyYAML，无法写入YAML文件。请运行: pip install pyyaml")
            raise ImportError("未安装PyYAML，请运行: pip install pyyaml")

        path = Path(filepath)
        if create_dirs:
            FileUtils.ensure_directory(path.parent)
            
        try:
            with open(path, 'w', encoding=encoding) as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        except yaml.YAMLError as e:
            logger.error(f"数据无法序列化为YAML: {filepath}, 错误: {e}")
            raise TypeError(f"数据无法序列化为YAML: {e}") from e
        except IOError as e:
            logger.error(f"写入YAML文件失败: {filepath}, 错误: {e}")
            raise
    
    @overload
    @staticmethod
    def read_csv(filepath: Union[str, Path], encoding: str = 'utf-8', 
                delimiter: str = ',', with_header: bool = True) -> List[Dict[str, str]]:
        ...

    @overload
    @staticmethod
    def read_csv(filepath: Union[str, Path], encoding: str = 'utf-8', 
                delimiter: str = ',', with_header: bool = False) -> List[List[str]]:
        ...

    @staticmethod
    def read_csv(filepath: Union[str, Path], encoding: str = 'utf-8', 
                delimiter: str = ',', with_header: bool = True) -> Union[List[Dict[str, str]], List[List[str]]]:
        """读取CSV文件。
        
        Args:
            filepath: 文件路径
            encoding: 文件编码
            delimiter: 列分隔符
            with_header: 是否包含标题行
            
        Returns:
            如果 with_header 为 True，返回包含字典的列表。
            如果 with_header 为 False，返回包含列表的列表。
            
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取文件失败
        """
        logger.debug(f"读取CSV文件: {filepath}, 带标题: {with_header}")
        result = []
        try:
            with open(filepath, 'r', encoding=encoding, newline='') as f:
                if with_header:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    for row in reader:
                        result.append(dict(row))
                else:
                    reader = csv.reader(f, delimiter=delimiter)
                    for row in reader:
                        result.append(row)
        except FileNotFoundError:
            logger.error(f"文件未找到: {filepath}")
            raise
        except IOError as e:
            logger.error(f"读取CSV文件失败: {filepath}, 错误: {e}")
            raise
        return result
    
    @staticmethod
    def write_csv(filepath: Union[str, Path], data: List[Dict[str, Any]], 
                 fieldnames: Optional[List[str]] = None, encoding: str = 'utf-8',
                 delimiter: str = ',', create_dirs: bool = True) -> None:
        """写入CSV文件。
        
        Args:
            filepath: 文件路径
            data: 要保存的数据
            fieldnames: 列名列表，None时使用第一行的键
            encoding: 文件编码
            delimiter: 列分隔符
            create_dirs: 是否自动创建父目录
            
        Raises:
            IOError: 写入文件失败
        """
        if not data:
            logger.warning(f"写入CSV文件 {filepath} 的数据为空，跳过写入")
            return
            
        logger.debug(f"写入CSV文件: {filepath}")
        path = Path(filepath)
        if create_dirs:
            FileUtils.ensure_directory(path.parent)
            
        # 自动获取列名
        if fieldnames is None:
            fieldnames = list(data[0].keys())
            
        try:
            with open(path, 'w', encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
        except IOError as e:
            logger.error(f"写入CSV文件失败: {filepath}, 错误: {e}")
            raise
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path], 
                 create_dirs: bool = True) -> None:
        """复制文件。
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            create_dirs: 是否自动创建目标父目录
            
        Raises:
            FileNotFoundError: 源文件不存在
            IOError: 复制文件失败
        """
        logger.info(f"复制文件: {src} -> {dst}")
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            logger.error(f"源文件不存在: {src}")
            raise FileNotFoundError(f"源文件不存在: {src}")
            
        if create_dirs:
            FileUtils.ensure_directory(dst_path.parent)
            
        try:
            shutil.copy2(src_path, dst_path)
        except IOError as e:
            logger.error(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            raise
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path], 
                 create_dirs: bool = True) -> None:
        """移动文件。
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            create_dirs: 是否自动创建目标父目录
            
        Raises:
            FileNotFoundError: 源文件不存在
            IOError: 移动文件失败
        """
        logger.info(f"移动文件: {src} -> {dst}")
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            logger.error(f"源文件不存在: {src}")
            raise FileNotFoundError(f"源文件不存在: {src}")
            
        if create_dirs:
            FileUtils.ensure_directory(dst_path.parent)
            
        try:
            shutil.move(str(src_path), str(dst_path))
        except IOError as e:
            logger.error(f"移动文件失败: {src} -> {dst}, 错误: {e}")
            raise
    
    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
        """安全删除文件或目录。
        
        如果路径不存在，则不执行任何操作并返回True。
        
        Args:
            path: 文件或目录路径
            
        Returns:
            是否成功删除
            
        Raises:
            IOError: 删除失败
        """
        path_obj = Path(path)
        if not path_obj.exists():
            logger.warning(f"尝试删除不存在的路径: {path_obj}")
            return True
            
        try:
            if path_obj.is_dir():
                logger.info(f"删除目录: {path_obj}")
                shutil.rmtree(path_obj)
            else:
                logger.info(f"删除文件: {path_obj}")
                path_obj.unlink()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_temp_dir() -> Path:
        """获取临时目录路径。
        
        Returns:
            临时目录路径对象
        """
        return Path(tempfile.gettempdir())
    
    @staticmethod
    def create_temp_dir(prefix: str = "tmp") -> Path:
        """创建临时目录。
        
        Args:
            prefix: 目录名前缀
            
        Returns:
            临时目录路径对象
            
        Raises:
            IOError: 创建临时目录失败
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        logger.info(f"创建临时目录: {temp_dir}")
        return temp_dir
    
    @staticmethod
    def create_temp_file(prefix: str = "tmp", suffix: str = ".tmp") -> Path:
        """创建临时文件。
        
        Args:
            prefix: 文件名前缀
            suffix: 文件名后缀
            
        Returns:
            临时文件路径对象
            
        Raises:
            IOError: 创建临时文件失败
        """
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(fd)
        temp_path = Path(path)
        logger.info(f"创建临时文件: {temp_path}")
        return temp_path
    
    @staticmethod
    def list_files(directory: Union[str, Path], 
                  pattern: str = "*", 
                  recursive: bool = False) -> List[Path]:
        """列出目录中的文件。
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归查找子目录
            
        Returns:
            文件路径对象列表
            
        Raises:
            FileNotFoundError: 目录不存在
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.error(f"目录不存在: {directory_path}")
            raise FileNotFoundError(f"目录不存在: {directory_path}")
            
        if recursive:
            return list(directory_path.glob(f"**/{pattern}"))
        else:
            return list(directory_path.glob(pattern))
    
    @staticmethod
    def with_temp_file(callback: Callable[[Path], Any], 
                      prefix: str = "tmp", 
                      suffix: str = ".tmp") -> Any:
        """使用临时文件执行操作。
        
        创建临时文件，执行回调，然后自动删除临时文件。
        
        Args:
            callback: 回调函数，接收临时文件路径作为参数
            prefix: 文件名前缀
            suffix: 文件名后缀
            
        Returns:
            回调函数的返回值
            
        Raises:
            IOError: 创建临时文件失败
        """
        temp_path = None
        try:
            temp_path = FileUtils.create_temp_file(prefix, suffix)
            logger.debug(f"执行回调函数，使用临时文件: {temp_path}")
            return callback(temp_path)
        finally:
            if temp_path and temp_path.exists():
                FileUtils.safe_delete(temp_path)
    
    @staticmethod
    def with_temp_dir(callback: Callable[[Path], Any], 
                     prefix: str = "tmp") -> Any:
        """使用临时目录执行操作。
        
        创建临时目录，执行回调，然后自动删除临时目录。
        
        Args:
            callback: 回调函数，接收临时目录路径作为参数
            prefix: 目录名前缀
            
        Returns:
            回调函数的返回值
            
        Raises:
            IOError: 创建临时目录失败
        """
        temp_dir = None
        try:
            temp_dir = FileUtils.create_temp_dir(prefix)
            logger.debug(f"执行回调函数，使用临时目录: {temp_dir}")
            return callback(temp_dir)
        finally:
            if temp_dir and temp_dir.exists():
                FileUtils.safe_delete(temp_dir)
    
    @staticmethod
    def get_file_size(filepath: Union[str, Path]) -> int:
        """获取文件大小。
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件大小(字节)
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(filepath)
        logger.debug(f"获取文件大小: {path}")
        try:
            return path.stat().st_size
        except FileNotFoundError:
            logger.error(f"文件未找到: {path}")
            raise
        except OSError as e:
            logger.error(f"获取文件大小失败: {path}, 错误: {e}")
            raise
    
    @staticmethod
    def get_file_extension(filepath: Union[str, Path]) -> str:
        """获取文件扩展名。
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件扩展名(不包含点)
        """
        path = Path(filepath)
        ext = path.suffix.lstrip('.')
        logger.debug(f"获取文件扩展名: {path} -> {ext}")
        return ext
    
    @staticmethod
    def change_extension(filepath: Union[str, Path], new_ext: str) -> Path:
        """更改文件扩展名。
        
        Args:
            filepath: 文件路径
            new_ext: 新扩展名(不需要包含点)
            
        Returns:
            新文件路径对象
        """
        path = Path(filepath)
        if not new_ext.startswith('.'):
            new_ext = '.' + new_ext
        new_path = path.with_suffix(new_ext)
        logger.debug(f"更改文件扩展名: {path} -> {new_path}")
        return new_path
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """标准化路径表示，返回绝对路径对象。
        
        Args:
            path: 文件或目录路径
            
        Returns:
            标准化的Path对象
        """
        normalized = Path(path).resolve()
        logger.debug(f"标准化路径: {path} -> {normalized}")
        return normalized