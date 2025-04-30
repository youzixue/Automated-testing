import pytest
import yaml
from pathlib import Path
from src.utils.log.manager import get_logger
from typing import List, Dict, Any # 导入 typing

from src.api.services.payment_service import PaymentService

logger = get_logger(__name__)

# --- 在模块加载时解析参数化数据 --- (最佳实践)
def _load_yaml_data(file_path: Path) -> Dict[str, Any]:
    """Helper to load YAML data, handling errors."""
    if not file_path.is_file():
        logger.error(f"YAML data file not found: {file_path}")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {file_path}: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading YAML file {file_path}: {e}", exc_info=True)
        return {}

_data_file_path = Path(__file__).parent.parent.parent / "data/api/payment_data.yaml"
_loaded_yaml_data = _load_yaml_data(_data_file_path)

# 提取参数化用例数据
INVALID_FORMAT_CASES_DATA: List[Dict] = _loaded_yaml_data.get('unified_order_invalid_format_type_cases', [])
LENGTH_CONSTRAINT_CASES_DATA: List[Dict] = _loaded_yaml_data.get('unified_order_length_constraint_cases', [])

# 生成参数化 IDs
INVALID_FORMAT_IDS: List[str] = [case.get('name', f"invalid_fmt_case_{i}") for i, case in enumerate(INVALID_FORMAT_CASES_DATA)]
LENGTH_CONSTRAINT_IDS: List[str] = [case.get('name', f"len_constr_case_{i}") for i, case in enumerate(LENGTH_CONSTRAINT_CASES_DATA)]

# --- Fixtures --- (保持现有 fixtures)

@pytest.fixture(scope="session")
def payment_api_data():
    """
    加载支付 API 测试数据 (payment_data.yaml).
    现在主要用于提供基础场景数据给测试函数体内部使用。
    参数化数据已在模块加载时单独提取。
    """
    if not _loaded_yaml_data: # 如果模块加载失败，fixture 也应该失败
        pytest.fail(f"无法从 {_data_file_path} 加载数据")
    logger.info(f"提供已加载的支付 API 测试数据 (来自 {_data_file_path})")
    return _loaded_yaml_data # 直接返回已在模块级别加载的数据

@pytest.fixture(scope="function")
def payment_service():
    """提供 PaymentService 实例并管理其生命周期。"""
    logger.debug("创建 PaymentService 实例")
    service = PaymentService()
    yield service
    logger.debug("清理 PaymentService 实例")
    service.close()