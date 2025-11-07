"""
Analysis script runner
"""

import logging
import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, List
import traceback

from ..llm.llm_manager import LLMManager
from ..config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class ScriptRunner:
    """Runs analysis scripts with LLM injection"""

    def __init__(self, config: ConfigManager, llm_manager: LLMManager):
        """
        Initialize script runner

        Args:
            config: Configuration manager
            llm_manager: LLM manager instance
        """
        self.config = config
        self.llm_manager = llm_manager

    async def run_script(
        self, script_path: str, chat_data: str, template_name: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Run an analysis script

        Args:
            script_path: Path to the analysis script
            chat_data: Cleaned chat data
            template_name: Name of the template
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)

        Returns:
            Analysis result
        """
        try:
            # Load the script module
            script_module = self._load_script_module(script_path, template_name)

            # Get the analyze function
            if not hasattr(script_module, "analyze"):
                raise ValueError(f"Script {script_path} missing 'analyze' function")

            analyze_func = getattr(script_module, "analyze")

            # Run the analysis with parameters
            logger.info(f"Running analysis script: {template_name}")
            logger.debug(f"Script parameters: {kwargs}")
            result = await analyze_func(chat_data, self.llm_manager, **kwargs)

            # Validate result format
            if not isinstance(result, dict):
                raise ValueError("Analysis function must return a dictionary")

            required_keys = ["result", "format"]
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Analysis result missing required key: {key}")

            # Add metadata
            if "metadata" not in result:
                result["metadata"] = {}

            result["metadata"].update(
                {
                    "template": template_name,
                    "script_path": script_path,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

            logger.info(f"Analysis completed: {template_name}")
            return result

        except Exception as e:
            logger.error(f"Analysis script failed: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")

            return {
                "result": f"Analysis failed: {str(e)}",
                "format": "text",
                "metadata": {
                    "template": template_name,
                    "error": str(e),
                    "success": False,
                },
            }

    def _load_script_module(self, script_path: str, template_name: str):
        """
        Load a script module dynamically

        Args:
            script_path: Path to the script file
            template_name: Name of the template (used for module name)

        Returns:
            Loaded module
        """
        script_file = Path(script_path)

        if not script_file.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        # Create a unique module name
        module_name = f"analysis_script_{template_name}_{id(self)}"

        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load script: {script_path}")

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules temporarily
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
            return module
        finally:
            # Clean up
            if module_name in sys.modules:
                del sys.modules[module_name]

    async def run_multiple_scripts(
        self, scripts: List[Dict[str, Any]], chat_data: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Run multiple analysis scripts

        Args:
            scripts: List of script information
            chat_data: Cleaned chat data
            **kwargs: Additional parameters to pass to all scripts

        Returns:
            List of analysis results
        """
        results = []

        for script_info in scripts:
            template_name = script_info["name"]
            script_path = script_info["script_path"]

            logger.info(f"Running script: {template_name}")

            try:
                result = await self.run_script(
                    script_path, chat_data, template_name, **kwargs
                )
                results.append(
                    {
                        "template": template_name,
                        "result": result,
                        "success": result.get("metadata", {}).get("success", True),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to run script {template_name}: {e}")
                results.append(
                    {
                        "template": template_name,
                        "result": {
                            "result": f"Script execution failed: {str(e)}",
                            "format": "text",
                            "metadata": {"success": False, "error": str(e)},
                        },
                        "success": False,
                    }
                )

        return results

    def validate_script(self, script_path: str) -> List[str]:
        """
        Validate a script file

        Args:
            script_path: Path to the script file

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        script_file = Path(script_path)

        if not script_file.exists():
            errors.append(f"Script file not found: {script_path}")
            return errors

        try:
            with open(script_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for required function
            if "async def analyze(" not in content:
                errors.append("Script missing required 'async def analyze(' function")

            # Check for required parameters
            if "chat_data" not in content:
                errors.append("Script must accept 'chat_data' parameter")

            if "llm_manager" not in content:
                errors.append("Script must accept 'llm_manager' parameter")

            # Check for return statement
            if "return {" not in content and "return dict(" not in content:
                errors.append(
                    "Script must return a dictionary with 'result' and 'format' keys"
                )

        except Exception as e:
            errors.append(f"Failed to read script file: {e}")

        return errors
