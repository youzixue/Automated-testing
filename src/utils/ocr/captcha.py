"""
验证码识别模块。

专注于验证码图片的多格式输入处理与识别，基于 ddddocr，支持多种输入类型和异常链路清晰。
"""
from __future__ import annotations
from src.utils.log.manager import get_logger
import os
from io import BytesIO
from typing import Union, Optional, BinaryIO
import numpy as np
from PIL import Image
import ddddocr

logger = get_logger(__name__)

_ocr_instance = ddddocr.DdddOcr(beta=True)

def _get_image_bytes(image_data: Union[str, bytes, np.ndarray, BinaryIO]) -> bytes:
    """
    获取图像字节数据，支持文件路径、字节、OpenCV图像、文件对象等多种输入。
    Args:
        image_data: 图像数据
    Returns:
        bytes: 图像字节数据
    Raises:
        ValueError: 不支持的图像类型或处理失败
    """
    try:
        if isinstance(image_data, str):
            if os.path.isfile(image_data):
                with open(image_data, 'rb') as f:
                    return f.read()
            else:
                raise ValueError(f"文件不存在: {image_data}")
        elif isinstance(image_data, bytes):
            return image_data
        elif isinstance(image_data, np.ndarray):
            pil_img = Image.fromarray(image_data)
            img_byte_arr = BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        elif hasattr(image_data, 'read'):
            position = image_data.tell()
            try:
                data = image_data.read()
                if isinstance(data, bytes):
                    return data
                else:
                    raise ValueError("无法从文件对象读取字节数据")
            finally:
                try:
                    image_data.seek(position)
                except Exception:
                    logger.warning("无法恢复文件对象的位置")
        else:
            raise ValueError(f"不支持的图像类型: {type(image_data)}")
    except Exception as e:
        logger.error(f"处理图像数据失败: {e}")
        raise ValueError(f"处理图像数据失败: {e}")

def recognize_captcha(
    image_data: Union[str, bytes, np.ndarray, BinaryIO],
    expected_length: Optional[int] = None
) -> str:
    """
    识别验证码图片，支持多种输入类型，自动调用 ddddocr。
    Args:
        image_data: 验证码图像数据（路径、字节、OpenCV、文件对象等）
        expected_length: 可选，期望验证码长度
    Returns:
        str: 识别出的验证码文本
    Raises:
        ValueError: 识别失败
    """
    logger.info("开始使用 ddddocr 识别验证码")
    try:
        image_bytes = _get_image_bytes(image_data)
        result = _ocr_instance.classification(image_bytes)
        if result and isinstance(result, str):
            if expected_length and len(result) != expected_length:
                logger.warning(f"识别结果长度({len(result)})与期望({expected_length})不符: {result}")
            logger.info(f"验证码识别成功: {result}")
            return result
        else:
            logger.error(f"ddddocr 未能识别验证码或返回无效结果: {result}")
            raise ValueError("ddddocr 未能识别验证码")
    except Exception as e:
        logger.error(f"验证码识别失败: {e}", exc_info=True)
        raise ValueError(f"验证码识别失败: {e}")