from enum import Enum


class ObjectTypes(Enum):
    SEQUENCE_TYPES = (list, tuple, range)
    MAPPING_TYPES = (dict,)
    SET_TYPES = (set, frozenset)
    RECURSIVE_TYPES = SEQUENCE_TYPES + MAPPING_TYPES + SET_TYPES

    @staticmethod
    def is_mapping_type(obj) -> bool:
        return type(obj) in ObjectTypes.MAPPING_TYPES.value

    @staticmethod
    def is_sequence_type(obj) -> bool:
        return type(obj) in ObjectTypes.SEQUENCE_TYPES.value

    @staticmethod
    def is_recursive_type(obj) -> bool:
        return type(obj) in ObjectTypes.RECURSIVE_TYPES.value


def sort_key(item: tuple) -> tuple:
    (name, value) = item
    if name == "_links":
        return (1, "")
    elif not ObjectTypes.is_recursive_type(value):
        return (2, name)
    else:
        return (3, name)


def doc_sort(doc):
    if ObjectTypes.is_recursive_type(doc):
        for name, value in (
            doc.items() if ObjectTypes.is_mapping_type(doc) else enumerate(doc)
        ):
            if ObjectTypes.is_recursive_type(value):
                doc[name] = doc_sort(value)
    return (
        dict(sorted(doc.items(), key=sort_key))
        if ObjectTypes.is_mapping_type(doc)
        else doc
    )
