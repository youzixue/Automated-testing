"""
异常基类和层次化的异常体系。

定义框架中使用的所有异常接口和实现，遵循层次结构和明确的命名规范。
每个异常接口对应特定的错误场景，避免使用通用异常。

- 这个文件包含了完整的异常类定义和实现。
"""

from typing import Optional, Any


class AutomationError(Exception):
    """自动化测试框架基础异常类。
    
    所有框架特定异常都应继承自此类，便于统一处理。
    
    Attributes:
        message: 错误信息
        cause: 原始异常（如果有）
    """
    
    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        """初始化异常。
        
        Args:
            message: 错误信息
            cause: 导致此异常的原始异常（如果有）
        """
        self.message = message
        self.cause = cause
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """格式化错误信息。
        
        如果有原始异常，将其包含在消息中。
        
        Returns:
            格式化后的错误信息
        """
        if self.cause:
            return f"{self.message} | 原因: {self.cause}"
        return self.message


class FrameworkError(AutomationError):
    """框架内部错误异常接口。
    
    表示框架本身的错误，而非测试执行中的错误。
    通常表示框架实现存在bug或配置错误。
    """
    pass


# 驱动相关异常接口
class DriverError(AutomationError):
    """驱动相关异常基类接口。
    
    用于表示所有与浏览器驱动相关的错误。
    """
    pass


# 元素相关异常接口
class ElementError(AutomationError):
    """元素操作相关异常基类接口。
    
    用于表示所有与UI元素交互相关的错误。
    """
    pass


class PageError(AutomationError):
    """页面操作相关异常基类接口。
    
    表示整个页面级别的错误，如页面加载失败、页面状态异常等。
    """
    pass


class LoginError(PageError):
    """登录相关异常接口。
    
    表示登录过程中出现的错误，如用户名或密码错误、验证码错误等。
    """
    pass


# 等待相关异常接口
class WaitError(AutomationError):
    """等待操作相关异常基类接口。
    
    用于表示所有与等待条件相关的错误。
    """
    pass


# 配置相关异常接口
class ConfigurationError(AutomationError):
    """配置相关异常基类接口。
    
    用于表示所有与配置加载、访问和验证相关的错误。
    """
    pass


class ConfigKeyError(ConfigurationError):
    """配置键不存在异常接口。
    
    当尝试访问不存在的配置项时抛出。
    """
    def __init__(self, key: str, message: Optional[str] = None) -> None:
        """初始化异常。
        
        Args:
            key: 不存在的配置键
            message: 错误信息，默认为None
        """
        self.key = key
        message = message or f"配置键 '{key}' 不存在"
        super().__init__(message)


class ConfigTypeError(ConfigurationError):
    """配置类型错误异常接口。
    
    当配置项值类型不符合预期时抛出。
    """
    def __init__(self, key: str, expected_type: str, actual_type: str, 
                 message: Optional[str] = None) -> None:
        """初始化异常。
        
        Args:
            key: 配置键
            expected_type: 预期类型
            actual_type: 实际类型
            message: 错误信息，默认为None
        """
        self.key = key
        self.expected_type = expected_type
        self.actual_type = actual_type
        message = message or f"配置键 '{key}' 类型错误: 预期 {expected_type}, 实际 {actual_type}"
        super().__init__(message)


class ConfigValueError(ConfigurationError):
    """配置值错误异常接口。
    
    当配置项值不符合预期范围或格式时抛出。
    """
    def __init__(self, key: str, value: Any, message: Optional[str] = None) -> None:
        """初始化异常。
        
        Args:
            key: 配置键
            value: 无效的配置值
            message: 错误信息，默认为None
        """
        self.key = key
        self.value = value
        message = message or f"配置键 '{key}' 的值 '{value}' 无效"
        super().__init__(message)


# 数据相关异常接口
class DataError(AutomationError):
    """数据相关异常基类接口。
    
    用于表示所有与数据加载、解析和验证相关的错误。
    """
    pass


# API相关异常接口
class ApiError(AutomationError):
    """API相关异常基类接口。
    
    用于表示所有与API请求和响应相关的错误。
    """
    pass


# 验证码相关异常接口
class CaptchaError(AutomationError):
    """验证码相关异常基类接口。
    
    用于表示所有与验证码识别和处理相关的错误。
    """
    pass


# 测试相关异常接口
class TestError(AutomationError):
    """测试相关异常基类接口。
    
    用于表示所有与测试执行相关的错误。
    """
    pass


# 资源相关异常接口
class ResourceError(AutomationError):
    """资源相关异常基类接口。
    
    用于表示所有与资源获取和释放相关的错误。
    """
    pass


