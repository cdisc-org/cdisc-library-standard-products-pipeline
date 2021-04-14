from utilities import logger
import html
import re

class Transformer:

    def __init__(self, config = None):
        self.config = config
    
    def format_name_for_link(self, name: str, chars_to_remove = None) -> str:
        formatted_name = name
        characters_to_remove = chars_to_remove or [" ", "-", ",","\n", "\\n", '"']
        characters_to_replace = {
            "*": "s"
        }
        for char in characters_to_remove:
            formatted_name = self.remove_str(formatted_name, char)
        for k, v in characters_to_replace.items():
            formatted_name = self.replace_str(formatted_name, k, v)
        return formatted_name
    
    def remove_str(self, string: str, existing: str, count = None) -> str:
        if count:
            new_string = string.replace(existing, "", count)
        else:
            new_string = string.replace(existing, "")

        if new_string != string:
            logger.debug(f"TRANSFORMATION: Removed {existing} from string converting {string} to {new_string}")
        return new_string
    
    def replace_str(self, string: str, existing: str, replacement: str, count = None) -> str:
        if count:
            new_string = string.replace(existing, replacement, count)
        else:
            new_string = string.replace(existing, replacement)
    
        if new_string != string:
            logger.debug(f"TRANSFORMATION: Replacing {existing} with {replacement} applied converting {string} to {new_string}")
        return new_string

    def cleanup_html_encoding(self, string: str) -> str:
        if string == None:
            return None
        html_entity_regex = "&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});"
        utf_to_ascii_mapping = {
            "\u2013": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201d": '"',
            "\u2011": "-",
            "\u2012": "-",
            "\u2014": "-",
            "\u2026": "...",
            "\u00a0": " "
        }
        for key in utf_to_ascii_mapping:
            if key in string:
                string = string.replace(key, utf_to_ascii_mapping.get(key))
        html_entities = re.findall(html_entity_regex, string)
        text = string
        for entity in html_entities:
            utf_string = html.entities.html5.get(f"{entity};")
            replacement = utf_to_ascii_mapping.get(utf_string, utf_string)
            if replacement:
                text = self.replace_str(text, f"&{entity};", replacement)
            else:
                logger.error(f"FAILED HTML transformation for string: {entity} found in {string}")
        return text
