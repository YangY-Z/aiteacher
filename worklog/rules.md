# Python 后端开发规范

## 一、核心设计原则

### SOLID 原则
- **单一职责 (SRP)**: 每个类只负责一个功能，避免"上帝类"
- **开闭原则 (OCP)**: 对扩展开放，对修改关闭，使用抽象和接口扩展功能
- **里氏替换 (LSP)**: 子类必须能替换父类，不破坏行为契约
- **接口隔离 (ISP)**: 接口要小而专一，避免臃肿大接口
- **依赖倒置 (DIP)**: 依赖注入，面向接口编程，高层不依赖低层

### 其他原则
- **DRY**: 避免重复，相同逻辑只在一处定义
- **KISS**: 保持简单，避免过度设计
- **YAGNI**: 只实现当前需要的功能，不提前编码
- **组合优于继承**: 优先使用对象组合实现复用

---

## 二、项目结构规范

```
project/
├── src/
│   ├── core/          # 核心模块：config, security, exceptions
│   ├── api/v1/        # API层：endpoints, router
│   ├── models/        # 数据模型：domain(领域模型), schemas(DTO)
│   ├── services/      # 业务逻辑层：interfaces, implementations
│   ├── repositories/  # 数据访问层
│   └── utils/         # 工具函数
├── tests/             # 测试：unit, integration, fixtures
├── alembic/           # 数据库迁移
└── docs/              # 文档
```

### 分层架构职责

| 层级 | 职责 | 依赖方向 |
|------|------|----------|
| API层 | 请求处理、参数验证、响应格式化 | → Service层 |
| Service层 | 业务逻辑、事务管理 | → Repository层 |
| Repository层 | 数据持久化、查询封装 | → Domain Model |
| Domain层 | 领域模型、业务规则 | 独立 |

---

## 三、代码风格规范

### 命名约定
- **模块/包**: 小写下划线 (`my_module.py`)
- **类名**: 大驼峰 (`UserService`)
- **函数/方法**: 小写下划线 (`get_user_by_id`)
- **变量**: 小写下划线 (`user_name`)
- **常量**: 全大写下划线 (`MAX_RETRY_COUNT`)
- **私有**: 单下划线前缀 (`_validate_email`)

### 类型注解（Python 3.9+ 必须使用）
```python
def get_user(user_id: int) -> Optional[User]:
    pass

def get_users(ids: List[int]) -> List[User]:
    pass

def get_metadata(key: str) -> Dict[str, Any]:
    pass
```

### 文档字符串（Google风格）
```python
def create_user(username: str, email: str) -> User:
    """创建新用户。

    Args:
        username: 用户名，3-50字符。
        email: 用户邮箱地址。

    Returns:
        新创建的用户对象。

    Raises:
        ValidationError: 参数格式错误时抛出。
        DuplicateUserError: 用户已存在时抛出。
    """
    pass
```

---

## 四、架构设计规范

### 依赖注入
```python
# 使用Protocol定义接口
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> Optional[User]: ...

# 通过构造函数注入依赖
class UserService:
    def __init__(self, repository: UserRepository, cache: Optional[CacheService] = None):
        self._repository = repository
        self._cache = cache
```

### 仓储模式
```python
class BaseRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[T]: ...

    @abstractmethod
    def create(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ...
```

### 领域模型与DTO分离
- **领域模型**: 使用dataclass，包含业务逻辑和规则
- **DTO**: 使用Pydantic BaseModel，用于API请求/响应
- 必须实现 `from_domain()` 方法进行转换

---

## 五、错误处理规范

### 自定义异常体系
```python
class AppException(Exception):
    """应用基础异常"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

class ValidationError(AppException): ...
class EntityNotFoundError(AppException): ...
class DuplicateEntityError(AppException): ...
class AuthenticationError(AppException): ...
class AuthorizationError(AppException): ...
```

### 全局异常处理
- 按异常类型映射HTTP状态码
- 记录错误日志（包含request_id、path、details）
- 返回统一格式错误响应

