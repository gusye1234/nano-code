"""
精简版UTF-8编码问题调试工具 - 只在有错误时输出
"""

def debug_utf8_error_simple(data, location="unknown"):
    """
    简单的UTF-8错误检查，只在发现错误时打印
    """
    if isinstance(data, str):
        _check_string_simple(data, location)
    elif isinstance(data, dict):
        _check_dict_simple(data, location)
    elif isinstance(data, list):
        _check_list_simple(data, location)


def clean_utf8_data(data):
    """
    清理数据中的UTF-8编码问题，移除代理字符和其他无效字符
    """
    if isinstance(data, str):
        return _clean_string(data)
    elif isinstance(data, dict):
        return {key: clean_utf8_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_utf8_data(item) for item in data]
    else:
        return data


def _clean_string(text):
    """
    清理字符串中的代理字符和其他UTF-8不兼容字符
    """
    if not isinstance(text, str):
        return text
    
    # 移除代理字符 (0xD800-0xDFFF)
    cleaned_chars = []
    for char in text:
        char_code = ord(char)
        if 0xD800 <= char_code <= 0xDFFF:
            # 跳过代理字符
            continue
        else:
            cleaned_chars.append(char)
    
    result = ''.join(cleaned_chars)
    
    # 验证结果可以正确编码为UTF-8
    try:
        result.encode('utf-8')
        return result
    except UnicodeEncodeError:
        # 如果仍有问题，使用错误处理策略
        return result.encode('utf-8', errors='ignore').decode('utf-8')


def _check_string_simple(text, location):
    """检查字符串，只在有错误时输出"""
    if not isinstance(text, str):
        return
    
    # 检查代理字符
    surrogates_found = []
    for i, char in enumerate(text):
        if 0xD800 <= ord(char) <= 0xDFFF:
            surrogates_found.append((i, char, ord(char), hex(ord(char))))
    
    if surrogates_found:
        print(f"\n🚨 [UTF8_ERROR] Found {len(surrogates_found)} surrogate character(s) in {location}")
        for pos, char, ord_val, hex_val in surrogates_found[:3]:  # 只显示前3个
            context_start = max(0, pos - 15)
            context_end = min(len(text), pos + 15)
            before = text[context_start:pos]
            after = text[pos+1:context_end]
            print(f"    Position {pos}: ord={ord_val}, hex={hex_val}")
            print(f"    Context: '{before}[{char}]{after}'")
        if len(surrogates_found) > 3:
            print(f"    ... and {len(surrogates_found) - 3} more")
    
    # 检查UTF-8编码错误
    try:
        text.encode('utf-8')
    except UnicodeEncodeError as e:
        print(f"\n🚨 [UTF8_ERROR] Encoding error in {location}")
        print(f"    Position: {e.start}-{e.end}")
        if hasattr(e, 'object') and e.object:
            error_char = e.object[e.start:e.end]
            print(f"    Error character(s): '{error_char}'")
            for i, char in enumerate(error_char):
                print(f"    Char {e.start + i}: ord={ord(char)}, hex={hex(ord(char))}")


def _check_dict_simple(data, location):
    """检查字典，只在有错误时输出"""
    for key, value in data.items():
        key_str = str(key)
        _check_string_simple(key_str, f"{location}.key[{key}]")
        
        if isinstance(value, str):
            _check_string_simple(value, f"{location}.{key}")
        elif isinstance(value, (dict, list)):
            debug_utf8_error_simple(value, f"{location}.{key}")


def _check_list_simple(data, location):
    """检查列表，只在有错误时输出"""
    for i, item in enumerate(data):
        debug_utf8_error_simple(item, f"{location}[{i}]")