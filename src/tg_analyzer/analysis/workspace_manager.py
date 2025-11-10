"""
Analysis workspace management
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import shutil

from ..config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Manages analysis workspaces for chat files"""

    def __init__(self, config: ConfigManager):
        """
        Initialize workspace manager

        Args:
            config: Configuration manager
        """
        self.config = config
        self.analysis_dir = Path(config.get("data_dir", "data")) / "analysis"

    def create_workspace(self, cleaned_file_path: str) -> Dict[str, Any]:
        """
        Create a workspace for a cleaned chat file

        Args:
            cleaned_file_path: Path to the cleaned file

        Returns:
            Workspace information
        """
        file_path = Path(cleaned_file_path)

        # Parse filename to extract chat name and dates
        chat_name, dates = self._parse_filename(file_path.name)

        # Create workspace directory name
        workspace_name = f"{chat_name}_{dates}"
        workspace_path = self.analysis_dir / workspace_name

        # Create workspace directory
        workspace_path.mkdir(parents=True, exist_ok=True)
        results_dir = workspace_path / "results"
        results_dir.mkdir(exist_ok=True)

        # Copy source file to workspace
        source_file = workspace_path / "source.txt"
        if not source_file.exists():
            shutil.copy2(file_path, source_file)

        workspace_info = {
            "workspace_path": str(workspace_path),
            "results_dir": str(results_dir),
            "source_file": str(source_file),
            "chat_name": chat_name,
            "dates": dates,
            "workspace_name": workspace_name,
        }

        logger.info(f"Created workspace: {workspace_name}")
        return workspace_info

    def _parse_filename(self, filename: str) -> tuple[str, str]:
        """
        Parse filename to extract chat name and dates

        Args:
            filename: Original filename

        Returns:
            Tuple of (chat_name, dates)
        """
        # Remove file extension
        name = Path(filename).stem

        # Try to extract dates from filename
        # Look for patterns like: SLP_Havala_20220228-20251014
        date_pattern = r"(\d{8})-(\d{8})"
        date_match = re.search(date_pattern, name)

        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)
            dates = f"{start_date}-{end_date}"
            # Remove dates from name to get chat name
            chat_name = re.sub(date_pattern, "", name).strip("_-")
        else:
            # Look for single date pattern
            single_date_pattern = r"(\d{8})"
            single_match = re.search(single_date_pattern, name)
            if single_match:
                dates = single_match.group(1)
                chat_name = re.sub(single_date_pattern, "", name).strip("_-")
            else:
                # No dates found, use current date
                dates = datetime.now().strftime("%Y%m%d")
                chat_name = name

        # Clean up chat name
        chat_name = re.sub(r"[^\w\s-]", "", chat_name).strip()
        chat_name = re.sub(r"\s+", "_", chat_name)

        return chat_name, dates

    def save_result(
        self,
        workspace_info: Dict[str, Any],
        template_name: str,
        result: str,
        format_type: str = "markdown",
    ) -> str:
        """
        Save analysis result to workspace

        Args:
            workspace_info: Workspace information
            template_name: Name of the analysis template
            result: Analysis result content
            format_type: Output format (markdown, json, text)

        Returns:
            Path to saved result file
        """
        results_dir = Path(workspace_info["results_dir"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Determine file extension
        extensions = {"markdown": ".md", "json": ".json", "text": ".txt"}
        ext = extensions.get(format_type, ".md")

        # Create filename
        filename = f"{template_name}_{timestamp}{ext}"
        result_path = results_dir / filename

        # Save result
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result)

        logger.info(f"Saved result: {result_path}")
        return str(result_path)

    def list_workspaces(self) -> list[Dict[str, Any]]:
        """
        List all analysis workspaces

        Returns:
            List of workspace information
        """
        workspaces = []

        if not self.analysis_dir.exists():
            return workspaces

        for workspace_path in self.analysis_dir.iterdir():
            if workspace_path.is_dir():
                workspace_info = {
                    "workspace_path": str(workspace_path),
                    "workspace_name": workspace_path.name,
                    "results_dir": str(workspace_path / "results"),
                    "source_file": str(workspace_path / "source.txt"),
                    "created": datetime.fromtimestamp(workspace_path.stat().st_ctime),
                    "modified": datetime.fromtimestamp(workspace_path.stat().st_mtime),
                }

                # Count results
                results_dir = workspace_path / "results"
                if results_dir.exists():
                    workspace_info["result_count"] = len(list(results_dir.glob("*")))
                else:
                    workspace_info["result_count"] = 0

                workspaces.append(workspace_info)

        # Sort by modification time (newest first)
        workspaces.sort(key=lambda x: x["modified"], reverse=True)
        return workspaces

    def get_workspace(self, workspace_name: str) -> Optional[Dict[str, Any]]:
        """
        Get workspace information by name

        Args:
            workspace_name: Name of the workspace

        Returns:
            Workspace information or None if not found
        """
        workspace_path = self.analysis_dir / workspace_name

        if not workspace_path.exists():
            return None

        return {
            "workspace_path": str(workspace_path),
            "workspace_name": workspace_name,
            "results_dir": str(workspace_path / "results"),
            "source_file": str(workspace_path / "source.txt"),
            "created": datetime.fromtimestamp(workspace_path.stat().st_ctime),
            "modified": datetime.fromtimestamp(workspace_path.stat().st_mtime),
        }

    def cleanup_workspace(self, workspace_name: str) -> bool:
        """
        Clean up a workspace (remove it)

        Args:
            workspace_name: Name of the workspace to clean up

        Returns:
            True if successful, False otherwise
        """
        workspace_path = self.analysis_dir / workspace_name

        if not workspace_path.exists():
            return False

        try:
            shutil.rmtree(workspace_path)
            logger.info(f"Cleaned up workspace: {workspace_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clean up workspace {workspace_name}: {e}")
            return False
