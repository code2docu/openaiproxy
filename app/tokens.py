import tiktoken

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    return len(tokens)