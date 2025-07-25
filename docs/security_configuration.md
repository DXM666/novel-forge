# NovelForge 安全配置指南

## 环境变量安全管理

### 🔒 基本原则

1. **永远不要将敏感信息提交到Git仓库**
2. **使用环境变量存储所有敏感配置**
3. **为不同环境使用不同的配置值**
4. **定期轮换API密钥和密码**

### 📁 文件结构

```
backend/
├── .env                 # 实际配置文件（不提交到Git）
├── .env.example         # 配置模板（可以提交到Git）
├── config.py           # 配置加载逻辑
└── utils/
    └── config_validator.py  # 配置验证
```

### 🛠️ 设置步骤

#### 1. 初始化配置文件

```bash
# 复制模板文件
cp backend/.env.example backend/.env

# 编辑配置文件，填入真实值
# 注意：.env 文件已在 .gitignore 中，不会被提交
```

#### 2. 填写必要的配置

在 `backend/.env` 文件中填入以下必要配置：

```bash
# AI服务配置
OPENAI_API_KEY=sk-your-real-openai-api-key-here
OPENAI_MODEL=gpt-4

# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/novelforge
DATABASE_PASSWORD=your_database_password

# Redis配置
REDIS_PASSWORD=your_redis_password

# 应用安全配置
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

#### 3. 验证配置

运行配置验证：

```bash
cd backend
python -c "from utils.config_validator import validate_all_config; validate_all_config()"
```

### 🔐 敏感信息类型

#### 高敏感度
- API密钥（OpenAI、Pinecone等）
- 数据库密码
- JWT密钥
- 加密密钥

#### 中敏感度
- 数据库连接字符串
- Redis连接信息
- 外部服务URL

#### 低敏感度
- 应用名称
- 日志级别
- 端口号

### 🚨 安全检查清单

#### 开发环境
- [ ] `.env` 文件已在 `.gitignore` 中
- [ ] 所有敏感信息都使用环境变量
- [ ] 配置模板文件 `.env.example` 不包含真实密钥
- [ ] 本地 `.env` 文件权限设置为 600

#### 生产环境
- [ ] 使用强密码和复杂密钥
- [ ] 定期轮换API密钥
- [ ] 使用专用的生产环境配置
- [ ] 启用HTTPS和其他安全措施

### 🔧 不同环境的配置管理

#### 开发环境 (.env.development)
```bash
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/novelforge_dev
```

#### 测试环境 (.env.test)
```bash
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/novelforge_test
```

#### 生产环境 (.env.production)
```bash
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod_user:strong_pass@prod_host:5432/novelforge_prod
```

### 🛡️ 额外安全措施

#### 1. 密钥管理
- 使用密钥管理服务（如AWS Secrets Manager、Azure Key Vault）
- 实施密钥轮换策略
- 监控密钥使用情况

#### 2. 访问控制
- 限制对配置文件的访问权限
- 使用最小权限原则
- 审计配置变更

#### 3. 监控和告警
- 监控异常的API调用
- 设置密钥泄露告警
- 记录配置访问日志

### 🚫 常见安全错误

#### ❌ 错误做法
```bash
# 直接在代码中硬编码密钥
OPENAI_API_KEY = "sk-1234567890abcdef"

# 将 .env 文件提交到Git
git add backend/.env

# 在日志中输出敏感信息
print(f"API Key: {api_key}")
```

#### ✅ 正确做法
```python
# 使用环境变量
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 验证密钥存在
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# 安全日志记录
logger.info(f"API Key loaded: {'*' * len(api_key)}")
```

### 📝 应急响应

#### 密钥泄露处理步骤
1. **立即撤销**泄露的密钥
2. **生成新密钥**并更新配置
3. **检查日志**确认是否有异常使用
4. **通知团队**并记录事件
5. **审查流程**防止再次发生

### 🔗 相关资源

- [OWASP Configuration Security](https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration)
- [12-Factor App Config](https://12factor.net/config)
- [Python-dotenv Documentation](https://python-dotenv.readthedocs.io/)

---

**记住：安全是一个持续的过程，不是一次性的任务！**
