# API自动化测试开发指南

## 1. 引言

### 1.1 指南目的

本指南旨在为测试人员提供一个清晰、详细的步骤指导，以便在本自动化测试框架内开发API自动化测试用例。无论你是否熟悉本项目，遵循本指南都可以帮助你快速上手并编写出符合规范的API测试。本指南不仅包含操作步骤，也致力于解释关键的技术概念和设计思想。

### 1.2 目标读者

本指南主要面向负责API自动化测试开发的**测试工程师**，包括对Python和自动化测试框架有不同程度了解的同学。

### 1.3 基础要求

在开始之前，建议具备以下基础知识：

*   **基本的Python编程知识**: 理解变量、函数、类、数据类型（字典、列表等）。
*   **了解HTTP协议**: 知道GET、POST等请求方法，理解状态码（200, 404, 500等）、请求头、请求体。
*   **了解API**: 知道什么是API，如何通过工具（如Postman）调用API。
*   **了解数据格式**: 对 JSON 和 YAML 这两种常见的数据交换格式有基本认识。

## 2. 项目背景与核心概念

### 2.1 七层架构概览

本项目采用标准的七层架构设计，旨在实现高内聚、低耦合。API测试主要涉及以下几个层级和目录：

*   **测试用例层 (`tests/`)**:
    *   `tests/api/`: 存放所有API测试脚本 (`test_*.py` 文件)。**这是你主要编写代码的地方**。
*   **固件层 (`tests/`)**:
    *   `tests/conftest.py`: 全局共享的测试配置和辅助函数 (**Fixtures**)。全局共享的 Fixtures（比如通用的日志配置）可以放在这里。
    *   `tests/api/conftest.py`: API测试专用的 **Fixtures**。特定于 API 测试的 Fixtures（如 `api_client`, `user_service` 等）应放在这里，以保持模块化。
*   **业务对象层 (`src/`, `data/`)**:
    *   `src/api/services/`: **API服务对象**。封装了调用相关API的逻辑。**你的测试用例主要通过调用这些服务对象的方法来与API交互**。
    *   `data/api/`: 存放API测试所需的数据文件（YAML或JSON格式），实现**数据驱动**。
*   **平台实现层 (`src/`)**:
    *   `src/api/`: 底层API请求发送的实现，通常使用 `httpx` 库。测试人员一般**不需要直接修改**。
    *   `src/api/models/`: **API数据模型**。使用 `Pydantic` 定义请求和响应的数据结构，用于**数据验证**。
*   **核心抽象层 (`src/`)**:
    *   `src/core/base/`: 定义了框架的基础接口、自定义**异常**等。
*   **工具层 (`src/`)**:
    *   `src/utils/`: 提供各种通用工具，如配置加载、日志记录、数据生成等。

> **重要**: 在开始编码前，请务必花时间阅读 `docs/enhanced_architecture.md` 文档，以深入理解项目架构。 (遵循 `project-documentation-first` 规则)

### 2.2 核心组件与技术点解释

理解以下核心组件和技术点，有助于你更好地使用本框架：

*   **`pytest` (测试引擎与指挥官)**:
    *   **是什么**: 一个成熟、功能丰富的 Python 测试框架。它是我们组织、执行和管理所有自动化测试的**核心引擎**。
    *   **主要特性**:
        *   **测试发现**: 自动查找并执行 `tests/` 目录下以 `test_` 开头的文件和函数/方法。
        *   **断言 (`assert`)**: 使用简单的 `assert` 语句进行结果验证，失败时 pytest 会提供详细的错误信息。
        *   **Fixtures (测试"零件"与"装备")**: 这是 `pytest` 的**核心特性**。Fixture 是特殊的函数（通常定义在 `conftest.py` 中，并使用 `@pytest.fixture` 装饰器），用于为测试函数提供所需的**测试环境、数据或服务实例** (比如前面例子中的 `user_service`)。它们实现了**依赖注入**，让测试代码更简洁、可复用，并能方便地管理资源的创建和销毁（如自动关闭数据库连接或HTTP客户端）。Fixture 可以设置不同的**作用域**（`function`, `class`, `module`, `session`），决定其多久被创建和销毁一次，这对于控制资源（如数据库连接或浏览器实例）的生命周期非常重要。
        *   **标记 (`Markers`, `@pytest.mark`)**: 用于给测试函数打标签（如 `@pytest.mark.smoke`, `@pytest.mark.api`），方便我们根据需要选择性地执行部分测试用例。
        *   **参数化 (`Parameterization`, `@pytest.mark.parametrize`)**: 允许你用**多组不同的输入数据**来运行同一个测试函数。这对于实现**数据驱动测试**（用不同的数据测同一个逻辑）非常有用，可以避免写大量重复的测试代码。我们在步骤4的例子中会看到它与YAML数据的结合。
        *   **插件 (`Plugins`)**: `pytest` 的强大之处在于其丰富的插件生态。插件可以扩展 `pytest` 的功能，例如：
            *   `pytest-html`: 生成 HTML 格式的测试报告。
            *   `pytest-xdist`: 支持并行执行测试，加快速度。
            *   `pytest-cov`: 计算代码测试覆盖率。
            *   `allure-pytest`: 集成 Allure 报告框架，生成更美观、功能更丰富的报告（本项目使用）。

