from typing import Any


def python_obj_to_json_schema_type(obj: Any) -> set[str]:
    if obj is None:
        return {"null"}

    obj_type = type(obj)
    if obj_type == int:
        return {"integer", "number"}
    elif obj_type == float:
        return {"number"}
    elif obj_type == str:
        return {"string"}
    elif obj_type == bool:
        return {"boolean"}
    elif obj_type == list:
        return {"array"}
    elif obj_type == dict:
        return {"object"}
    else:
        return {"unknown"}


class SchemaValidator:
    """
    Simple utility to validate objects against JSON Schemas
    """

    @staticmethod
    def validate(schema: dict, data) -> tuple[bool, str]:
        """
        Validates data against a JSON schema

        Args:
            schema: JSON Schema to validate against
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        # This is a simplified implementation
        # In a real application, you would use a library like jsonschema for proper validation

        # Check for required fields
        if "required" in schema and isinstance(schema["required"], list):
            required = schema["required"]

            if not isinstance(data, dict):
                return False, "Data must be a dictionary for required field validation"

            for field in required:
                if field not in data:
                    return False, f"Missing required field: {field}"

        # Check property types if properties are defined
        if "properties" in schema and isinstance(schema["properties"], dict):
            properties = schema["properties"]

            if not isinstance(data, dict):
                return False, "Argument must be a dictionary for property validation"

            for key, prop in properties.items():
                if key in data and "type" in prop:
                    expected_type = prop["type"]
                    value = data[key]

                    # Determine actual type
                    actual_types = python_obj_to_json_schema_type(value)

                    if expected_type not in actual_types:
                        return (
                            False,
                            f'Type mismatch for property "{key}": expected {expected_type}, got {", ".join(actual_types)}',
                        )

        return True, "Validation successful"
