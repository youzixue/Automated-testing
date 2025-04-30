import httpx
from src.utils.log.manager import get_logger
from typing import Dict, Any, Optional, Union
import json

# --- Pydantic Imports ---
from pydantic import ValidationError
from src.api.models.payment_models import (
    CreateOrderResponse,
    CreateOrderRequestParams, # 用于内部校验或类型提示
    GetSignRequestParams,     # 用于内部校验或类型提示
    OneDataModel,             # 用于处理 one_data
)
# ------------------------

from src.utils.config.manager import get_config
from src.utils.signature import calculate_md5_sign
from src.utils.data_generator import DataGenerator
from src.core.base.errors import ApiRequestError

class PaymentService:
    """
    封装支付相关 API 操作的服务类 (已集成 Pydantic)。
    """
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        初始化支付服务。

        Args:
            base_url: API 的基础 URL。如果为 None，则尝试从配置加载。
            api_key: 用于签名的 API 密钥 (key)。如果为 None，则尝试从配置/环境变量加载。
        """
        self.logger = get_logger(self.__class__.__name__) # 使用 get_logger
        self.config = get_config() # 加载合并后的配置

        # 获取基础 URL (修正为读取 api.base_url)
        self.base_url = base_url or self.config.get('api', {}).get('base_url')
        if not self.base_url:
            # 更新错误消息中的配置路径
            self.logger.error("API 基础 URL 未配置 (在配置文件的 api -> base_url 或通过 ${env:API_BASE_URL})")
            raise ValueError("API 基础 URL 未配置")

        # 获取签名密钥 (优先从参数获取，其次从配置)
        # get_config 已经处理了环境变量替换 ${env:PAYMENT_API_KEY}
        self.api_key = api_key or self.config.get('api', {}).get('payment', {}).get('key')
        if not self.api_key:
            self.logger.error("支付 API 签名密钥 (key) 未配置 (在配置文件的 api -> payment -> key 或通过 ${env:PAYMENT_API_KEY})")
            raise ValueError("支付 API 签名密钥未配置")

        # 获取其他必要配置 (保持读取 api.payment 下的特定配置)
        self.mch_id = self.config.get('api', {}).get('payment', {}).get('mch_id')
        self.device_info = self.config.get('api', {}).get('payment', {}).get('device_info')

        # --- !!! 添加调试打印，查看实际读取到的 MCH_ID 和 DEVICE_INFO !!! ---
        print(f"[DEBUG] PaymentService __init__: Read mch_id: {self.mch_id} (from config['api']['payment']['mch_id'])")
        print(f"[DEBUG] PaymentService __init__: Read device_info: {self.device_info} (from config['api']['payment']['device_info'])")
        # ------------------------------------------------------------

        if not self.mch_id:
            self.logger.warning("商户号 (mch_id) 未在配置中找到 (api -> payment -> mch_id)")
        if not self.device_info:
            self.logger.warning("设备号 (device_info) 未在配置中找到 (api -> payment -> device_info)")

        self.client = httpx.Client(base_url=self.base_url, timeout=30.0, verify=False)
        self.data_generator = DataGenerator()
        self.default_headers = {"Content-Type": "application/json"}

    def _prepare_common_params(self, specific_params: Dict[str, Any]) -> Dict[str, Any]:
        """准备包含动态和通用参数的字典"""
        params = {
            "mch_id": self.mch_id,
            "device_info": self.device_info,
            "nonce_str": self.data_generator.generate_nonce_str(),
            "out_trade_no": self.data_generator.generate_out_trade_no(),
            "trade_expire_time": self.data_generator.generate_trade_expire_time(),
            "charset": "UTF-8",
            "sign_type": "MD5",
            # 添加来自 specific_params 的参数，它们会覆盖通用参数（如果键相同）
            **specific_params
        }
        # 过滤掉值为 None 的参数，以防万一
        return {k: v for k, v in params.items() if v is not None}

    def _prepare_request_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备最终发送给 API 的请求数据字典。
        处理 one_data 序列化和 total_fee 转字符串。
        """
        request_data = params.copy() # 操作副本

        # 序列化 one_data (如果它是 OneDataModel 实例)
        if 'one_data' in request_data and isinstance(request_data['one_data'], OneDataModel):
            try:
                # 使用 Pydantic 的方法导出为 JSON 字符串，确保兼容别名
                request_data['one_data'] = request_data['one_data'].model_dump_json(by_alias=True)
            except Exception as e:
                self.logger.error(f"序列化 one_data 模型失败: {e}", exc_info=True)
                raise ValueError(f"无法将 one_data 模型序列化为 JSON: {e}") from e
        # 如果传入的已经是字符串，则直接使用 (保持兼容性)
        elif 'one_data' in request_data and not isinstance(request_data['one_data'], str):
             # 如果不是 Model 也不是 str，可能需要报错或尝试转换
             try:
                 request_data['one_data'] = json.dumps(request_data['one_data'], ensure_ascii=False)
             except TypeError as e:
                 self.logger.error(f"无法将 one_data (类型: {type(request_data['one_data'])}) 转换为 JSON 字符串: {e}")
                 raise ValueError(f"one_data 必须是 OneDataModel 实例或有效的 JSON 字符串") from e


        # 转换 total_fee 为字符串
        if 'total_fee' in request_data and isinstance(request_data['total_fee'], int):
            request_data['total_fee'] = str(request_data['total_fee'])
        elif 'total_fee' in request_data and not isinstance(request_data['total_fee'], str):
            # 如果不是 int 也不是 str，尝试转换，失败则报错
            try:
                request_data['total_fee'] = str(request_data['total_fee'])
            except Exception as e:
                 self.logger.error(f"无法将 total_fee (类型: {type(request_data['total_fee'])}) 转换为字符串: {e}")
                 raise ValueError("total_fee 必须能转换为字符串") from e

        # 可以在这里添加更多数据准备逻辑，例如日期格式化等

        return request_data

    def get_payment_sign(self, order_params: Dict[str, Any]) -> str:
        """
        调用 /open/sign/paySign 接口获取支付签名。

        Args:
            order_params: 订单相关参数，至少需要包含 total_fee, one_data, sub_appid, sub_openid 等。
                          也可能包含 attach, detail, notify_url, pay_type, return_url 等。

        Returns:
            从接口获取的签名字符串。

        Raises:
            ApiRequestError: 如果请求失败或无法获取签名。
            ValueError: 如果必要的 order_params 缺失。
        """
        endpoint = "/open/sign/paySign"
        self.logger.info(f"开始获取支付签名，目标: {endpoint}")

        # 1. 准备基础参数 (合并通用和特定参数)
        prepared_params = self._prepare_common_params(order_params)
        prepared_params['appKey'] = self.api_key # 获取签名需要 appKey

        # 可选: 使用 Pydantic 模型验证合并后的参数结构
        try:
            # 尝试验证，需要处理 one_data 可能已经是字符串的情况
            params_for_validation = prepared_params.copy()
            if 'one_data' in params_for_validation and isinstance(params_for_validation['one_data'], str):
                try:
                    # 尝试解析回模型以进行验证
                    params_for_validation['one_data'] = OneDataModel.model_validate_json(params_for_validation['one_data'])
                except (ValidationError, json.JSONDecodeError) as json_error:
                     self.logger.warning(f"无法将字符串 one_data 解析回模型进行验证: {json_error}")
                     # 无法解析时，不对 one_data 进行模型验证，继续其他字段验证
                     # 或者直接移除 one_data 进行部分验证
                     if 'one_data' in params_for_validation: # 确保存在再删除
                         del params_for_validation['one_data']

            GetSignRequestParams.model_validate(params_for_validation)
        except ValidationError as e:
            self.logger.error(f"获取签名接口的输入参数验证失败: {e}")
            raise ValueError(f"获取签名输入参数无效: {e}") from e

        # 2. 准备实际发送的数据 (处理 one_data, total_fee 等)
        request_data_to_send = self._prepare_request_data(prepared_params)

        # 3. 计算签名 (使用处理后的数据)
        try:
            request_data_to_send['sign'] = calculate_md5_sign(
                request_data_to_send, self.api_key, request_data_to_send.get("charset", "UTF-8")
            )
        except (ValueError, RuntimeError) as e:
            self.logger.error(f"为 {endpoint} 计算签名失败: {e}", exc_info=True)
            raise ApiRequestError(f"获取支付签名失败：无法计算签名") from e

        # 4. 记录和发送请求 (使用处理后的数据)
        log_headers = self.default_headers.copy()
        self.logger.debug(f"--> 请求 [GET SIGN]:\n"
                          f"    Method: POST\n"
                          f"    URL: {self.base_url}{endpoint}\n"
                          f"    Headers: {json.dumps(log_headers, indent=2)}\n"
                          f"    Body: {json.dumps(request_data_to_send, indent=2, ensure_ascii=False)}")

        try:
            response = self.client.post(endpoint, headers=self.default_headers, json=request_data_to_send)

            log_response_headers = dict(response.headers)
            response_body_preview = response.text[:500] + ('...' if len(response.text) > 500 else '')
            self.logger.debug(f"<-- 响应 [GET SIGN]:\n"
                              f"    Status Code: {response.status_code}\n"
                              f"    Headers: {json.dumps(log_response_headers, indent=2)}\n"
                              f"    Body: {response_body_preview}")

            response.raise_for_status() # 检查 HTTP 状态码

            obtained_sign = response.text.strip()
            if not obtained_sign:
                self.logger.error(f"{endpoint} 返回了空的签名响应体。")
                raise ApiRequestError("获取支付签名失败：API 返回空响应")

            self.logger.info(f"成功从 {endpoint} 获取签名: {obtained_sign[:10]}...")
            return obtained_sign

        except httpx.HTTPStatusError as e:
            self.logger.error(f"请求 {endpoint} 失败，状态码: {e.response.status_code}，响应: {e.response.text}", exc_info=True)
            raise ApiRequestError(f"获取支付签名失败：API 返回错误状态 {e.response.status_code}") from e
        except httpx.RequestError as e:
            self.logger.error(f"请求 {endpoint} 时发生网络错误: {e}", exc_info=True)
            raise ApiRequestError(f"获取支付签名失败：网络请求错误") from e
        except json.JSONDecodeError as e: # get_payment_sign 预期返回纯文本签名，这里可能不需要
             self.logger.error(f"{endpoint} 响应不是预期格式 (纯文本签名)，解析错误: {e}. 响应: {response.text if response else 'N/A'}")
             raise ApiRequestError(f"获取支付签名失败：API 响应格式错误") from e
        except Exception as e:
            self.logger.error(f"处理 {endpoint} 响应时发生未知错误: {e}", exc_info=True)
            raise ApiRequestError(f"获取支付签名失败：未知错误 ({type(e).__name__})") from e

    def create_unified_order(self, order_params: Dict[str, Any]) -> CreateOrderResponse:
        """
        调用 /payment/unifiedorder 接口创建统一支付订单。
        返回经过 Pydantic 验证的响应模型。

        Args:
            order_params: 订单相关参数字典。

        Returns:
            CreateOrderResponse: 验证后的响应模型实例。

        Raises:
            ApiRequestError: 如果请求失败或响应验证失败。
            ValueError: 如果必要的输入参数缺失或转换失败。
        """
        endpoint = "/payment/unifiedorder"
        self.logger.info(f"开始创建统一支付订单，目标: {endpoint}")

        request_data_to_send = {} # 初始化
        response = None           # 初始化
        response_json = None      # 初始化

        # 1. 准备数据和签名
        try:
            prepared_params = self._prepare_common_params(order_params)
            if 'appKey' in prepared_params: # 下单接口不需要 appKey
                del prepared_params['appKey']

            # 可选: 使用 Pydantic 模型验证准备好的参数
            try:
                params_for_validation = prepared_params.copy()
                if 'one_data' in params_for_validation and isinstance(params_for_validation['one_data'], str):
                     try:
                          params_for_validation['one_data'] = OneDataModel.model_validate_json(params_for_validation['one_data'])
                     except (ValidationError, json.JSONDecodeError) as json_error:
                          self.logger.warning(f"无法将字符串 one_data 解析回模型进行验证: {json_error}")
                          if 'one_data' in params_for_validation:
                              del params_for_validation['one_data']

                # CreateOrderRequestParams 验证 total_fee 是 int，但我们需要发送 str
                # 所以在验证前可能需要处理或调整模型
                # 暂不在此处验证 CreateOrderRequestParams 以简化流程
                # CreateOrderRequestParams.model_validate(params_for_validation)
            except ValidationError as e:
                 self.logger.error(f"创建订单接口的输入参数验证失败: {e}")
                 raise ValueError(f"创建订单输入参数无效: {e}") from e


            request_data_to_send = self._prepare_request_data(prepared_params)
            current_sign = calculate_md5_sign(
                request_data_to_send, self.api_key, request_data_to_send.get("charset", "UTF-8")
            )
            request_data_to_send['sign'] = current_sign
            self.logger.debug(f"为 {endpoint} 计算签名为: {current_sign}")

        except (ValueError, RuntimeError) as e:
             self.logger.error(f"为 {endpoint} 准备数据或计算签名失败: {e}", exc_info=True)
             raise ApiRequestError(f"创建统一订单失败：准备请求失败: {e}") from e

        # 2. 发送请求、解析和验证
        try:
            log_headers = self.default_headers.copy()
            self.logger.debug(
                f"--> 请求 [CREATE ORDER]:\n"
                f"    Method: POST\n"
                f"    URL: {self.base_url}{endpoint}\n"
                f"    Headers: {json.dumps(log_headers, indent=2)}\n"
                f"    Body: {json.dumps(request_data_to_send, indent=2, ensure_ascii=False)}"
            )

            response = self.client.post(endpoint, headers=self.default_headers, json=request_data_to_send)

            response_body_preview = response.text[:500] + ('...' if len(response.text) > 500 else '')
            log_response_headers = dict(response.headers)
            self.logger.debug(
                f"<-- 响应 [CREATE ORDER]:\n"
                f"    Status Code: {response.status_code}\n"
                f"    Headers: {json.dumps(log_response_headers, indent=2)}\n"
                f"    Body: {response_body_preview}"
            )
            self.logger.info(f"收到 {endpoint} 响应，状态码: {response.status_code}")

            # 不需要显式 raise_for_status，因为我们要处理非 2xx 的 JSON 响应
            # response.raise_for_status()

            response_json = response.json() # 可能 JSONDecodeError
            validated_response = CreateOrderResponse.model_validate(response_json) # 可能 ValidationError
            self.logger.info(f"响应体通过 Pydantic 模型验证: {validated_response.return_code} / {validated_response.result_code}")
            return validated_response

        # 明确捕获预期的异常类型
        except httpx.RequestError as e:
            self.logger.error(f"请求 {endpoint} 时发生网络错误: {e}", exc_info=True)
            raise ApiRequestError(f"创建统一订单失败：网络请求错误") from e
        except json.JSONDecodeError as e:
             response_text = response.text if response is not None else "N/A"
             self.logger.error(f"{endpoint} 响应体不是有效的 JSON: {response_text}", exc_info=True) # 添加 exc_info
             raise ApiRequestError(f"创建订单失败：响应不是有效的 JSON") from e
        except ValidationError as e:
             original_json_str = str(response_json) if response_json is not None else "N/A (JSON parsing failed)"
             self.logger.error(f"{endpoint} 响应体验证失败: {e}. 原始响应 JSON: {original_json_str}", exc_info=True) # 添加 exc_info
             raise ApiRequestError(f"创建订单失败：响应数据验证失败: {e}") from e
        # 捕获所有其他未预料到的异常
        except Exception as e:
             self.logger.error(f"处理 {endpoint} 时发生未知意外错误: {e}", exc_info=True)
             raise ApiRequestError(f"创建统一订单失败：未知错误 ({type(e).__name__})") from e

    def close(self):
        """关闭内部的 HTTP 客户端。"""
        if hasattr(self, 'client') and self.client:
            try:
                self.client.close()
                self.logger.info("PaymentService 的 HTTP client 已关闭。")
            except Exception as e:
                self.logger.warning(f"关闭 PaymentService HTTP client 时出错: {e}", exc_info=True)

    # 实现上下文管理器协议，以便使用 with 语句自动关闭 client
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()