import zlib

def encode6bit(b):
    """Кодирует 6-битное число в специальный символ PlantUML."""
    if b < 10:
        return chr(ord('0') + b)
    b -= 10
    if b < 26:
        return chr(ord('A') + b)
    b -= 26
    if b < 26:
        return chr(ord('a') + b)
    b -= 26
    if b == 0:
        return '-'
    if b == 1:
        return '_'
    return '?'

def plantuml_encode(plantuml_text):
    """
    Кодирует текст диаграммы PlantUML в специальный формат для URL.
    """
    # 1. Кодируем текст в UTF-8
    utf8_text = plantuml_text.encode('utf-8')

    # 2. Сжимаем с помощью DEFLATE без заголовков (wbits=-15)
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    compressed = compressor.compress(utf8_text) + compressor.flush()

    # 3. Кодируем сжатые данные
    encoded_chars = []
    for i in range(0, len(compressed), 3):
        chunk = compressed[i:i+3]

        b1 = chunk[0]
        b2 = chunk[1] if len(chunk) > 1 else 0
        b3 = chunk[2] if len(chunk) > 2 else 0

        # Преобразуем 3 байта (24 бита) в 4 6-битных числа
        c1 = b1 >> 2
        c2 = ((b1 & 3) << 4) | (b2 >> 4)
        c3 = ((b2 & 15) << 2) | (b3 >> 6)
        c4 = b3 & 63

        encoded_chars.append(encode6bit(c1))
        encoded_chars.append(encode6bit(c2))
        if len(chunk) > 1:
            encoded_chars.append(encode6bit(c3))
        if len(chunk) > 2:
            encoded_chars.append(encode6bit(c4))

    return "".join(encoded_chars)

def generate_plantuml_url(plantuml_code, server_url="https://plantuml.online/uml/"):
    """
    Генерирует полную ссылку на визуализацию PlantUML-диаграммы.
    """
    encoded_code = plantuml_encode(plantuml_code)
    return f"{server_url}{encoded_code}"