*   **`httpx` (HTTP通信专家)**:
    *   **是什么**: 一个现代化的、支持同步和异步请求的 Python HTTP 客户端库。
    *   **在框架中的作用**: 它位于**平台实现层**，负责实际与后端API服务器进行通信。我们的 `UserService` 等服务对象内部会使用 `httpx` 来发送 `GET`, `POST` 等请求，处理请求头、查询参数、请求体（通常是JSON），接收响应，并获取状态码和响应内容。
    *   **测试人员交互**: 你通常**不需要直接**在测试用例中调用 `httpx`。框架的设计目标是让你通过调用**服务对象**（如 `user_service.get_user_info()`）来间接使用 `httpx`，从而隐藏底层的HTTP细节，让测试代码更关注业务逻辑。

*   **`Pydantic` (数据建模与校验大师)**:
    *   **是什么**: 一个基于 Python 类型注解的数据验证库。
    *   **在框架中的作用**:
        1.  **数据建模**: 在 `src/api/models/` 中，我们使用 Pydantic 来定义 API **请求体**和**响应体**的预期数据结构（就像创建数据蓝图）。这使得数据结构清晰、易于理解。
        2.  **数据验证**: 当服务对象收到 API 的响应时，会尝试使用对应的 Pydantic 模型来解析和验证响应数据。如果响应数据的格式、类型或值不符合模型的定义（例如，缺少必填字段、邮箱格式错误、状态值无效），Pydantic 会自动**抛出验证错误** (`ValidationError`)。这极大地保证了我们测试结果的可靠性，因为我们不仅检查了请求是否成功，还严格检查了返回的数据是否符合预期规范。
        3.  **简化断言**: 因为服务对象方法通常会返回**已验证过的 Pydantic 模型实例**，所以在测试用例中，你可以直接访问模型的属性（如 `user_info.name`）并进行断言，代码更简洁、易读。

*   **YAML/JSON (数据食谱)**:
    *   **是什么**: 轻量级的数据交换格式。
    *   **在框架中的作用**: 主要用于在 `data/api/` 目录下存储**测试数据**（如不同场景的请求参数、预期结果等）和在 `config/` 目录下存储**配置信息**。使用 YAML 或 JSON 可以让数据与代码分离，便于维护和管理。

*   **Allure (报告展示艺术家)**:
    *   **是什么**: 一个灵活的、支持多语言的测试报告框架。
    *   **在框架中的作用**: 与 `pytest` 集成（通过 `allure-pytest` 插件），收集测试执行过程中的信息，并生成详细、美观、交互式的 HTML 测试报告。报告可以包含测试步骤、日志、截图、附件等，方便分析测试结果和定位问题。

*   **数据驱动 (测试设计思想)**:
    *   **是什么**: 一种测试方法，将测试输入数据和预期输出结果从测试逻辑中分离出来，存储在外部（如YAML文件）。测试框架读取这些数据，并循环执行相同的测试逻辑。
    *   **在框架中的体现**: 我们通过将测试数据存储在 `data/api/` 的 YAML 文件中，并结合 `pytest` 的**参数化**功能 (`@pytest.mark.parametrize`) 来实现数据驱动。这样做的好处是，增加新的测试场景通常只需要修改数据文件，而不需要修改测试代码。

