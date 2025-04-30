import json
import pytest
import copy
from typing import Any, Optional, List, Dict
import allure  # 导入 allure

from pydantic import ValidationError # 导入 ValidationError

from src.api.services.payment_service import PaymentService
from src.api.models.payment_models import CreateOrderResponse, OneDataModel, GoodsDetailItem
from src.core.base.errors import ApiRequestError
from src.utils.log.manager import get_logger

# 从 conftest 导入预加载的参数化数据和 IDs
from .conftest import (
    INVALID_FORMAT_CASES_DATA,
    LENGTH_CONSTRAINT_CASES_DATA,
    INVALID_FORMAT_IDS,
    LENGTH_CONSTRAINT_IDS
)

logger = get_logger(__name__)

# --- 断言常量定义 ---
SUCCESS_CODE = "SUCCESS"
FAILED_CODE = "FAILED"

# 预期的错误信息片段 (根据日志和 API 行为调整)
ERR_MSG_SIGNATURE = "签名错误"
ERR_MSG_DUPLICATE_ORDER = "此交易订单号重复"
ERR_MSG_INVALID_IP = "IP错误"
ERR_MSG_INVALID_URL = "URL格式错误"
ERR_MSG_INVALID_AMOUNT = "金额格式错误"
ERR_MSG_INVALID_TIME_FORMAT = "时间格式错误"
ERR_MSG_GOODS_DETAIL = "商品描述42位以内"
ERR_MSG_LENGTH_LIMIT = "单号格式错误"
ERR_MSG_INVALID_INPUT = "输入参数无效" # 用于服务层校验失败

# --- 辅助函数：将 YAML 数据转换为 Pydantic 模型 ---
def parse_one_data(one_data_dict: Dict[str, Any]) -> OneDataModel:
    """尝试将字典解析为 OneDataModel"""
    try:
        return OneDataModel.model_validate(one_data_dict)
    except ValidationError as e:
        logger.error(f"测试数据中的 one_data 格式无法解析为 OneDataModel: {e}")
        raise ValueError(f"无法解析测试数据中的 one_data: {e}") from e

# --- 成功场景测试 ---
@pytest.mark.api
@pytest.mark.smoke
@allure.title("统一支付下单 - 成功场景")
def test_unified_order_success(
    payment_service: PaymentService,
    payment_api_data: dict
):
    """
    测试成功场景：调用获取签名接口，然后使用签名成功创建统一支付订单。
    现在断言基于 Pydantic 模型。
    """
    test_scenario = payment_api_data.get('unified_order_success')
    if not test_scenario:
        pytest.fail("未找到 'unified_order_success' 场景数据")

    get_sign_params = test_scenario.get('get_sign_order_params')
    create_order_params = test_scenario.get('create_order_params')
    # expected_status 不再是主要断言依据

    if not all([get_sign_params, create_order_params]):
        pytest.fail("'unified_order_success' 场景数据不完整")

    logger.info("--- 测试场景: 统一支付下单成功 ---")

    # 在测试开始前处理 one_data 转换，确保服务层接收正确类型
    try:
         if 'one_data' in get_sign_params:
              get_sign_params['one_data'] = parse_one_data(get_sign_params['one_data'])
         if 'one_data' in create_order_params:
              create_order_params['one_data'] = parse_one_data(create_order_params['one_data'])
    except ValueError as e:
         pytest.fail(f"测试数据准备失败: {e}")

    # 步骤 1: 获取支付签名 (get_payment_sign 保持不变，返回 str)
    try:
        logger.info("步骤 1: 调用 get_payment_sign 获取签名")
        payment_sign = payment_service.get_payment_sign(get_sign_params)
        assert payment_sign, "获取到的支付签名不能为空"
        logger.info(f"成功获取支付签名: {payment_sign[:10]}...")
    except (ApiRequestError, ValueError) as e:
        logger.error(f"步骤 1 失败: 获取支付签名时出错 - {e}", exc_info=True)
        pytest.fail(f"获取支付签名失败: {e}")
        return

    # 步骤 2: 创建统一支付订单 (create_unified_order 返回 CreateOrderResponse)
    try:
        logger.info("步骤 2: 调用 create_unified_order 进行下单")

        unique_out_trade_no = payment_service.data_generator.generate_out_trade_no("SUCCESSTEST_")
        # 注意：create_order_params 是 base_params 的别名，直接修改会影响 base_params
        # 为了隔离，应该 deepcopy
        current_create_params = copy.deepcopy(create_order_params)
        current_create_params['out_trade_no'] = unique_out_trade_no
        logger.info(f"强制使用唯一订单号: {unique_out_trade_no}")

        # --- 调用返回 Pydantic 模型的服务方法 ---
        validated_response: CreateOrderResponse = payment_service.create_unified_order(current_create_params)
        # -----------------------------------------
        logger.debug(f"下单接口响应模型: {validated_response.model_dump_json(indent=2, exclude_none=True)}")

        # --- 主要断言基于模型属性 ---
        assert validated_response.return_code == SUCCESS_CODE, \
            f"预期通信成功 (return_code='{SUCCESS_CODE}'), 实际为 '{validated_response.return_code}', msg: {validated_response.return_msg}"
        assert validated_response.result_code == SUCCESS_CODE, \
            f"预期业务成功 (result_code='{SUCCESS_CODE}'), 实际为 '{validated_response.result_code}', err: {validated_response.err_code}-{validated_response.err_msg}"
        assert validated_response.pay_url is not None, \
            "预期成功的响应中包含 'pay_url'"
        logger.info("--- 测试场景通过: 统一支付下单成功 ---")

    except (ApiRequestError, ValueError) as e:
        # ApiRequestError 可能包含 Pydantic 的 ValidationError
        logger.error(f"步骤 2 失败: 创建统一订单时出错 - {e}", exc_info=True)
        pytest.fail(f"创建统一订单失败: {e}")
    # 不需要单独捕获 AssertionError，因为 Pydantic 验证失败会抛出 ApiRequestError 或 ValueError


