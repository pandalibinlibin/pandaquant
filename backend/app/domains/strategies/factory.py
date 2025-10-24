import os
import importlib
import inspect
from typing import Dict, Type, List, Any
from .base_strategy import BaseStrategy
from .services import StrategyService


class StrategyFactory:

    def __init__(self, strategy_service: StrategyService):
        self.strategy_service = strategy_service
        self.strategy_dir = os.path.dirname(__file__)
        self.registered_strategies = {}

    def auto_discover_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        discovered_strategies = {}

        for filename in os.listdir(self.strategy_dir):
            if filename.endswith("_strategy.py") and filename != "__init__.py":
                module_name = filename[:-3]

                try:
                    module = importlib.import_module(
                        f".{module_name}", package=__package__
                    )

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, BaseStrategy)
                            and obj != BaseStrategy
                            and not name.startswith("_")
                        ):
                            strategy_name = name.lower().replace("strategy", "")
                            discovered_strategies[strategy_name] = obj
                            print(f"Discovered strategy: {strategy_name}")
                except Exception as e:
                    print(f"Error importing strategy module {module_name}: {e}")

        return discovered_strategies

    def register_discovered_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        discovered_strategies = self.auto_discover_strategies()
        for strategy_name, strategy_class in discovered_strategies.items():
            try:
                self.strategy_service.register_strategy_class(
                    strategy_name, strategy_class
                )
                self.registered_strategies[strategy_name] = strategy_class
                print(
                    f"Registered strategy: {strategy_name} -> {strategy_class.__name__}"
                )

            except Exception as e:
                print(f"Error registering strategy {strategy_name}: {e}")

        return self.registered_strategies

    def get_registered_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        return self.registered_strategies

    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        if strategy_name not in self.registered_strategies:
            raise ValueError(f"Strategy {strategy_name} not found")

        strategy_class = self.registered_strategies[strategy_name]
        return {
            "name": strategy_name,
            "class": strategy_class.__name__,
            "module": strategy_class.__module__,
            "doc": strategy_class.__doc__,
            "methods": [
                method for method in dir(strategy_class) if not method.startswith("_")
            ],
        }