*   **服务对象 (Service Objects, 业务封装者)**:
    *   **是什么**: 位于 `src/api/services/` 的 Python 类。
    *   **在框架中的作用**: 它们是**测试用例与底层 API 调用之间的桥梁**。每个服务对象通常封装了一组相关业务功能的 API 调用逻辑（例如 `UserService` 封装用户增删改查的 API 调用）。它们负责构建请求（可能需要处理签名、认证等）、调用 `httpx` 发送请求、解析响应、使用 Pydantic 模型验证响应数据，并处理常见的错误情况（如网络错误、API业务错误），最后向测试用例返回一个清晰的结果（通常是 Pydantic 模型实例或抛出特定异常）。
    *   **为什么重要**: 让测试代码更简洁、更稳定、更易于维护，因为它隐藏了复杂的 API 调用细节，并提供了一个面向业务的接口。通过 **Fixtures** 进行**依赖注入**（例如，将配置好的 `httpx.Client` 注入到服务对象中），可以进一步提高代码的可测试性和灵活性。

*   **自定义异常 (错误信号灯)**:
    *   **是什么**: 在 `src/core/base/errors.py` 中定义的、继承自 Python 内建 `Exception` 的类 (遵循 `specific-exceptions` 规则)。
    *   **在框架中的作用**: 用于更精确地表示不同类型的错误情况（例如 `ApiRequestError`, `ResourceNotFoundError`)。服务对象在遇到特定错误时（如 API 返回 404），会抛出这些自定义异常。测试用例可以通过捕获这些特定异常 (`pytest.raises`) 来验证负向测试场景是否按预期失败。

### 2.3 关键开发流程概览

1.  **理解API需求**: 获取并理解API文档。
2.  **定义数据模型**: 在 `src/api/models/` 使用 Pydantic 定义请求/响应模型。
3.  **实现服务逻辑**: 在 `src/api/services/` 查找或创建服务对象，添加调用API并返回Pydantic模型的方法。
4.  **准备测试数据**: 在 `data/api/` 创建或更新YAML文件，包含各场景的输入和预期结果（值或异常）。
5.  **编写测试用例**: 在 `tests/api/` 创建 `test_*.py` 文件，使用 Fixture 获取服务实例和数据，调用服务方法，并使用 `assert` 或 `pytest.raises` 验证结果。
6.  **运行与调试**: 使用 `pytest` 命令执行测试，查看日志和 Allure 报告。

## 3. 环境准备

### 3.1 安装项目依赖

确保你已经按照项目 `README.md` 或 `docs/enhanced_architecture.md` 中的说明设置好了Python环境 (>=3.11)。然后，在项目根目录下执行以下命令安装所有依赖：

```bash
poetry install
```

这会自动安装 `pyproject.toml` 文件中定义的所有主依赖和开发依赖。 (遵循 `environment-setup` 规则)

### 3.2 配置环境

项目配置（如API基础URL、认证信息等）通过 `.env` 文件和 `config/` 目录下的文件管理。

*   **`.env` 文件**: 用于存放本地开发环境的敏感信息（如API密钥、密码）。**此文件不应提交到版本控制系统**。请根据 `.env.example` 文件创建你自己的 `.env` 文件并填入必要的值。 (遵循 `secure-data-handling` 规则)
*   **`config/` 目录**: 存放非敏感配置，如 `settings.yaml` (默认配置) 和 `config/env/` 下的环境特定配置。配置通过 `src/utils/config/manager.py` 加载。 (遵循 `external-configuration` 规则)

### 3.3 获取API文档

在编写测试之前，你需要了解待测试API的详细信息：

*   **请求URL**: API的完整地址。
*   **请求方法**: GET, POST, PUT, DELETE 等。
*   **请求头**: 如 `Content-Type`, `Authorization` 等。
*   **请求体**: POST/PUT请求的数据格式和内容。
*   **预期响应**: 成功的状态码、响应头、响应体结构和内容（字段名、类型等）。
*   **错误响应**: 不同错误情况下的状态码和响应体结构。

这些信息通常可以从API开发者提供的文档（如Swagger UI、OpenAPI规范文件、Postman Collection）中获取。

## 4. 编写第一个API测试（逐步指南）

假设我们要测试一个获取用户信息的API：

