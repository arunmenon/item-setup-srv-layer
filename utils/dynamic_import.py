import importlib

def dynamic_import(class_path: str):
    """
    Dynamically import a class from a string path "module.submodule.ClassName".
    """
    parts = class_path.split('.')
    module_path = '.'.join(parts[:-1])
    class_name = parts[-1]
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls
