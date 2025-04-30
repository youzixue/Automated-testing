from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
import re

# ================= Response Models =================

class CreateOrderResponse(BaseModel):
    """
    统一支付下单接口 (/payment/unifiedorder) 的响应模型。
    """
    return_code: str = Field(..., description="通信标识: SUCCESS/FAIL")
    return_msg: Optional[str] = Field(None, description="通信错误信息，如签名失败")

    # --- 业务结果 (当 return_code 为 SUCCESS 时存在) ---
    result_code: Optional[str] = Field(None, description="业务结果: SUCCESS/FAIL/FAILED", pattern=r"^(SUCCESS|FAIL|FAILED)$")
    err_code: Optional[Union[str, int]] = Field(None, description="业务错误代码")
    err_msg: Optional[str] = Field(None, description="业务错误描述")

    # --- 成功时特有字段 (当 result_code 为 SUCCESS 时可能存在) ---
    appid: Optional[str] = Field(None, description="服务商 AppID")
    mch_id: Optional[str] = Field(None, description="服务商商户号")
    sub_appid: Optional[str] = Field(None, description="子商户 AppID")
    sub_mch_id: Optional[str] = Field(None, description="子商户商户号")
    nonce_str: Optional[str] = Field(None, description="随机字符串")
    sign: Optional[str] = Field(None, description="签名")
    pay_url: Optional[HttpUrl] = Field(None, description="支付跳转 URL") # 使用 HttpUrl 验证

    # --- 可以在这里添加其他 API 可能返回的字段 ---

    @model_validator(mode='after')
    def check_response_logic(self) -> 'CreateOrderResponse':
        """校验响应的逻辑一致性"""
        if self.return_code == "FAIL" and not self.return_msg:
             # 如果通信失败，应该有通信错误信息 (允许为空)
             pass

        if self.return_code == "SUCCESS":
            if not self.result_code:
                 raise ValueError("result_code is required when return_code is SUCCESS")
            if self.result_code == "SUCCESS":
                # 业务成功时，某些字段应该是必须的
                if not self.pay_url:
                    raise ValueError("pay_url is required when result_code is SUCCESS")
                # 暂时不强制校验 appid, mch_id 等，根据实际 API 确定
                # if not self.appid or not self.mch_id or not self.nonce_str or not self.sign:
                #      raise ValueError("appid, mch_id, nonce_str, sign are required when result_code is SUCCESS")
            elif self.result_code in ["FAIL", "FAILED"]:
                # 业务失败时，错误码和错误信息应该是必须的
                if self.err_code is None or self.err_msg is None: # 检查 None 而不是 Falsy
                    raise ValueError("err_code and err_msg are required when result_code is FAIL/FAILED")
        return self

# ================= Request Models =================

# 正则表达式常量
IP_ADDRESS_REGEX = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$" # 简单的 IPv4 格式
YYYYMMDDHHMMSS_REGEX = r"^\d{14}$" # 14位数字

class GoodsDetailItem(BaseModel):
    """one_data 中 goodsDetail 的子项模型 (示例)"""
    category: str
    spName: str
    taxRate: float
    totalAmount: float
    needDeduction: int
    sortNo: int
    orderItemId: str

    # 使用 model_config 替代 Config
    model_config = ConfigDict(populate_by_name=True)

class OneDataModel(BaseModel):
    """解析后的 one_data 模型 (示例)"""
    oneUserId: str
    consumeSceneId: str
    bizAccountId: str
    customParam: Optional[str] = None
    goodsDetail: List[GoodsDetailItem]

    # 使用 model_config 替代 Config
    model_config = ConfigDict(populate_by_name=True)

class CreateOrderRequestParams(BaseModel):
    """
    统一支付下单接口 (/payment/unifiedorder) 的请求参数模型。
    注意：模型定义的是理想状态的字段类型，服务层在发送前可能需要转换。
    例如 total_fee 需要是字符串，one_data 需要是 JSON 字符串。
    签名 sign 通常由服务层计算并添加。
    """
    mch_id: str = Field(..., description="商户号")
    device_info: Optional[str] = Field(None, description="设备号")
    nonce_str: str = Field(..., description="随机字符串", min_length=1, max_length=32)
    out_trade_no: str = Field(..., description="商户订单号", min_length=5, max_length=32)
    total_fee: int = Field(..., description="订单总金额，单位为分", gt=0) # 模型中用 int，发送前转 str
    one_data: OneDataModel # 定义为模型，在服务层序列化
    sub_appid: Optional[str] = Field(None, description="子商户 AppID")
    sub_openid: Optional[str] = Field(None, description="子商户用户标识")
    pay_type: str = Field(..., description="支付类型")
    attach: Optional[str] = Field(None, description="附加数据")
    detail: Optional[str] = Field(None, description="商品详情")
    goods_detail: Optional[str] = Field(None, description="单品优惠详情(兼容老接口)")
    notify_url: HttpUrl = Field(..., description="异步接收支付结果通知的回调地址")
    return_url: Optional[HttpUrl] = Field(None, description="支付后同步跳转地址")
    # 添加 IP 和时间格式校验
    spbill_create_id: str = Field(..., description="终端 IP", pattern=IP_ADDRESS_REGEX)
    trade_expire_time: Optional[str] = Field(None, description="交易结束时间 (YYYYMMDDHHMMSS)", pattern=YYYYMMDDHHMMSS_REGEX)
    division_flag: Optional[str] = Field(None, description="是否分账 'true'/'false'")
    asyn_division_flag: Optional[str] = Field(None, description="是否异步分账 'true'/'false'")

    charset: str = Field("UTF-8", description="字符集", pattern=r"^(UTF-8)$") # 限定为 UTF-8
    sign_type: str = Field("MD5", description="签名类型", pattern=r"^(MD5)$") # 限定为 MD5
    sign: Optional[str] = Field(None, description="签名 (由服务层生成)")

    # 使用 model_config 替代 Config
    model_config = ConfigDict(populate_by_name=True)


# 可以根据需要添加 get_payment_sign 的请求/响应模型
class GetSignRequestParams(BaseModel):
    """
    获取支付签名接口 (/open/sign/paySign) 的请求参数模型 (基于 PaymentService)。
    """
    mch_id: str
    device_info: Optional[str] = None
    nonce_str: str = Field(..., min_length=1, max_length=32)
    total_fee: int = Field(..., gt=0) # 模型中用 int
    one_data: OneDataModel # 模型
    sub_appid: Optional[str] = None
    sub_openid: Optional[str] = None
    pay_type: str
    attach: Optional[str] = None
    detail: Optional[str] = None
    goods_detail: Optional[str] = None # 兼容
    notify_url: HttpUrl
    return_url: Optional[HttpUrl] = None
    # 添加 IP 格式校验
    spbill_create_id: str = Field(..., pattern=IP_ADDRESS_REGEX)

    charset: str = Field("UTF-8", pattern=r"^(UTF-8)$")
    sign_type: str = Field("MD5", pattern=r"^(MD5)$")
    appKey: str = Field(..., description="获取签名需要 appKey") # 添加 appKey
    sign: Optional[str] = Field(None, description="签名 (由服务层生成)")

    # 使用 model_config 替代 Config
    model_config = ConfigDict(populate_by_name=True)

# --- 删除注释掉的 GetSignResponse 模型 --- 