*   **功能**: 根据用户ID获取用户信息。
*   **URL**: `/users/{user_id}` (基础URL在配置中定义)
*   **方法**: GET
*   **成功响应**:
    *   状态码: 200
    *   响应体 (JSON): `{"id": user_id, "name": "...", "email": "...", "status": "..."}`
*   **失败响应 (示例)**:
    *   用户不存在: 状态码 404, 响应体 `{"error": "User not found"}`
    *   无效用户ID: 状态码 400, 响应体 `{"error": "Invalid user ID format"}`

### 步骤 1: 定义数据模型 (Pydantic Models)

*   **位置**: `src/api/models/` (可能需要新建 `user_models.py`)
*   **操作**: 定义API响应的数据结构。这是使用 **Pydantic** 技术的体现。

```python
# src/api/models/user_models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserInfoResponse(BaseModel):
    id: int = Field(..., description="用户唯一标识")
    name: str = Field(..., description="用户名")
    email: Optional[EmailStr] = Field(None, description="用户邮箱") # EmailStr 会自动验证邮箱格式
    status: str = Field(..., description="用户状态 (e.g., active, inactive)")
    # ... 其他你关心的字段

# 可以为错误响应定义模型（如果结构统一）
# class ErrorResponse(BaseModel):
#     error: str
```

### 步骤 2: 查找或创建服务对象 (Service Layer)

检查 `src/api/services/` 目录下是否已经有处理用户相关API的服务对象，例如 `user_service.py`。这是**封装业务逻辑**的地方。

*   **如果已存在**: 查看是否有类似 `get_user_info(user_id)` 的方法。如果没有，可以添加。
*   **如果不存在**: 创建一个新的文件，例如 `src/api/services/user_service.py`。

**示例 `src/api/services/user_service.py` (返回Pydantic模型)**:

```python
# src/api/services/user_service.py
import httpx
from typing import Dict, Any, Optional
import logging
from pydantic import ValidationError # 导入 ValidationError

# 假设模型和配置管理器已导入
from src.api.models.user_models import UserInfoResponse # 导入 Pydantic 模型
# (假设)从 utils 导入配置管理器，实际可能通过依赖注入获取配置
from src.utils.config import ConfigManager
# (假设)从 core 导入自定义异常 (位于 src/core/base/errors.py)
from src.core.base.errors import ApiRequestError, ResourceNotFoundError

class UserService:
    """封装用户相关API操作的服务类 (返回Pydantic模型)"""

    # 注意：在实际框架中，推荐通过依赖注入或 Fixture 传入 httpx.Client 实例
    # 而不是在 __init__ 中创建，以方便管理生命周期和配置
    def __init__(self, client: httpx.Client, base_url: Optional[str] = None):
        """
        初始化用户服务。

        Args:
            client: httpx 客户端实例 (通常由 Fixture 提供)。
            base_url: API的基础URL (可选，如果 client 未配置 base_url)。
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = client
        # base_url 最好在 client 初始化时配置，这里作为备选
        self.base_url_fallback = base_url or ConfigManager.load().get('api', {}).get('base_url')

    def get_user_info(self, user_id: int | str, headers: Optional[Dict[str, str]] = None) -> UserInfoResponse:
        """
        根据用户ID获取用户信息，并返回经过验证的 Pydantic 模型。
        该方法负责处理 HTTP 请求和基础响应校验，以及 Pydantic 模型验证。

        Args:
            user_id: 要查询的用户ID。服务层会尝试处理 int 或 str 类型，但最终的API调用可能需要特定类型。
            headers: 额外的请求头 (例如认证信息)。

        Returns:
            UserInfoResponse: 验证后的用户信息模型。

        Raises:
            ResourceNotFoundError: 如果API返回404，表示用户不存在。
            ApiRequestError: 其他API请求错误（如网络问题、非200/404状态码）或响应数据验证失败。
        """
        url = f"/users/{user_id}" # 构造相对路径，依赖 client 的 base_url
        endpoint_desc = f"获取用户信息 (ID: {user_id})" # 用于日志和错误信息

        self.logger.info(f"开始 {endpoint_desc}，请求 URL: {url}")
        response = None
        try:
            # 准备最终请求头
            effective_headers = self.client.headers.copy() # 获取 client 的默认头
            if headers:
                effective_headers.update(headers) # 合并传入的头

            # 执行 HTTP GET 请求
            response = self.client.get(url, headers=effective_headers)
            self.logger.info(f"收到 {endpoint_desc} 响应: 状态码={response.status_code}")
            response_body_preview = response.text[:100] + '...' if len(response.text) > 100 else response.text
            self.logger.debug(f"响应体预览: {response_body_preview}")

            # 根据状态码进行处理
            if response.status_code == 200:
                try:
                    # 尝试解析 JSON 并用 Pydantic 模型验证
                    validated_data = UserInfoResponse.model_validate(response.json())
                    self.logger.info(f"{endpoint_desc} 响应通过 Pydantic 模型验证")
                    return validated_data
                except ValidationError as e:
                    # Pydantic 验证失败
                    self.logger.error(f"{endpoint_desc} 响应体验证失败: {e}\n原始响应: {response.text}", exc_info=True)
                    # 抛出自定义异常，封装错误信息
                    raise ApiRequestError(f"{endpoint_desc} 响应验证失败") from e
                except Exception as e: # 例如 json.JSONDecodeError
                    self.logger.error(f"{endpoint_desc} 响应解析失败: {e}\n原始响应: {response.text}", exc_info=True)
                    raise ApiRequestError(f"{endpoint_desc} 响应解析失败") from e
            elif response.status_code == 404:
                # 用户不存在，抛出特定的 ResourceNotFoundError
                self.logger.warning(f"{endpoint_desc} - 用户不存在 (404)")
                raise ResourceNotFoundError(f"用户 ID '{user_id}' 未找到")
            # elif response.status_code == 400:
                # # 可以为 400 Bad Request (如无效 ID 格式) 抛出更具体的异常
                # self.logger.warning(f"{endpoint_desc} - 请求格式错误 (400)")
                # error_body = response.text
                # try: error_body = response.json()
                # except: pass
                # raise InvalidInputError(f"{endpoint_desc} 请求参数无效", response_body=error_body) # 假设有 InvalidInputError
            else:
                # 其他未预期的 HTTP 错误状态码
                self.logger.error(f"{endpoint_desc} 请求失败，状态码: {response.status_code}, 响应: {response.text}")
                error_body = response.text
                try: error_body = response.json() # 尝试解析错误体
                except: pass
                # 抛出通用的 API 请求错误，包含状态码和响应体
                raise ApiRequestError(f"{endpoint_desc} API返回错误状态 {response.status_code}",
                                      status_code=response.status_code,
                                      response_body=error_body)

        except httpx.RequestError as e:
            # 处理 httpx 请求级别的错误 (网络问题、DNS错误等)
            self.logger.error(f"{endpoint_desc} 请求时发生网络错误: {e}", exc_info=True)
            raise ApiRequestError(f"{endpoint_desc} 网络请求错误") from e
        # 注意：避免捕获顶级 Exception，让特定异常冒泡给测试用例

    # ... 其他用户相关的API方法 ...

    # close 方法通常由管理 client 的 Fixture 负责，服务对象自身可能不需要 close
    # def close(self): ...
```

**要点** (与第 2.2 节呼应):

*   服务对象封装了 `httpx` 的调用细节。
*   返回 **Pydantic 模型**实例，隐藏了解析和验证步骤。
*   `httpx.Client` 通常由 **Fixture** 提供 (体现**依赖注入**)。
*   遵循了日志、配置、异常处理、类型注解等规范。

### 步骤 3: 准备测试数据 (YAML Data)

在 `data/api/` 目录下创建数据文件，例如 `user_data.yaml`。这是**数据驱动**的体现。

```yaml
# data/api/user_data.yaml

get_user_info:
  valid_user:
    user_id: 123
    # expected_status: 200 # 状态码检查已移到服务层
    expected_values: # 验证具体业务值
      id: 123
      name: "Expected Test User" # 假设我们知道预期名字
      email: "test@example.com"
      status: "active"
    # request_headers: # 如果需要特定请求头
    #   Authorization: "Bearer FAKE_TOKEN"

  non_existent_user:
    user_id: 99999
    # expected_status: 404 # 状态码检查已移到服务层
    expected_exception: ResourceNotFoundError # 预期服务层抛出的异常类型名称 (来自 src.core.base.errors)
    # expected_error_msg_part: "未找到" # 可选，验证异常信息的一部分

  invalid_user_id_format:
    user_id: "abc" # 格式错误
    # 预期服务层依赖API返回错误(如400或404)，然后服务层抛出ApiRequestError或ResourceNotFoundError
    expected_exception: ApiRequestError # 或者 ResourceNotFoundError, 取决于API如何响应无效ID格式
    # expected_error_msg_part: "API返回错误状态 400" # 可选，验证异常信息的一部分

```

