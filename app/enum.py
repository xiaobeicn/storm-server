# 数据状态
class EnumArticleStatus:
    DEFAULT = 0
    VALID = 1
    DELETED = 2


# 阶段状态
class EnumArticleState:
    INIT = "initiated"
    DONE = "completed"


# 模型
class EnumLLMModel:
    GPT_4O = "gpt-4o-2024-08-06"
    GPT_4O_MINI = "gpt-4o-mini-2024-07-18"
    RM = "SerperRM"


# 审查
class EnumReviewStatus:
    ALLOWED = "0"
    POINTLESS = "1"
    SENSITIVE = "2"


# tokens
class EnumTokens:
    THRESHOLD_MIN = 200000
