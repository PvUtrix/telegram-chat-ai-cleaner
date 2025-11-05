"""
Analysis template management
"""

import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import importlib.util
import sys

from ..config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages analysis templates"""

    def __init__(self, config: ConfigManager):
        """
        Initialize template manager

        Args:
            config: Configuration manager
        """
        self.config = config
        self.templates_dir = Path('analysis_templates')
        self.templates_dir.mkdir(exist_ok=True)

    def discover_templates(self) -> List[Dict[str, Any]]:
        """
        Discover all available analysis templates

        Returns:
            List of template information
        """
        templates = []
        
        if not self.templates_dir.exists():
            return templates
        
        for template_dir in self.templates_dir.iterdir():
            if not template_dir.is_dir():
                continue
            
            template_info = self._load_template_info(template_dir)
            if template_info:
                templates.append(template_info)
        
        # Sort by name
        templates.sort(key=lambda x: x['name'])
        return templates

    def _load_template_info(self, template_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Load template information from directory

        Args:
            template_dir: Template directory path

        Returns:
            Template information or None if invalid
        """
        script_file = template_dir / 'script.py'
        config_file = template_dir / 'config.yaml'
        
        if not script_file.exists():
            logger.warning(f"Template {template_dir.name} missing script.py")
            return None
        
        # Load template metadata
        template_info = {
            'name': template_dir.name,
            'script_path': str(script_file),
            'template_dir': str(template_dir),
            'description': f"Analysis template: {template_dir.name}",
            'version': '1.0.0',
            'author': 'Unknown',
            'tags': []
        }
        
        # Load config file if exists
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    template_info.update(config_data)
                    
                    # Extract LLM config if present
                    if 'llm_config' in config_data:
                        template_info['llm_defaults'] = config_data['llm_config']
            except Exception as e:
                logger.warning(f"Failed to load config for {template_dir.name}: {e}")
        
        # Extract description from script docstring
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for docstring at the top
            if '"""' in content:
                start = content.find('"""') + 3
                end = content.find('"""', start)
                if end > start:
                    docstring = content[start:end].strip()
                    # Extract description from docstring
                    lines = docstring.split('\n')
                    for line in lines:
                        if line.strip() and not line.strip().startswith('Template:'):
                            template_info['description'] = line.strip()
                            break
        except Exception as e:
            logger.warning(f"Failed to extract description from {template_dir.name}: {e}")
        
        return template_info

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific template information

        Args:
            template_name: Name of the template

        Returns:
            Template information or None if not found
        """
        template_dir = self.templates_dir / template_name
        return self._load_template_info(template_dir)

    def get_template_defaults(self, template_name: str) -> Dict[str, Any]:
        """
        Get LLM defaults for a specific template

        Args:
            template_name: Name of the template

        Returns:
            Dictionary of LLM parameter defaults
        """
        template = self.get_template(template_name)
        if not template:
            return {}
        
        return template.get('llm_defaults', {})

    def merge_template_defaults(self, template_name: str, user_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge template defaults with user parameters
        
        Args:
            template_name: Name of the template
            user_params: User-specified parameters
            
        Returns:
            Merged parameters with template defaults as fallback
        """
        template_defaults = self.get_template_defaults(template_name)
        
        # Start with template defaults
        merged_params = template_defaults.copy()
        
        # Override with user parameters
        merged_params.update(user_params)
        
        return merged_params

    def validate_template(self, template_name: str) -> List[str]:
        """
        Validate a template structure

        Args:
            template_name: Name of the template to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        template_dir = self.templates_dir / template_name
        
        if not template_dir.exists():
            errors.append(f"Template directory not found: {template_dir}")
            return errors
        
        script_file = template_dir / 'script.py'
        if not script_file.exists():
            errors.append(f"Script file not found: {script_file}")
        else:
            # Check if script has required analyze function
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'async def analyze(' not in content:
                    errors.append("Script missing required 'analyze' function")
                
                if 'llm_manager' not in content:
                    errors.append("Script must use 'llm_manager' parameter")
                    
            except Exception as e:
                errors.append(f"Failed to read script file: {e}")
        
        return errors

    def create_template(self, template_name: str, description: str = None) -> bool:
        """
        Create a new template structure

        Args:
            template_name: Name of the new template
            description: Template description

        Returns:
            True if successful, False otherwise
        """
        template_dir = self.templates_dir / template_name
        
        if template_dir.exists():
            logger.error(f"Template {template_name} already exists")
            return False
        
        try:
            # Create template directory
            template_dir.mkdir(parents=True)
            
            # Create script.py with template
            script_content = f'''"""
Template: {template_name}
Description: {description or f"Analysis template: {template_name}"}

NOTE: This is a placeholder template. You need to customize the analyze function
with your specific analysis logic and prompts before using it.
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Analyze chat data using LLM
    
    NOTE: This is a placeholder implementation. You should customize:
    - The analysis prompt to match your specific analysis goals
    - The model and parameters for optimal results
    - The metadata returned for better tracking
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options (model, temperature, max_tokens, etc.)
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # TODO: Customize these parameters for your analysis
    model = kwargs.get('model', 'openai/gpt-4')
    temperature = kwargs.get('temperature', 0.7)
    max_tokens = kwargs.get('max_tokens', 4000)
    provider = kwargs.get('provider', 'openrouter')
    
    # TODO: Customize this prompt for your specific analysis needs
    prompt = """Please analyze this Telegram chat and provide insights about:
    
1. Main topics discussed
2. Key participants and their roles  
3. Overall sentiment and tone
4. Any notable patterns or trends
5. Important links or resources shared

NOTE: This is a placeholder prompt. Customize it based on your analysis goals.

Chat data:
{{chat_data}}"""

    result = await llm_manager.generate(
        input_data=chat_data,
        prompt=prompt.format(chat_data=chat_data),
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return {{
        'result': result,
        'format': 'markdown',
        'metadata': {{
            'template': '{template_name}',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        }}
    }}
'''
            
            script_file = template_dir / 'script.py'
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Create config.yaml
            config_content = f'''name: {template_name}
description: {description or f"Analysis template: {template_name}"}
version: "1.0.0"
author: "User"
tags: []
'''
            
            config_file = template_dir / 'config.yaml'
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logger.info(f"Created template: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template {template_name}: {e}")
            return False

    def delete_template(self, template_name: str) -> bool:
        """
        Delete a template

        Args:
            template_name: Name of the template to delete

        Returns:
            True if successful, False otherwise
        """
        template_dir = self.templates_dir / template_name
        
        if not template_dir.exists():
            logger.error(f"Template {template_name} not found")
            return False
        
        try:
            import shutil
            shutil.rmtree(template_dir)
            logger.info(f"Deleted template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete template {template_name}: {e}")
            return False