**要点**:

*   测试数据与代码分离。
*   预期结果关注业务值 (`expected_values`) 或特定异常 (`expected_exception`)。

### 步骤 4: 编写测试用例 (Pytest Tests)

在 `tests/api/` 目录下创建测试文件，例如 `test_user_api.py`。

*   **确保 `conftest.py` (`tests/api/conftest.py`) 中有 Fixtures**:
    *   提供 **`UserService` 实例** 的 fixture，通常它会依赖并自动获取一个配置好的 **`httpx.Client` 实例** fixture。
    *   还需要一个 fixture 来 **加载并提供 `user_data.yaml` 中的测试数据**。
    *   *(假设这些 Fixtures 已按规范定义在 `tests/api/conftest.py` 中)*

**示例 `test_user_api.py` (调用返回 Pydantic 模型的方法)**:

```python
# tests/api/test_user_api.py
import pytest
import logging
from pathlib import Path # 用于辅助 conftest 加载数据

# 导入服务对象和 Pydantic 模型
from src.api.services.user_service import UserService
from src.api.models.user_models import UserInfoResponse
# 导入预期的自定义异常
from src.core.base.errors import ApiRequestError, ResourceNotFoundError

# ---- 测试用例 ----

# 使用 pytest.mark 进行标记
@pytest.mark.api
@pytest.mark.smoke
def test_get_valid_user_info(user_service: UserService, user_api_data: dict):
    """
    测试获取有效用户的信息。
    使用 user_service Fixture 获取服务实例。
    使用 user_api_data Fixture 获取 YAML 数据。
    断言服务层返回的 Pydantic 模型属性。
    """
    test_data = user_api_data.get('get_user_info', {}).get('valid_user')
    if not test_data: pytest.fail("测试数据 'get_user_info.valid_user' 未找到")

    user_id = test_data['user_id']
    expected_values = test_data.get('expected_values')
    if not expected_values: pytest.fail("测试数据缺少 'expected_values'")
    headers = test_data.get('request_headers')

    logging.info(f"测试场景: 获取有效用户信息 (ID: {user_id})")

    try:
        # 调用服务方法，预期返回 UserInfoResponse 模型实例
        user_info: UserInfoResponse = user_service.get_user_info(user_id, headers=headers)

        # 直接在模型属性上进行断言 (assert)
        assert user_info.id == expected_values['id']
        assert user_info.name == expected_values['name']
        assert user_info.email == expected_values['email']
        assert user_info.status == expected_values['status']

        logging.info("测试通过: 成功获取用户信息，且模型数据验证通过")

    except (ApiRequestError, ResourceNotFoundError) as e:
        # 如果预期成功的场景抛出了我们定义的业务或请求异常，则测试失败
        pytest.fail(f"预期成功但获取用户信息失败 (ID: {user_id}): {e}")
    except Exception as e:
        # 捕获其他意外错误
        pytest.fail(f"测试有效用户信息时发生意外错误: {e}", pytrace=True)

@pytest.mark.api
@pytest.mark.negative
def test_get_non_existent_user(user_service: UserService, user_api_data: dict):
    """
    测试获取不存在的用户信息。
    预期服务层抛出 ResourceNotFoundError 异常。
    使用 pytest.raises 来捕获和验证异常。
    """
    test_data = user_api_data.get('get_user_info', {}).get('non_existent_user')
    if not test_data: pytest.fail("测试数据 'get_user_info.non_existent_user' 未找到")

    user_id = test_data['user_id']
    # 从数据中获取预期的异常类型名称字符串
    expected_exception_name = test_data.get('expected_exception')
    if not expected_exception_name: pytest.fail("测试数据缺少 'expected_exception'")

    # 通过 YAML 中定义的异常名称字符串，动态查找对应的异常类
    # (这样做是为了保持测试数据驱动，避免在测试代码中硬编码或导入所有异常类型)
    try:
        # 尝试从当前模块或已导入的模块中查找
        expected_exception_type = globals().get(expected_exception_name) or \
                                 getattr(__import__('src.core.base.errors'), expected_exception_name)
    except (AttributeError, ImportError):
         pytest.fail(f"无法找到预期的异常类型: {expected_exception_name}")


    logging.info(f"测试场景: 获取不存在的用户信息 (ID: {user_id})")

    # 使用 pytest.raises 作为上下文管理器来断言异常
    with pytest.raises(expected_exception_type) as exc_info:
        user_service.get_user_info(user_id)

    # (可选) 断言异常信息的内容
    expected_msg_part = test_data.get('expected_error_msg_part')
    if expected_msg_part:
        assert expected_msg_part in str(exc_info.value)

    logging.info(f"测试通过: 获取不存在用户时按预期抛出 {expected_exception_name}: {exc_info.value}")


@pytest.mark.api
@pytest.mark.negative
def test_get_user_invalid_id_format(user_service: UserService, user_api_data: dict):
    """
    测试使用无效格式的用户ID。
    预期服务层处理错误或 API 返回错误，最终由服务层抛出 ApiRequestError 或 ResourceNotFoundError。
    """
    test_data = user_api_data.get('get_user_info', {}).get('invalid_user_id_format')
    if not test_data: pytest.fail("测试数据 'get_user_info.invalid_user_id_format' 未找到")

    user_id = test_data['user_id'] # "abc"
    expected_exception_name = test_data.get('expected_exception')
    if not expected_exception_name: pytest.fail("测试数据缺少 'expected_exception'")

    try:
        expected_exception_type = globals().get(expected_exception_name) or \
                                 getattr(__import__('src.core.base.errors'), expected_exception_name)
    except (AttributeError, ImportError):
         pytest.fail(f"无法找到预期的异常类型: {expected_exception_name}")

    logging.info(f"测试场景: 使用无效格式的用户ID ({user_id})")

    with pytest.raises(expected_exception_type) as exc_info:
        # 调用服务方法。服务层会处理类型转换或依赖API返回错误
        user_service.get_user_info(user_id)

    # (可选) 检查异常信息或属性
    expected_msg_part = test_data.get('expected_error_msg_part')
    if expected_msg_part:
        assert expected_msg_part in str(exc_info.value)
    # 例如，如果预期是ApiRequestError并包含400状态码
    # if isinstance(exc_info.value, ApiRequestError):
    #     assert exc_info.value.status_code == 400

    logging.info(f"测试通过: 使用无效格式ID时按预期抛出 {expected_exception_name}: {exc_info.value}")
```