# --- 参数化测试 - 缺少必填字段 ---
MANDATORY_CREATE_ORDER_FIELDS = [
    # 保留原来的字段列表，但注意 one_data 和 total_fee 的类型
    "pay_type", "goods_detail", "total_fee", "spbill_create_id", "notify_url", "one_data" # 添加 one_data
    # "return_url" 在模型中是 Optional，不再是必填
]

@pytest.mark.api
@pytest.mark.negative
@pytest.mark.parametrize("field_to_omit", MANDATORY_CREATE_ORDER_FIELDS)
@allure.title("统一支付下单 - 缺少必填字段: {field_to_omit}")
def test_unified_order_missing_mandatory_field(
    payment_service: PaymentService,
    payment_api_data: dict,
    field_to_omit: str
):
    """测试创建订单时缺少指定的必填字段。"""
    logger.info(f"--- 测试场景: 创建订单缺少必填字段: {field_to_omit} ---")
    base_params_yaml = payment_api_data.get('base_create_order_params')
    if not base_params_yaml:
        pytest.fail("未找到 'base_create_order_params' 数据")

    create_order_params = copy.deepcopy(base_params_yaml)

    # 预处理 one_data
    try:
         if 'one_data' in create_order_params:
              create_order_params['one_data'] = parse_one_data(create_order_params['one_data'])
         else:
             if field_to_omit == 'one_data': # 如果要测试缺少 one_data，但基础数据里就没有，跳过
                 pytest.skip("基础数据不含 one_data，无法测试缺少它的情况")
                 return
    except ValueError as e:
         pytest.fail(f"测试数据准备失败 (one_data): {e}")


    if field_to_omit in create_order_params:
        del create_order_params[field_to_omit]
        logger.debug(f"移除了字段: {field_to_omit}")
    else:
        logger.warning(f"基础测试数据中不包含字段 {field_to_omit}，跳过此参数组合")
        pytest.skip(f"基础数据不含字段 {field_to_omit}")
        return

    # 预期行为：现在预期 API 调用成功返回，但业务失败，total_fee 缺失时可能返回 null 导致验证错误
    if field_to_omit == 'total_fee':
        # 特殊处理：total_fee 缺失导致 API 可能返回 null，触发模型验证错误
        try:
            with pytest.raises(ApiRequestError) as excinfo:
                 payment_service.create_unified_order(create_order_params)
            logger.info(f"场景通过: 缺少字段 '{field_to_omit}' 时按预期捕获到 ApiRequestError: {excinfo.value}")
            # 检查是否因为输入为 None 导致的模型验证错误
            assert "input_value=None" in str(excinfo.value) and "model_type" in str(excinfo.value), \
                f"缺少字段 '{field_to_omit}' 时，预期 ApiRequestError 是关于 None 输入的模型错误，实际: '{excinfo.value}'"
        except Exception as e:
            logger.error(f"测试缺少 {field_to_omit} 时发生意外情况 (非预期 ApiRequestError)", exc_info=True)
            pytest.fail(f"测试缺少 {field_to_omit} 时发生意外情况: {e}")
    else:
        # 其他字段缺失，预期业务失败
        try:
            validated_response: CreateOrderResponse = payment_service.create_unified_order(create_order_params)
            logger.debug(f"缺少字段 '{field_to_omit}' 时的响应: {validated_response.model_dump_json(indent=2, exclude_none=True)}")

            # --- 断言业务失败和错误信息 ---
            assert validated_response.return_code == SUCCESS_CODE, \
                f"缺少字段 '{field_to_omit}' 时，预期通信成功 (return_code='{SUCCESS_CODE}'), 实际为 '{validated_response.return_code}'"
            assert validated_response.result_code == FAILED_CODE, \
                f"缺少字段 '{field_to_omit}' 时，预期业务失败 (result_code='{FAILED_CODE}'), 实际为 '{validated_response.result_code}'"
            assert validated_response.err_msg is not None, \
                f"缺少字段 '{field_to_omit}' 时，预期业务失败应包含 err_msg"
            logger.info(f"场景通过: 缺少字段 '{field_to_omit}' 时按预期业务失败，err_msg: '{validated_response.err_msg}'")

        except (ApiRequestError, ValueError, TypeError) as e:
            # 如果这里仍然捕获到异常，说明服务层在处理前就出错了，或者 API 返回了无法解析的格式
            logger.error(f"缺少字段 '{field_to_omit}' 时发生意外异常", exc_info=True)
            pytest.fail(f"缺少字段 '{field_to_omit}' 时发生意外异常: {e}")


