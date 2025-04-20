# src/core/base 核心抽象层说明

本目录用于定义自动化测试框架的核心接口、抽象基类和异常体系，确保各平台实现和业务对象的解耦与可扩展性。

## 主要内容
- 所有平台（Web/API/移动端）通用的接口定义（如 BaseDriver、BaseElement、BaseConditionHandler 等）
- 层次化异常体系（如 AutomationError、DriverError、ElementError、ApiError 等）
- 条件与等待机制的抽象接口（如 ExpectedCondition、BaseConditionHandler 等）
- 业务对象和平台实现必须依赖接口而非具体实现，禁止跨层依赖
- 推荐使用 Python ABC 抽象基类，便于类型检查和扩展

## 设计原则
- 先定义接口，再实现具体类（见 interface-first-principle.mdc）
- 所有公共API必须加类型注解和Google风格docstring（见 type-annotations.mdc、documentation-completeness.mdc）
- 命名、注释、类型注解需与项目规范一致（见 code-consistency.mdc）
- 异常体系分层清晰，所有异常类以Error结尾，docstring需说明异常场景（见 specific-exceptions.mdc）
- 新增接口、抽象基类或异常时，务必补充本 README

## 最佳实践示例
```python
from abc import ABC, abstractmethod
from typing import Any

class BaseDriver(ABC):
    """浏览器驱动基础接口。"""
    @abstractmethod
    async def get_element(self, selector: str) -> Any:
        """获取单个元素。"""
        pass

class AutomationError(Exception):
    """自动化测试框架基础异常类。"""
    pass
```

## 参考
- .cursor/rules/interface-first-principle.mdc
- .cursor/rules/code-consistency.mdc
- .cursor/rules/type-annotations.mdc
- .cursor/rules/documentation-completeness.mdc
- .cursor/rules/specific-exceptions.mdc
