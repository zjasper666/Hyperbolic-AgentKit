from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager

REMOTE_SHELL_PROMPT = """
Execute shell commands on the remote server via SSH.

Input parameters:
- command: The shell command to execute on the remote server

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Use 'ssh_status' to check current connection status
- Commands are executed in the connected SSH session
- Returns command output as a string
"""

class RemoteShellInput(BaseModel):
    """Input argument schema for remote shell commands."""
    command: str = Field(..., description="The shell command to execute on the remote server")

def execute_remote_command(command: str) -> str:
    """
    Execute a command on the remote server.
    
    Args:
        command: The shell command to execute
    
    Returns:
        str: Command output or error message
    """
    # Special command to check SSH status
    if command.strip().lower() == 'ssh_status':
        return ssh_manager.get_connection_info()

    # Verify SSH is connected before executing
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."

    # Execute command remotely
    return ssh_manager.execute(command)

class RemoteShellAction(HyperbolicAction):
    """Remote shell command execution action."""
    
    name: str = "remote_shell"
    description: str = REMOTE_SHELL_PROMPT
    args_schema: type[BaseModel] = RemoteShellInput
    func: Callable[..., str] = execute_remote_command