# --- 参数化测试 - 无效格式或类型 ---
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.parametrize("test_case_data", INVALID_FORMAT_CASES_DATA, ids=INVALID_FORMAT_IDS)
@allure.title("统一支付下单 - 参数格式或类型无效")
def test_unified_order_invalid_format_or_type(
    payment_service: PaymentService,
    payment_api_data: dict,
    test_case_data: dict
):
    """测试创建订单时提供无效格式或类型的字段值。"""
    field_name = test_case_data['field_name']
    invalid_value = test_case_data['invalid_value']
    expected_error_msg_part = test_case_data['expected_error_msg_part']
    test_name = test_case_data.get('name', f'{field_name}={invalid_value}')

    logger.info(f"--- 测试场景 (from conftest/YAML): {test_name} ---")

    base_params_yaml = payment_api_data.get('base_create_order_params')
    if not base_params_yaml:
        pytest.fail("未找到 'base_create_order_params' 数据")

    create_order_params = copy.deepcopy(base_params_yaml)
    # 预处理 one_data
    try:
         if 'one_data' in create_order_params:
              create_order_params['one_data'] = parse_one_data(create_order_params['one_data'])
    except ValueError as e:
         pytest.fail(f"测试数据准备失败 (one_data): {e}")

    if field_name not in create_order_params and field_name != 'total_fee': # total_fee 在模型中是 int
         logger.warning(f"基础数据不含字段 {field_name}，跳过此无效格式测试: {test_name}")
         pytest.skip(f"基础数据不含字段 {field_name}")
         return

    create_order_params[field_name] = invalid_value
    logger.debug(f"修改参数: {create_order_params}")

    # --- 测试执行和断言逻辑 ---
    if field_name == "total_fee":
        # 预期捕获到服务层处理非 JSON 响应时抛出的 ApiRequestError
        with pytest.raises(ApiRequestError) as excinfo:
            payment_service.create_unified_order(create_order_params)
        logger.info(f"场景通过: [{test_name}] 无效 total_fee 时按预期捕获到 ApiRequestError: {excinfo.value}")
        # 断言错误信息包含 服务层包装的 "响应不是有效的 JSON"
        error_message = str(excinfo.value)
        assert "响应不是有效的 JSON" in error_message, \
               f"[{test_name}] 无效 total_fee 时，预期 ApiRequestError 包含 '响应不是有效的 JSON', 实际: '{error_message}'"
    else:
        # 对于其他字段，预期业务失败
        try:
            validated_response: CreateOrderResponse = payment_service.create_unified_order(create_order_params)
            logger.debug(f"[{test_name}] 响应模型: {validated_response.model_dump_json(indent=2, exclude_none=True)}")

            assert validated_response.return_code == SUCCESS_CODE, \
                f"[{test_name}] 预期通信成功 (return_code='{SUCCESS_CODE}')"
            assert validated_response.result_code == FAILED_CODE, \
                f"[{test_name}] 预期业务失败 (result_code='{FAILED_CODE}'), 实际为 '{validated_response.result_code}'"
            assert validated_response.err_msg is not None, \
                f"[{test_name}] 预期业务失败应包含 err_msg"
            assert expected_error_msg_part.lower() in validated_response.err_msg.lower(), \
                f"[{test_name}] 预期错误信息 err_msg ('{validated_response.err_msg}') 包含 '{expected_error_msg_part}'"

            logger.info(f"场景通过: [{test_name}] 无效 {field_name} 时按预期业务失败，err_msg: '{validated_response.err_msg}'")

        except (ApiRequestError, ValueError, TypeError) as e:
            # 如果这里仍然捕获到异常，说明服务层在处理前就出错了
            logger.error(f"[{test_name}] 测试无效 {field_name} 时发生意外异常", exc_info=True)
            pytest.fail(f"[{test_name}] 测试无效 {field_name} 时发生意外异常: {e}")
        except Exception as e:
            # 捕获未预期的成功或其他异常
            logger.error(f"[{test_name}] 测试无效 {field_name} 时发生未知意外情况", exc_info=True)
            pytest.fail(f"[{test_name}] 测试无效 {field_name} 时发生未知意外情况: {e}")