# 安全相关异常接口
class SecurityError(AutomationError):
    """安全相关异常基类接口。
    
    用于表示所有与安全问题相关的错误。
    """
    pass


# 报告相关异常接口
class ReportError(AutomationError):
    """报告相关异常基类接口。
    
    用于表示所有与测试报告生成和处理相关的错误。
    """
    pass


# 驱动相关异常实现
class DriverInitError(DriverError):
    """驱动初始化失败异常。
    
    表示无法创建或初始化浏览器驱动实例的情况。
    """
    pass


class DriverNotStartedError(DriverError):
    """驱动未启动异常。
    
    当尝试在驱动未启动的情况下执行操作时抛出。
    """
    pass


class NavigationError(DriverError):
    """页面导航异常。
    
    表示页面导航失败，如URL无效、页面加载超时等情况。
    """
    pass


class BrowserError(DriverError):
    """浏览器操作异常。
    
    表示与浏览器窗口、标签页等相关的操作错误。
    """
    pass


# 元素相关异常实现
class ElementNotFoundError(ElementError):
    """元素未找到异常。
    
    当指定的元素在DOM中不存在时抛出。
    """
    pass


class ElementNotVisibleError(ElementError):
    """元素不可见异常。
    
    当元素存在于DOM但不可见时抛出。
    """
    pass


class ElementNotInteractableError(ElementError):
    """元素不可交互异常。
    
    当元素存在且可见，但无法与之交互（如被其他元素遮挡）时抛出。
    """
    pass


class ElementStateError(ElementError):
    """元素状态异常。
    
    当元素处于无法执行请求操作的状态时抛出（如尝试选中已选中的复选框）。
    """
    pass


# 页面操作异常实现
class PageOperationError(PageError):
    """页面操作异常。
    
    当页面操作（如导航、刷新、等待页面加载等）失败时抛出。
    """
    pass


# 等待相关异常实现
class TimeoutError(WaitError):
    """操作超时异常。
    
    当等待条件在指定时间内未满足时抛出。
    不要与Python内置的TimeoutError混淆。
    """
    pass


class ConditionNotMetError(WaitError):
    """等待条件未满足异常。
    
    当条件无法满足（而非超时）时抛出，表示一个不可恢复的等待失败。
    """
    pass


# 配置相关异常实现
class ConfigFileError(ConfigurationError):
    """配置文件错误异常。
    
    当配置文件不存在或格式错误时抛出。
    """
    pass


# 验证码相关异常实现
class CaptchaRecognitionError(CaptchaError):
    """验证码识别失败异常。
    
    当无法正确识别验证码内容时抛出。
    """
    pass


class CaptchaPreprocessingError(CaptchaError):
    """验证码图像预处理错误异常。
    
    当验证码图像预处理过程中出现错误时抛出。
    """
    pass


# API相关异常实现
class ApiRequestError(ApiError):
    """API请求异常。
    
    当发送API请求失败时如网络错误、请求格式错误等。
    """
    pass


class ApiResponseError(ApiError):
    """API响应异常。
    
    当API响应不符合预期时抛出，如状态码错误、响应格式错误等。
    """
    pass


# 数据相关异常实现
class DataLoadError(DataError):
    """数据加载失败异常。
    
    当无法从源加载数据时抛出，如文件不存在、格式错误等。
    """
    pass


class DataFormatError(DataError):
    """数据格式错误异常。
    
    当数据的格式不符合预期时抛出，如JSON解析错误、CSV格式错误等。
    """
    pass


# 测试相关异常实现
class TestSetupError(TestError):
    """测试设置失败异常。
    
    当测试前置条件（setup）无法满足时抛出。
    """
    pass


class TestTeardownError(TestError):
    """测试清理失败异常。
    
    当测试后置处理（teardown）失败时抛出。
    """
    pass


# 资源相关异常实现
class ResourceNotFoundError(ResourceError):
    """资源未找到异常。
    
    当请求的资源不存在时抛出。
    """
    pass


class ResourceBusyError(ResourceError):
    """资源忙异常。
    
    当资源正在被使用且无法获取时抛出。
    """
    pass


# 安全相关异常实现
class SecurityPermissionError(SecurityError):
    """安全权限异常。
    
    当操作因权限不足而失败时抛出。
    """
    pass


# 报告相关异常实现
class ReportFormatError(ReportError):
    """报告格式异常。
    
    当报告格式不正确或无法解析时抛出。
    """
    pass


class ReportGenerationError(ReportError):
    """报告生成异常。
    
    当生成测试报告过程中发生错误时抛出。
    """
    pass 