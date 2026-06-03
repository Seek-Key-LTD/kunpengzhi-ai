MODEL_HANDLERS = {    "byteseed": {        "endpoint": "https://api.volcengine.com/openai/v1/chat/completions",        "auth_header": lambda key: {"Authorization": f"Bearer {key}"},    },}