# --- 参数化测试 - 长度约束 ---
@pytest.mark.api
@pytest.mark.parametrize("test_case_data", LENGTH_CONSTRAINT_CASES_DATA, ids=LENGTH_CONSTRAINT_IDS)
@allure.title("统一支付下单 - 参数长度约束")
def test_unified_order_length_constraint(
    payment_service: PaymentService,
    payment_api_data: dict,
    test_case_data: dict
):
    """测试创建订单时特定字段的长度约束。"""
    field_name = test_case_data['field_name']
    test_value = test_case_data['test_value']
    expect_success = test_case_data['expect_success']
    expected_error_msg_part = test_case_data['expected_error_msg_part']
    test_name = test_case_data.get('name', f'{field_name} len={len(str(test_value))}')

    logger.info(f"--- 测试场景 (from conftest/YAML): {test_name} ---")

    base_params_yaml = payment_api_data.get('base_create_order_params')
    if not base_params_yaml:
        pytest.fail("未找到 'base_create_order_params' 数据")

    create_order_params = copy.deepcopy(base_params_yaml)
    # 预处理 one_data
    try:
         if 'one_data' in create_order_params:
              create_order_params['one_data'] = parse_one_data(create_order_params['one_data'])
    except ValueError as e:
         pytest.fail(f"测试数据准备失败 (one_data): {e}")


    if field_name not in create_order_params:
         logger.warning(f"基础数据不含字段 {field_name}，跳过此长度约束测试: {test_name}")
         pytest.skip(f"基础数据不含字段 {field_name}")
         return

    current_test_value = str(test_value)
    current_len = len(current_test_value)

    if field_name == "out_trade_no" and expect_success:
        required_length = len(current_test_value)
        unique_prefix = payment_service.data_generator.generate_out_trade_no(f"LEN{required_length}_")
        current_test_value = unique_prefix[:required_length]
        logger.info(f"[{test_name}] 预期成功场景：为 out_trade_no (长度 {required_length}) 生成唯一值: {current_test_value}")

    create_order_params[field_name] = current_test_value
    logger.debug(f"最终使用的参数: {create_order_params}")

    # --- 测试执行和断言逻辑 ---
    try:
        validated_response: CreateOrderResponse = payment_service.create_unified_order(create_order_params)
        logger.debug(f"[{test_name}] 响应模型: {validated_response.model_dump_json(indent=2, exclude_none=True)}")

        if expect_success:
            # 断言业务成功
            assert validated_response.return_code == SUCCESS_CODE, f"[{test_name}] 预期通信成功"
            assert validated_response.result_code == SUCCESS_CODE, \
                f"[{test_name}] 预期 '{field_name}' 长度 {current_len} 时成功, 实际 result_code='{validated_response.result_code}'"
            assert validated_response.pay_url is not None, f"[{test_name}] 成功时应有 pay_url"
            logger.info(f"场景通过: [{test_name}] 长度 {current_len} 时成功")
        else:
            # 断言业务失败
            assert validated_response.return_code == SUCCESS_CODE, f"[{test_name}] 预期通信成功"
            assert validated_response.result_code == FAILED_CODE, \
                f"[{test_name}] 预期 '{field_name}' 长度 {current_len} 时业务失败, 实际 result_code='{validated_response.result_code}'"
            assert validated_response.err_msg is not None, f"[{test_name}] 失败时应有 err_msg"
            if expected_error_msg_part:
                 assert expected_error_msg_part in validated_response.err_msg, \
                    f"[{test_name}] 预期错误信息包含 '{expected_error_msg_part}'，实际为: '{validated_response.err_msg}'"
            logger.info(f"场景通过: [{test_name}] 长度 {current_len} 时业务按预期失败")

    except (ApiRequestError, ValueError) as e:
         # 如果是预期成功的场景捕获到异常，则测试失败
         if expect_success:
              logger.error(f"[{test_name}] 预期长度 {current_len} 成功但捕获异常", exc_info=True)
              pytest.fail(f"[{test_name}] 预期长度 {current_len} 成功但捕获异常: {e}")
         # 如果是预期失败的场景捕获到异常，检查错误信息是否符合预期
         else:
              logger.info(f"场景通过: [{test_name}] 长度 {current_len} 时失败 (捕获异常: {e})")
              error_str = str(e).lower()
              if expected_error_msg_part:
                   assert expected_error_msg_part.lower() in error_str, \
                        f"[{test_name}] 捕获的异常信息 '{e}' 未包含预期片段 '{expected_error_msg_part}'"
              else:
                   # 如果预期失败但没有特定错误信息，接受任何 ApiRequestError 或 ValueError
                   pass
    except Exception as e:
        logger.error(f"[{test_name}] 测试长度约束时发生未知意外错误", exc_info=True)
        pytest.fail(f"[{test_name}] 测试长度约束时发生未知意外错误: {e}")