---

## 六、配置管理规范

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 环境变量 > .env文件 > 默认值
    app_name: str = "My App"
    database_url: str  # 必填
    redis_url: Optional[str] = None
    secret_key: str  # 必填
    debug: bool = False
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"
```

---

## 七、API设计规范

### RESTful 规范
- URL使用名词复数：`/api/v1/users`
- HTTP方法表达意图：GET查询、POST创建、PUT更新、DELETE删除
- 版本控制：`/api/v1/`、`/api/v2/`

### 统一响应格式
```python
class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T]
    message: Optional[str]
    meta: Optional[PaginationMeta]  # 分页时使用
```

---

## 八、安全规范

### 必须遵守
- 密码使用bcrypt哈希存储
- JWT认证，token设置合理过期时间
- 所有用户输入必须验证（Pydantic validator）
- SQL查询必须参数化，防止注入
- 敏感数据不在日志中出现
- 使用HTTPS传输

### 输入验证示例
```python
class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
```

---

## 九、数据库规范

### SQLAlchemy模型
- 必须包含 `created_at`、`updated_at` 时间戳
- 软删除使用 `deleted_at` 字段
- 为常用查询字段添加索引
- 实现领域模型转换方法 `to_domain()`

### 查询优化
- 使用 `joinedload`/`selectinload` 避免N+1问题
- 分页查询必须使用limit/offset
- 计数使用 `func.count()` 而非加载全部数据

---

## 十、测试规范

### 分层测试
- **单元测试**: 测试单个函数/类，使用Mock隔离依赖
- **集成测试**: 测试组件协作，使用测试数据库
- **覆盖率要求**: >80%

### 测试命名
```python
class TestUserService:
    def test_get_user_from_cache(self): ...
    def test_get_user_not_found(self): ...
```

---

## 十一、日志规范

- 使用结构化JSON格式日志
- 必须包含：timestamp、level、logger、message
- 按场景包含：request_id、user_id、exception
- 错误日志使用 `logger.exception()` 自动记录堆栈

---

## 十二、性能优化

### 必须遵守
- 避免循环中的数据库查询
- 热点数据使用缓存（Redis）
- 大数据量查询必须分页
- 使用连接池管理数据库连接

### 缓存策略
- 查询结果缓存需设置合理TTL
- 缓存键格式：`{prefix}:{resource}:{id}`

---

## 十三、代码审查检查清单

提交前必须检查：

**代码质量**
- [ ] 遵循PEP 8风格
- [ ] 使用类型注解
- [ ] 有文档字符串
- [ ] 无重复代码

**设计原则**
- [ ] 类遵循单一职责
- [ ] 函数不超过30行
- [ ] 使用依赖注入

**错误处理**
- [ ] 正确处理异常
- [ ] 记录错误日志
- [ ] 避免捕获宽泛异常

**安全性**
- [ ] 验证所有输入
- [ ] 敏感数据加密
- [ ] 参数化SQL查询

**性能**
- [ ] 无N+1查询
- [ ] 添加必要索引
- [ ] 使用缓存

**测试**
- [ ] 编写单元测试
- [ ] 测试边界条件
- [ ] 覆盖率达标

---

## 十四、版本控制规范

### 分支策略
- **main**: 生产代码
- **develop**: 开发集成
- **feature/xxx**: 新功能
- **bugfix/xxx**: Bug修复
- **hotfix/xxx**: 紧急修复

### Commit规范
```
<type>(<scope>): <subject>

类型：feat(新功能) | fix(修复) | docs(文档) | refactor(重构) | test(测试)
示例：feat(user): add password reset functionality
```

---

## 十五、工具配置

### 必用工具
- **black**: 代码格式化
- **ruff**: 代码检查
- **mypy**: 类型检查
- **pytest**: 单元测试

### 配置要点
- 行长度：100字符
- Python版本：3.9+
- 类型检查：严格模式