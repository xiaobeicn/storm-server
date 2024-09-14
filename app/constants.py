# 数据状态
class ArticleStatus:
    DEFAULT = 0
    VALID = 1
    DELETED = 2


# 阶段状态
class ArticleState:
    INIT = "initiated"
    DONE = "completed"


# 模型
class LLMModel:
    GPT_4O = "gpt-4o-2024-08-06"
    GPT_4O_MINI = "gpt-4o-mini-2024-07-18"
    RM = "SerperRM"


# 审查
class ReviewStatus:
    ALLOWED = "0"
    POINTLESS = "1"
    SENSITIVE = "2"


# tokens
class Tokens:
    THRESHOLD = 200000