# --- 测试无效签名 ---
@pytest.mark.api
@pytest.mark.negative
@allure.title("统一支付下单 - 无效签名")
def test_unified_order_invalid_signature(
    payment_service: PaymentService,
    payment_api_data: dict,
    monkeypatch
):
    """测试创建订单时提供无效签名。"""
    logger.info("--- 测试场景: 创建订单提供无效签名 ---")
    base_params_yaml = payment_api_data.get('base_create_order_params')
    if not base_params_yaml:
        pytest.fail("未找到 'base_create_order_params' 数据")

    create_order_params = copy.deepcopy(base_params_yaml)
    # 预处理 one_data
    try:
         if 'one_data' in create_order_params:
              create_order_params['one_data'] = parse_one_data(create_order_params['one_data'])
    except ValueError as e:
         pytest.fail(f"测试数据准备失败 (one_data): {e}")

    invalid_sign = "INVALID_SIGNATURE_FOR_TEST"

    def mock_calculate_sign(*args, **kwargs):
        logger.debug("Mocked calculate_md5_sign called, returning invalid sign")
        return invalid_sign

    target_module_path = 'src.api.services.payment_service.calculate_md5_sign'
    try:
        monkeypatch.setattr(target_module_path, mock_calculate_sign, raising=False)
    except (AttributeError, ImportError) as patch_err:
         logger.error(f"无法 monkeypatch calculate_md5_sign: {patch_err}", exc_info=True)
         pytest.fail(f"Monkeypatching 失败: {patch_err}")
         return

    # 预期：API 请求会成功，但返回业务失败，错误信息与签名相关
    try:
        validated_response: CreateOrderResponse = payment_service.create_unified_order(create_order_params)
        logger.debug(f"错误响应模型: {validated_response.model_dump_json(indent=2, exclude_none=True)}")

        assert validated_response.return_code == SUCCESS_CODE, \
             f"预期无效签名时 return_code='{SUCCESS_CODE}', 实际='{validated_response.return_code}'"
        assert validated_response.result_code == FAILED_CODE, \
             f"预期无效签名时 result_code='{FAILED_CODE}', 实际='{validated_response.result_code}'"
        assert ERR_MSG_SIGNATURE in validated_response.err_msg, \
             f"预期无效签名时 err_msg 包含 '{ERR_MSG_SIGNATURE}', 实际='{validated_response.err_msg}'"
        # 检查 return_msg 是否也包含签名错误 (根据实际 API 行为调整)
        if validated_response.return_msg:
             assert ERR_MSG_SIGNATURE in validated_response.return_msg, \
                 f"预期无效签名时 return_msg 包含 '{ERR_MSG_SIGNATURE}', 实际='{validated_response.return_msg}'"

        logger.info(f"场景通过: 无效签名时业务按预期失败 (包含 '{ERR_MSG_SIGNATURE}')")

    except ApiRequestError as e:
         # 如果 API 请求本身就失败了（例如网络错误），则不符合此场景预期
         logger.error(f"测试无效签名时发生未预期的 ApiRequestError", exc_info=True)
         pytest.fail(f"测试无效签名时发生未预期的 ApiRequestError: {e}")
    except Exception as e:
        logger.error("测试无效签名时发生未知意外错误", exc_info=True)
        pytest.fail(f"测试无效签名时发生未知意外错误: {e}")


