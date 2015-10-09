"""
Developed by Craig J Williams
"""
from .managers import default_relational_manager

manager = default_relational_manager
register = default_relational_manager.register
get_registered_models = default_relational_manager.get_registered_models