**要点**:

*   测试用例调用**服务对象**，而非直接操作 `httpx`。
*   利用 **Fixtures** (`user_service`, `user_api_data`) 获取依赖和数据。
*   断言直接作用于服务层返回的 **Pydantic 模型**属性，或使用 `pytest.raises` 验证预期的**自定义异常**。
*   (如果需要测多组数据) 可以在测试函数上使用 `@pytest.mark.parametrize` 结合 YAML 数据实现**参数化**。

## 5. 执行测试与查看报告

### 5.1 执行测试

你可以通过 `pytest` 命令执行测试：

*   **执行所有测试**:
    ```bash
    pytest
    ```
*   **仅执行API测试 (根据标记)**:
    ```bash
    pytest -m api
    ```
*   **执行特定文件的测试**:
    ```bash
    pytest tests/api/test_user_api.py
    ```
*   **执行特定测试函数**:
    ```bash
    pytest tests/api/test_user_api.py::test_get_valid_user_info
    ```
*   **生成Allure报告数据**:
    ```bash
    pytest --alluredir=output/allure-results
    ```
    (确保 `output/allure-results` 目录存在)

### 5.2 查看Allure报告

1.  首先，确保你已经安装了 Allure 命令行工具。
2.  执行完带有 `--alluredir` 参数的 `pytest` 命令后，运行以下命令生成并打开HTML报告：

    ```bash
    allure generate output/allure-results --clean -o output/reports/allure-report
    allure open output/reports/allure-report
    ```