# --- 测试重复订单号 ---
@pytest.mark.api
@pytest.mark.negative
@allure.title("统一支付下单 - 重复订单号")
def test_unified_order_duplicate_out_trade_no(
    payment_service: PaymentService,
    payment_api_data: dict
):
    """测试使用相同的商户订单号 (`out_trade_no`) 连续创建两次订单。"""
    logger.info("--- 测试场景: 创建订单使用重复 out_trade_no ---")
    base_params_yaml = payment_api_data.get('base_create_order_params')
    if not base_params_yaml:
        pytest.fail("未找到 'base_create_order_params' 数据")

    create_order_params = copy.deepcopy(base_params_yaml)
     # 预处理 one_data
    try:
         if 'one_data' in create_order_params:
              create_order_params['one_data'] = parse_one_data(create_order_params['one_data'])
    except ValueError as e:
         pytest.fail(f"测试数据准备失败 (one_data): {e}")

    unique_out_trade_no = payment_service.data_generator.generate_out_trade_no("DUPLTEST_")
    create_order_params['out_trade_no'] = unique_out_trade_no

    # 步骤 1: 第一次成功下单
    logger.info(f"步骤 1: 首次调用 create_unified_order, out_trade_no={unique_out_trade_no}")
    try:
        response1: CreateOrderResponse = payment_service.create_unified_order(create_order_params)
        assert response1.return_code == SUCCESS_CODE, f"首次下单通信失败: {response1.return_msg}"
        assert response1.result_code == SUCCESS_CODE, \
            f"首次下单业务失败 (result_code != {SUCCESS_CODE}): {response1.err_msg}"
        logger.info(f"首次下单成功, out_trade_no: {unique_out_trade_no}")
    except (ApiRequestError, ValueError) as e:
         logger.error(f"首次下单意外失败: {e}", exc_info=True)
         pytest.fail(f"首次下单意外失败: {e}")
         return

    # 步骤 2: 使用相同的参数再次下单 (包含相同的 out_trade_no)
    logger.info(f"步骤 2: 使用相同的 out_trade_no ({unique_out_trade_no}) 再次调用 create_unified_order")
    try:
        response2: CreateOrderResponse = payment_service.create_unified_order(create_order_params)
        logger.debug(f"重复订单响应模型: {response2.model_dump_json(indent=2, exclude_none=True)}")

        # 断言通信成功，业务失败
        assert response2.return_code == SUCCESS_CODE, f"重复订单请求通信失败: {response2.return_msg}"
        assert response2.result_code == FAILED_CODE, \
             f"预期重复订单请求 result_code='{FAILED_CODE}', 实际={response2.result_code}"

        # 检查错误信息是否包含重复订单提示
        assert response2.err_msg is not None, "重复订单失败时应有 err_msg"
        assert ERR_MSG_DUPLICATE_ORDER in response2.err_msg, \
            f"预期错误信息包含 '{ERR_MSG_DUPLICATE_ORDER}'，实际为: '{response2.err_msg}'"

        logger.info(f"场景通过: 重复订单号业务按预期失败 (包含 '{ERR_MSG_DUPLICATE_ORDER}')")

    except (ApiRequestError, ValueError) as e:
         # 如果第二次请求出现意外错误（不是预期的业务失败）
         logger.error(f"测试重复订单号时发生意外错误", exc_info=True)
         pytest.fail(f"测试重复订单号时发生意外错误: {e}")
    except Exception as e:
        logger.error("测试重复订单号时发生未知意外错误", exc_info=True)
        pytest.fail(f"测试重复订单号时发生未知意外错误: {e}")

# 注意：可以根据需要添加更多场景，例如并发请求、特定业务逻辑边界值等。