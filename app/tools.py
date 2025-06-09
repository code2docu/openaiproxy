def make_md():
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_markdown",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                        },
                        "content": {
                            "type": "string",
                        }
                    },
                    "required": ["title", "content"]
                }
            }
        }
    ]


def make_uml():
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_uml",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {
                            "type": "string",
                        }
                    },
                    "required": ["title", "content"]
                }
            }
        }
    ]


