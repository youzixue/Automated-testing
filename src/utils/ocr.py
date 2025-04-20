from __future__ import annotations
import ddddocr
from PIL import Image, ImageFilter
import io
from src.utils.log.manager import get_logger

logger = get_logger(__name__)

def preprocess_captcha(img_bytes: bytes, threshold: int = 140, scale: int = 2) -> bytes:
    """
    对验证码图片进行灰度、二值化、去噪、放大等预处理，提高识别率。
    Args:
        img_bytes: 原始图片字节
        threshold: 二值化阈值
        scale: 放大倍数
    Returns:
        bytes: 预处理后的图片字节
    """
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = img.convert("L")
        img = img.point(lambda x: 0 if x < threshold else 255, '1')
        img = img.filter(ImageFilter.MedianFilter())
        img = img.resize((img.width * scale, img.height * scale))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"[OCR] 预处理失败: {e}")
        logger.debug("[OCR] 预处理失败，返回原图")
        return img_bytes

def recognize_captcha(img_bytes: bytes) -> str:
    """
    多重预处理+多次识别，提升验证码识别率。
    Args:
        img_bytes: 验证码图片字节
    Returns:
        str: 识别结果，失败返回空字符串
    """
    ocr = ddddocr.DdddOcr(show_ad=False)
    try:
        result1 = ocr.classification(img_bytes)
        pre_img_bytes = preprocess_captcha(img_bytes)
        result2 = ocr.classification(pre_img_bytes)
        if result1 and result1 == result2:
            logger.info(f"[OCR] 识别成功: {result1}")
            return result1
        result = result2 if result2 else result1
        if result:
            logger.info(f"[OCR] 识别成功: {result}")
        else:
            logger.error("[OCR] 识别失败，返回空字符串")
        return result or ""
    except Exception as e:
        logger.error(f"[OCR] 识别失败: {e}")
        return ""