这会在你的默认浏览器中打开一个交互式的 **Allure** 测试报告。

## 6. 遵循的最佳实践与项目规范

在开发API测试时，请务必牢记并遵守以下项目规范 (`.cursor/rules/` 目录)：

*   **代码分析优先 (`code-analysis-first`)**: 检查是否已有类似实现。 (详见 `.cursor/rules/code-analysis-first.mdc`)
*   **代码风格一致性 (`code-consistency`)**: 使用 Black, Pylint, MyPy。 (详见 `.cursor/rules/code-consistency.mdc`)
*   **强制业务代码实现 (`force-business-implementation`)**: 编写实际业务逻辑。 (详见 `.cursor/rules/force-business-implementation.mdc`)
*   **接口先行原则 (`interface-first-principle`)**: 复杂服务可考虑接口。 (详见 `.cursor/rules/interface-first-principle.mdc`)
*   **日志标准化 (`logging-standards`)**: 使用 `logging`。 (详见 `.cursor/rules/logging-standards.mdc`)
*   **配置外部化 (`external-configuration`)**: 使用 `config/` 和 `.env`。 (详见 `.cursor/rules/external-configuration.mdc`)
*   **资源自动释放 (`resource-management`)**: **Fixture** 通常负责管理资源。 (详见 `.cursor/rules/resource-management.mdc`)
*   **安全数据处理 (`secure-data-handling`)**: 不硬编码敏感信息。 (详见 `.cursor/rules/secure-data-handling.mdc`)
*   **七层架构设计 (`seven-layer-architecture`)**: 代码放置在正确目录。 (详见 `.cursor/rules/seven-layer-architecture.mdc`)
*   **异常专一性 (`specific-exceptions`)**: 使用**自定义异常**。 (详见 `.cursor/rules/specific-exceptions.mdc`)
*   **测试数据分离 (`test-data-separation`)**: 使用 `data/` 和**数据驱动**。 (详见 `.cursor/rules/test-data-separation.mdc`)
*   **类型注解强制 (`type-annotations`)**: 使用类型提示。 (详见 `.cursor/rules/type-annotations.mdc`)
*   **版本控制 (`version-control`)**: 遵循提交规范。 (详见 `.cursor/rules/version-control.mdc`)

## 7. 常见问题与调试

*   **`AssertionError`**: 断言失败。检查失败信息，对比预期结果和实际响应的模型属性值。
*   **`FileNotFoundError`**: 测试数据 (`data/`) 或配置文件 (`config/`) 未找到。检查路径是否正确，文件是否存在。
*   **`ApiRequestError` (封装了 `ConnectionError` / `TimeoutError`)**: 网络问题。检查网络、API服务状态、URL配置、超时。
*   **`AttributeError`**: 访问了模型对象上不存在的属性。检查模型定义 (`src/api/models/`) 是否与API实际返回一致。
*   **`ApiRequestError` (封装了 `401`/`403`)**: 认证失败。检查认证信息是否正确、有效，并由 Fixture 正确注入到 `httpx.Client` 的请求头中。
*   **`ApiRequestError` (封装了 `pydantic.ValidationError`)**: API响应结构与模型定义不符。**检查服务层日志**中的原始响应体和 Pydantic 错误详情，对比模型定义 (`src/api/models/`)。
*   **`ResourceNotFoundError` 等自定义异常**: 服务层按预期（负向场景）或意外（正向场景）捕获到特定业务错误。查看异常信息和日志判断原因。

**调试技巧**:

*   **日志是关键**: 仔细查看 `logging` 输出的 DEBUG 和 INFO 级别的日志，特别是服务层记录的请求 URL、头、响应码、响应体预览和错误详情。
*   **打印模型**: 在测试用例中打印返回的模型实例 `print(user_info.model_dump())` 查看数据。
*   **调试器**: 使用 IDE 的调试器或 `import pdb; pdb.set_trace()` 设置断点，检查服务层内部或测试用例中的变量。
*   **Postman/curl**: 使用外部工具独立验证 API 的行为，排除测试代码本身的问题。

---

希望这份经过大幅补充和优化的指南能更好地帮助你和其他测试同学理解和使用这个自动化测试框架！如果在实践中遇到任何问题，请参考项目文档或与其他团队成员交流。