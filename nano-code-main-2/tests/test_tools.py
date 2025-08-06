from nano_code.agent_tool.tool_schema import SchemaValidator


def test_schema_validator():
    schema = {
        "properties": {
            "absolute_path": {
                "description": "The absolute path to the file to read (e.g., '/home/user/project/file.txt'). Relative paths are not supported. You must provide an absolute path.",
                "type": "string",
                "pattern": "^/",
            },
            "offset": {
                "description": "Optional: For text files, the 0-based line number to start reading from. Requires 'limit' to be set. Use for paginating through large files.",
                "type": "number",
            },
            "limit": {
                "description": "Optional: For text files, maximum number of lines to read. Use with 'offset' to paginate through large files. If omitted, reads the entire file (if feasible, up to a default limit).",
                "type": "number",
            },
        },
        "required": ["absolute_path"],
        "type": "object",
    }

    r = SchemaValidator.validate(
        schema, {"absolute_path": "/home/user/project/file.txt"}
    )
    assert r[0]

    r = SchemaValidator.validate(
        schema, {"absolute_path": "/home/user/project/file.txt", "offset": "10"}
    )
    assert not r[0]
