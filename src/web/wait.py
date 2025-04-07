"""
Playwright等待策略实现。

基于Playwright实现智能等待策略，支持元素状态等待和自定义条件等待。
避免硬编码等待时间，提高测试稳定性。
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Tuple

from playwright.sync_api import Locator, ElementHandle, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.core.base.wait import ElementCondition
from src.core.base.wait import WaitStrategy
from src.core.base.errors import TimeoutError, ElementNotFoundError, ConditionNotMetError
from src.web.condition_handlers import (
    PlaywrightPresentHandler,
    PlaywrightVisibleHandler,
    PlaywrightClickableHandler,
    PlaywrightTextHandler,
    PlaywrightAttributeHandler
)

# Import the condition handler registry implementation if needed
from src.web.condition_handlers import PlaywrightConditionHandlerRegistry


T = TypeVar('T')  # 结果类型
PlaywrightElement = Union[Locator, ElementHandle]


class PlaywrightWaitStrategy(WaitStrategy[Locator]):
    """Playwright等待策略实现。
    
    基于Playwright实现智能等待，支持元素状态等待和自定义条件等待。
    使用动态退避算法优化轮询间隔，提高测试稳定性。
    
    Attributes:
        page: Playwright Page对象
        default_timeout: 默认超时时间(秒)
        default_poll_frequency: 默认初始轮询频率(秒)
        backoff_factor: 退避因子，用于计算下一次轮询间隔
        max_poll_frequency: 最大轮询间隔(秒)
        condition_registry: 条件处理器注册表
    """
    
    DEFAULT_BACKOFF_FACTOR = 1.5
    DEFAULT_MAX_POLL_FREQUENCY = 5.0  # 最大轮询间隔为5秒
    
    def __init__(self, 
                page: Optional[Page] = None,
                default_timeout: float = 10, 
                default_poll_frequency: float = 0.5,
                backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
                max_poll_frequency: float = DEFAULT_MAX_POLL_FREQUENCY):
        """初始化Playwright等待策略。
        
        Args:
            page: Playwright Page对象 (Optional)
            default_timeout: 默认超时时间(秒)
            default_poll_frequency: 默认初始轮询频率(秒)
            backoff_factor: 退避因子，轮询间隔按此系数递增
            max_poll_frequency: 最大轮询间隔(秒)
        """
        self._page = page
        self._default_timeout = default_timeout
        self._default_poll_frequency = default_poll_frequency
        self._logger = logging.getLogger(self.__class__.__name__)

        self._backoff_factor = backoff_factor
        self._max_poll_frequency = min(max_poll_frequency, default_timeout / 2)
        
        # 使用 Playwright 特定的注册表实现
        self._condition_registry = PlaywrightConditionHandlerRegistry(page)
        
        self._logger.debug(f"创建Playwright等待策略：超时={default_timeout}秒, "
                         f"初始间隔={default_poll_frequency}秒, "
                         f"退避因子={backoff_factor}, "
                         f"最大间隔={self._max_poll_frequency}秒")
    
    def set_page(self, page: Page) -> None:
        """Sets the Playwright Page object for the strategy.

        This should be called after the WebDriver has initialized the page.
        Args:
            page: The Playwright Page object.
        """
        if page is None:
             raise ValueError("Page object cannot be None when setting it.")
        self._page = page
        # Update the page reference in the condition registry
        self._condition_registry.update_page(page)
        self._logger.debug("Updated page reference in condition handlers via registry.")
    
    def _get_condition_function(self,
                                condition: ElementCondition,
                                args: Dict[str, Any]
                               ) -> Callable[[], Optional[Locator]]:
        """获取处理指定条件的函数。

        Args:
            condition: 元素条件
            args: 传递给处理器的参数 (e.g., selector, text, attribute_name)

        Returns:
            处理条件的函数，返回 Locator 或 None

        Raises:
            ValueError: 不支持的条件类型或缺少必要参数
        """
        handler = self._condition_registry.get_handler(condition)
        if handler is None:
            raise ValueError(f"不支持的条件类型: {condition}")

        # Ensure 'selector' is present in args for element-based conditions
        if not isinstance(condition, Callable) and 'selector' not in args:
             # Add specific condition check if some non-element conditions exist
             raise ValueError(f"条件 {condition} 缺少必要的 'selector' 参数")

        # Return a lambda that calls the handler's check method with all arguments
        # Handler's check method expects args like selector, timeout etc.
        return lambda: handler.check(**args)
    
    def _wait_with_backoff(self, 
                          condition_fn: Callable[[], T], 
                          timeout: Optional[float] = None, 
                          poll_frequency: Optional[float] = None,
                          message: Optional[str] = None) -> T:
        """使用动态退避算法实现智能等待。
        
        根据等待时间动态调整轮询频率，开始时快速轮询，随着时间推移逐渐减慢轮询频率。
        
        Args:
            condition_fn: 条件函数，返回任何真值表示条件满足
            timeout: 超时时间(秒)，None表示使用默认超时时间
            poll_frequency: 初始轮询频率(秒)，None表示使用默认轮询频率
            message: 超时时显示的错误消息
            
        Returns:
            条件函数的返回值
            
        Raises:
            TimeoutError: 在指定时间内未满足条件
        """
        # 使用默认值
        actual_timeout = timeout if timeout is not None else self._default_timeout
        actual_poll_frequency = poll_frequency if poll_frequency is not None else self._default_poll_frequency
        
        # 初始化计时器和轮询频率
        start_time = time.time()
        end_time = start_time + actual_timeout
        current_poll_frequency = actual_poll_frequency
        attempt_count = 0
        
        self._logger.debug(f"开始等待，超时时间: {actual_timeout}秒，初始轮询频率: {actual_poll_frequency}秒")
        
        # 等待循环
        while True:
            # 执行条件检查
            attempt_count += 1
            result = condition_fn()
            elapsed = time.time() - start_time  # 提前计算已耗时间，避免日志中使用未定义变量
            
            if result:
                self._logger.debug(f"条件已满足，耗时: {elapsed:.2f}秒，总尝试次数: {attempt_count}")
                return result
                
            # 检查是否超时
            current_time = time.time()
            if current_time >= end_time:
                error_msg = message or f"等待超时，已等待{elapsed:.2f}秒"
                self._logger.warning(f"{error_msg}，总尝试次数: {attempt_count}")
                raise TimeoutError(error_msg)
                
            # 计算本次等待时间
            remaining = end_time - current_time
            
            # 动态调整轮询频率 - 随着时间推移减慢轮询，但不超过最大轮询频率
            current_poll_frequency = min(
                actual_poll_frequency * (self._backoff_factor ** attempt_count),
                self._max_poll_frequency
            )
            
            # 确保等待时间不超过剩余时间
            wait_time = min(current_poll_frequency, remaining)
            
            self._logger.debug(f"尝试次数: {attempt_count}, "
                             f"当前轮询频率: {current_poll_frequency:.3f}秒, "
                             f"本次等待: {wait_time:.3f}秒, "
                             f"已耗时: {elapsed:.2f}秒, "
                             f"剩余时间: {remaining:.2f}秒")
            
            # 执行等待
            time.sleep(wait_time)
    
    def wait_until(self, 
                  condition_fn: Callable[[], T], 
                  timeout: Optional[float] = None, 
                  poll_frequency: Optional[float] = None,
                  message: Optional[str] = None) -> T:
        """等待直到条件函数返回真值。
        
        使用动态退避算法逐渐增加轮询间隔，优化资源使用。
        
        Args:
            condition_fn: 条件函数，返回任何真值表示条件满足
            timeout: 超时时间(秒)，None表示使用默认超时时间
            poll_frequency: 初始轮询频率(秒)，None表示使用默认轮询频率
            message: 超时时显示的错误消息
            
        Returns:
            条件函数的返回值
            
        Raises:
            TimeoutError: 在指定时间内未满足条件
        """
        # 验证页面是否已设置
        if self._page is None:
            raise RuntimeError("Playwright Page对象未设置，无法执行等待操作。请确保WebDriver已初始化。")
        self._logger.debug(f"等待自定义条件函数")
        return self._wait_with_backoff(condition_fn, timeout, poll_frequency, message)
    
    def wait_for(self,
                condition: Union[ElementCondition, Callable[..., bool]],
                timeout: Optional[float] = None,
                condition_args: Optional[Dict[str, Any]] = None,
                poll_frequency: Optional[float] = None,
                message: Optional[str] = None) -> Locator:
        """等待条件满足。
        Args:
            condition: 等待条件，可以是ElementCondition枚举或自定义函数
            timeout: 超时时间(秒)，None表示使用默认超时时间
            condition_args: 传递给条件的参数 (必须包含 'selector' 当 condition 是 ElementCondition 时)
            poll_frequency: 轮询频率(秒)，None表示使用默认轮询频率
            message: 超时时显示的错误消息
        Returns:
            满足条件的元素 (Locator)
        Raises:
            TimeoutError: 在指定时间内未满足条件
            ConditionNotMetError: 条件无法满足
            ValueError: 如果 condition 是 ElementCondition 但 condition_args 中缺少 'selector'
        """
        if self._page is None:
            raise RuntimeError("Playwright Page对象未设置，无法执行等待操作。请确保WebDriver已初始化。")

        args = condition_args or {}
        actual_timeout = timeout if timeout is not None else self._default_timeout
        msg = message or f"等待条件 '{condition}' 超时 (超时时间: {actual_timeout} 秒)"

        self._logger.debug(f"等待条件: {condition}, 参数: {args}, 超时: {actual_timeout}秒")

        if isinstance(condition, ElementCondition):
            # 确保 selector 在参数中
            if 'selector' not in args:
                 raise ValueError(f"等待元素条件 {condition} 时，'selector' 必须在 condition_args 中提供")
            check_fn = self._get_condition_function(condition, args)
        elif callable(condition):
            # 对于自定义 callable，假定它自己处理参数或不需要参数
            # Wrap the callable to fit the expected signature if needed, assuming it returns Locator or None
            check_fn = lambda: condition(**args) if args else condition() # Adapt based on callable needs
        else:
            raise TypeError(f"不支持的条件类型: {type(condition)}")

        try:
            # _wait_with_backoff 期望 check_fn 返回 T 或 None
            result = self._wait_with_backoff(check_fn, actual_timeout, poll_frequency, msg)
            if result is None: # Should not happen if _wait_with_backoff raises TimeoutError correctly
                 raise TimeoutError(msg) # Defensive check
            return result # result should be a Locator here
        except TimeoutError as e:
            self._logger.warning(f"等待条件 '{condition}' 失败 (选择器: {args.get('selector', 'N/A')}): {e}")
            raise  # Re-raise the TimeoutError
        except Exception as e:
             self._logger.error(f"等待条件 '{condition}' 时发生意外错误 (选择器: {args.get('selector', 'N/A')}): {e}", exc_info=True)
             # Wrap unexpected errors into ConditionNotMetError or re-raise specific framework errors
             raise ConditionNotMetError(f"等待条件 '{condition}' 时出错: {e}") from e

    def wait_for_any(self,
                    conditions: List[Union[ElementCondition, Callable[..., bool]]],
                    timeout: Optional[float] = None,
                    condition_args: Optional[List[Dict[str, Any]]] = None,
                    poll_frequency: Optional[float] = None,
                    message: Optional[str] = None) -> Locator:
        """等待任意一个条件满足。
        Args:
            conditions: 等待条件列表
            timeout: 超时时间(秒)
            condition_args: 与 conditions 对应的参数列表 (每个 dict 必须包含 'selector' 当对应 condition 是 ElementCondition 时)
            poll_frequency: 轮询频率(秒)
            message: 超时错误消息
        Returns:
            满足任一条件的元素 (Locator)
        Raises:
            TimeoutError: 超时
            ValueError: 参数不匹配或缺少 'selector'
        """
        if self._page is None:
            raise RuntimeError("Playwright Page对象未设置，无法执行等待操作。请确保WebDriver已初始化。")

        actual_timeout = timeout if timeout is not None else self._default_timeout
        actual_poll = poll_frequency if poll_frequency is not None else self._default_poll_frequency
        args_list = condition_args or ([{}] * len(conditions))

        if len(conditions) != len(args_list):
            raise ValueError("conditions 和 condition_args 的长度必须匹配")

        msg = message or f"等待任何条件 {conditions} 超时 (超时时间: {actual_timeout} 秒)"
        self._logger.debug(f"等待任意条件: {conditions}, 参数: {args_list}, 超时: {actual_timeout}秒")

        condition_fns = []
        selectors = set() # Track selectors involved
        for i, cond in enumerate(conditions):
            args = args_list[i]
            if isinstance(cond, ElementCondition):
                 if 'selector' not in args:
                      raise ValueError(f"等待元素条件 {cond} (索引 {i}) 时，'selector' 必须在对应的 condition_args 中提供")
                 selectors.add(args['selector'])
                 condition_fns.append(self._get_condition_function(cond, args))
            elif callable(cond):
                 # Assume callable handles its own args or context
                 condition_fns.append(lambda c=cond, a=args: c(**a) if a else c())
            else:
                 raise TypeError(f"不支持的条件类型: {type(cond)}")

        def check_any_condition() -> Optional[Locator]:
            """检查是否有任何一个条件满足。"""
            for i, fn in enumerate(condition_fns):
                try:
                    result = fn()
                    if result:
                        self._logger.debug(f"条件 {conditions[i]} (索引 {i}) 已满足")
                        return result
                except Exception as e:
                     # Log errors during individual checks but continue checking others
                     self._logger.warning(f"检查条件 {conditions[i]} 时出错: {e}", exc_info=False)
            return None # No condition met in this poll cycle

        try:
            result = self._wait_with_backoff(check_any_condition, actual_timeout, actual_poll, msg)
            if result is None:
                 raise TimeoutError(msg)
            return result
        except TimeoutError as e:
            self._logger.warning(f"等待任何条件失败 ({list(selectors)}): {e}")
            raise
        except Exception as e:
            self._logger.error(f"等待任何条件时发生意外错误 ({list(selectors)}): {e}", exc_info=True)
            raise ConditionNotMetError(f"等待任何条件时出错: {e}") from e

    @property
    def timeout(self) -> float:
        """获取默认超时时间。"""
        return self._default_timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        """设置默认超时时间。"""
        if value <= 0:
            raise ValueError("超时时间必须大于0")
        self._default_timeout = value
        self._max_poll_frequency = min(self._max_poll_frequency, value / 2) # Adjust max poll based on new timeout
        self._logger.info(f"默认超时时间已更新为: {value}秒") 