"""
验证码识别模块。

提供验证码识别相关功能，包括不同来源的验证码图片处理。
"""

import logging
import os
from io import BytesIO
from typing import Union, Optional, BinaryIO
import numpy as np
from PIL import Image
import ddddocr

logger = logging.getLogger(__name__)

# 初始化 ddddocr 实例（如果需要可以设置为可配置）
# 设置 beta=True 可能对某些验证码类型提高准确率
ocr = ddddocr.DdddOcr(beta=True)

def _get_image_bytes(image_data: Union[str, bytes, np.ndarray, BinaryIO]) -> bytes:
    """获取图像字节数据。
    
    将不同格式的图像数据转换为字节。
    
    Args:
        image_data: 图像数据，可以是文件路径、字节、OpenCV图像或文件对象
        
    Returns:
        图像字节数据
        
    Raises:
        ValueError: 不支持的图像类型
    """
    try:
        # 如果是文件路径
        if isinstance(image_data, str):
            if os.path.isfile(image_data):
                with open(image_data, 'rb') as f:
                    return f.read()
            else:
                raise ValueError(f"文件不存在: {image_data}")
        
        # 如果是字节
        elif isinstance(image_data, bytes):
            return image_data
        
        # 如果是NumPy数组（OpenCV图像）
        elif isinstance(image_data, np.ndarray):
            # 转换为PIL图像，然后转换为字节
            pil_img = Image.fromarray(image_data)
            img_byte_arr = BytesIO()
            # ddddocr 通常直接接受字节，可能不需要保存
            # 如果保存，确保格式兼容，PNG 通常是安全的
            pil_img.save(img_byte_arr, format='PNG') 
            return img_byte_arr.getvalue()
        
        # 如果是文件对象(如BytesIO)
        elif hasattr(image_data, 'read'):
            # 保存当前位置
            position = image_data.tell()
            try:
                # 读取全部内容
                data = image_data.read()
                # 如果已是字节，直接返回
                if isinstance(data, bytes):
                    return data
                # 否则尝试转换为字节
                else:
                    raise ValueError("无法从文件对象读取字节数据")
            finally:
                # 恢复原始位置
                try:
                    image_data.seek(position)
                except:
                    logger.warning("无法恢复文件对象的位置")
                    
        else:
            raise ValueError(f"不支持的图像类型: {type(image_data)}")
    except Exception as e:
        logger.error(f"处理图像数据失败: {e}")
        raise ValueError(f"处理图像数据失败: {e}")

def recognize_captcha(image_data: Union[str, bytes, np.ndarray, BinaryIO], **kwargs) -> str:
    """识别验证码。
    
    使用 ddddocr 识别图像中的验证码文本。
    
    Args:
        image_data: 验证码图像数据，可以是路径字符串、字节、OpenCV图像或文件对象
        **kwargs: 可选参数 (目前未使用，保留兼容性)
        
    Returns:
        识别出的验证码文本
        
    Raises:
        ValueError: 验证码识别失败
    """
    logger.info("开始使用 ddddocr 识别验证码")
    
    try:
        # 获取图像字节数据
        image_bytes = _get_image_bytes(image_data)
        
        # 使用 ddddocr 进行识别
        result = ocr.classification(image_bytes)
            
        # ddddocr 通常返回识别结果字符串
        if result and isinstance(result, str):
            # 可以选择性地清理或验证结果长度，但 ddddocr 通常比较准确
            expected_length = kwargs.get("expected_length") # 检查是否仍需要长度预期
            if expected_length and len(result) != expected_length:
                 logger.warning(f"ddddocr 识别结果 '{result}' 长度 ({len(result)}) 与预期 ({expected_length}) 不符")
                 # 决定是抛出错误还是直接返回结果
                 # 目前只记录警告并返回结果，也可以选择抛出 ValueError
            
            # 如果需要，只保留字母和数字
            # result = ''.join(c for c in result if c.isalnum())
            
            logger.info(f"ddddocr 验证码识别成功: {result}")
            return result
        else:
            logger.warning(f"ddddocr 未能识别验证码或返回无效结果: {result}")
            raise ValueError("ddddocr 未能识别验证码")
            
    except Exception as e:
        logger.error(f"ddddocr 验证码识别失败: {e}", exc_info=True)
        # 将异常包装为 ValueError 以保持与先前接口的一致性
        raise ValueError(f"ddddocr 验证码识别失败: {e}")