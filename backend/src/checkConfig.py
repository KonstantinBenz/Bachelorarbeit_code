from typing import Any
# Import logging
from src.loggingConfig import logger

def toBool(val: str) -> bool:
    """
    Converts a string to a boolean. Supports "true" and "false" (case-insensitive).
    
    :param val: The string value to be converted to bool.
    :return: The converted boolean value.
    :raises ValueError: If the value cannot be converted to a boolean.
    """
    try:
        if isinstance(val, str) and val.lower() == "true":
            logger.info(f"Converting {val} to True.")
            return True
        elif isinstance(val, str) and val.lower() == "false":
            logger.info(f"Converting {val} to False.")
            return False
        else:
            logger.warning(f"Unexpected value for boolean conversion: {val}")
            raise ValueError(f"Cannot convert {val} to bool.")
    except Exception as e:
        logger.error(f"Error converting {val} to bool: {e}")
        raise ValueError(f"Cannot convert {val} to bool: {e}")

def toInt(val: str) -> int:
    """
    Converts a string to an integer.
    
    :param val: The string value to be converted to an integer.
    :return: The converted integer value.
    :raises ValueError: If the value cannot be converted to an integer.
    """
    try:
        result = int(val)
        logger.info(f"Converting {val} to {result}.")
        return result
    except ValueError as e:
        logger.error(f"Error converting {val} to int: {e}")
        raise ValueError(f"Cannot convert {val} to int: {e}")

def toString(val: Any) -> str:
    """
    Converts any value to a string.
    
    :param val: The value to be converted to a string.
    :return: The converted string.
    :raises ValueError: If the value cannot be converted to a string.
    """
    try:
        result = str(val)
        logger.info(f"Converting {val} to {result}.")
        return result
    except Exception as e:
        logger.error(f"Error converting {val} to string: {e}")
        raise ValueError(f"Cannot convert {val} to string: {e}")
