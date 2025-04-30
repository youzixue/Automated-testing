import hashlib
from src.utils.log.manager import get_logger
from typing import Dict, Any

# 获取日志记录器
logger = get_logger(__name__)

def calculate_md5_sign(params_to_sign: Dict[str, Any], secret_key: str, charset: str = "UTF-8") -> str:
    """
    根据微信支付兼容规则计算 MD5 签名。

    Args:
        params_to_sign: 需要参与签名的参数字典。
        secret_key: 签名密钥。
        charset: 编码字符集，默认为 UTF-8。

    Returns:
        大写的 MD5 签名字符串。

    Raises:
        ValueError: 如果参数或密钥无效。
        Exception: 其他计算错误。
    """
    if not isinstance(params_to_sign, dict):
        raise ValueError("params_to_sign 必须是字典类型")
    if not secret_key:
        raise ValueError("secret_key 不能为空")

    logger.debug(f"开始计算MD5签名，原始参数: {params_to_sign}")

    # 第一步：过滤掉 sign 参数和值为空或 None 的参数
    filtered_params = {
        k: v for k, v in params_to_sign.items()
        if v is not None and v != '' and k not in ['sign', 'key', 'appKey'] # 兼容原始脚本中的过滤逻辑
    }
    logger.debug(f"过滤后的签名参数: {filtered_params}")

    # 第二步：按参数名 ASCII 码从小到大排序（字典序）
    try:
        sorted_items = sorted(filtered_params.items())
    except TypeError as e:
        logger.error(f"参数排序失败，可能包含不可比较的类型: {e}", exc_info=True)
        raise ValueError(f"参数排序失败: {e}") from e

    # 第三步：使用 URL 键值对的格式（key1=value1&key2=value2…）拼接成字符串 stringA
    stringA = '&'.join([f"{k}={v}" for k, v in sorted_items])
    logger.debug(f"拼接的 StringA: {stringA}")

    # 第四步：在 stringA 最后拼接上 key 得到 stringSignTemp 字符串
    stringSignTemp = f"{stringA}&key={secret_key}"
    logger.debug(f"待签名的 StringSignTemp: {stringSignTemp}")

    # 第五步：对 stringSignTemp 进行 MD5 运算，并转换为大写
    try:
        encoded_string = stringSignTemp.encode(charset)
        md5_hash = hashlib.md5(encoded_string).hexdigest().upper()
        logger.info(f"计算得到的 MD5 签名: {md5_hash}")
        return md5_hash
    except UnicodeEncodeError as e:
        logger.error(f"使用字符集 '{charset}' 对字符串进行编码时出错: {e}", exc_info=True)
        raise ValueError(f"无效的字符集 '{charset}' 或字符串包含无法编码的字符") from e
    except Exception as e:
        logger.error(f"计算 MD5 时发生未知错误: {e}", exc_info=True)
        raise RuntimeError(f"计算 MD5 签名时出错: {e}") from e 