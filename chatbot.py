import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to PYTHONPATH so Python can find the hyperbolic packages
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import time
import threading
import signal
from datetime import datetime

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun

# Import CDP Agentkit Langchain Extension.
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from cdp_langchain.tools import CdpTool
from pydantic import BaseModel, Field
from cdp import Wallet

# Import Hyperbolic Agentkit Langchain Extension
from hyperbolic_langchain.agent_toolkits import HyperbolicToolkit
from hyperbolic_langchain.utils import HyperbolicAgentkitWrapper

from twitter_langchain import (TwitterApiWrapper, TwitterToolkit)
from hyperbolic_agentkit_core.actions.remote_shell import RemoteShellAction

# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"

DEPLOY_MULTITOKEN_PROMPT = """
This tool deploys a new multi-token contract with a specified base URI for token metadata.
The base URI should be a template URL containing {id} which will be replaced with the token ID.
For example: 'https://example.com/metadata/{id}.json'
"""


class DeployMultiTokenInput(BaseModel):
    """Input argument schema for deploy multi-token contract action."""
    base_uri: str = Field(
        ...,
        description=
        "The base URI template for token metadata. Must contain {id} placeholder.",
        example="https://example.com/metadata/{id}.json")


def deploy_multi_token(wallet: Wallet, base_uri: str) -> str:
    """Deploy a new multi-token contract with the specified base URI.

    Args:
        wallet (Wallet): The wallet to deploy the contract from.
        base_uri (str): The base URI template for token metadata. Must contain {id} placeholder.

    Returns:
        str: A message confirming deployment with the contract address.
    """
    # Validate that the base_uri contains the {id} placeholder
    if "{id}" not in base_uri:
        raise ValueError("base_uri must contain {id} placeholder")

    # Deploy the contract
    deployed_contract = wallet.deploy_multi_token(base_uri)
    result = deployed_contract.wait()

    return f"Successfully deployed multi-token contract at address: {result.contract_address}"


def initialize_agent():
    """Initialize the agent with CDP Agentkit and Hyperbolic Agentkit."""
    # Initialize LLM.
    llm = ChatOpenAI(model="gpt-4o")

    wallet_data = None

    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    # Configure CDP Agentkit Langchain Extension.
    values = {}
    if wallet_data is not None:
        # If there is a persisted agentic wallet, load it and pass to the CDP Agentkit Wrapper.
        values = {"cdp_wallet_data": wallet_data}

    agentkit = CdpAgentkitWrapper(**values)

    # persist the agent's CDP MPC Wallet Data.
    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    # Initialize CDP Agentkit Toolkit and get tools.
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()

    # Initialize Hyperbolic Agentkit Toolkit and get tools.
    hyperbolic_agentkit = HyperbolicAgentkitWrapper()
    hyperbolic_toolkit = HyperbolicToolkit.from_hyperbolic_agentkit_wrapper(hyperbolic_agentkit)
    tools.extend(hyperbolic_toolkit.get_tools())

    twitter_api_wrapper = TwitterApiWrapper()
    twitter_toolkit = TwitterToolkit.from_twitter_api_wrapper(
        twitter_api_wrapper)
    tools.extend(twitter_toolkit.get_tools())
    
    deployMultiTokenTool = CdpTool(
        name="deploy_multi_token",
        description=DEPLOY_MULTITOKEN_PROMPT,
        cdp_agentkit_wrapper=agentkit,
        args_schema=DeployMultiTokenInput,
        func=deploy_multi_token,
    )

    # Add additional tools
    tools.extend([
        deployMultiTokenTool,
        DuckDuckGoSearchRun(
            name="web_search",
            description="Search the internet for current information. Use this when you need to find up-to-date information or verify facts."
        )
    ])

    # Store buffered conversation history in memory.
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP and Hyperbolic Agentkit Chatbot Example!"}}

    # Create ReAct Agent using the LLM and all tools.
    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=
        """You are a helpful agent that can interact with multiple platforms and services:

        1. Blockchain Operations (via CDP):
        - Interact onchain via Coinbase Developer Platform
        - Deploy tokens and manage wallets
        - Request funds from faucet on network ID `base-sepolia`

        2. Compute Operations (via Hyperbolic):
        - Rent compute resources
        - Check GPU status and availability
        - Manage compute infrastructure
        - Connect to remote servers via SSH (use ssh_connect)
        - Execute commands on remote server (use remote_shell)

        3. System Operations:
        - Use 'ssh_status' to check current SSH connection
        - Search the internet for current information
        - Post updates on X (Twitter)

        If asked about something beyond your tools' capabilities, guide users to:
        - CDP: docs.cdp.coinbase.com
        - Hyperbolic: docs.hyperbolic.xyz

        Be concise and helpful. Only describe your tools when explicitly asked.""",
    ), config


class CommandTimeout(Exception):
    """Exception raised when a command execution times out."""
    pass

# ANSI color codes
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

# def print_user(text):
#     """Print user messages in blue."""
#     print(f"\n{Colors.BLUE}{Colors.BOLD}User: {Colors.ENDC}{text}")

def print_ai(text):
    """Print AI responses in green."""
    print(f"{Colors.GREEN}{text}{Colors.ENDC}")

def print_system(text):
    """Print system messages in yellow."""
    print(f"{Colors.YELLOW}{text}{Colors.ENDC}")

def print_error(text):
    """Print error messages in red."""
    print(f"{Colors.RED}{text}{Colors.ENDC}")

class ProgressIndicator:
    def __init__(self):
        self.animation = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"
        self.idx = 0
        self._stop_event = threading.Event()
        self._thread = None
        
    def _animate(self):
        """Animation loop running in separate thread."""
        while not self._stop_event.is_set():
            print(f"\r{Colors.YELLOW}Processing {self.animation[self.idx]}{Colors.ENDC}", end="", flush=True)
            self.idx = (self.idx + 1) % len(self.animation)
            time.sleep(0.2)  # Update every 0.2 seconds
            
    def start(self):
        """Start the progress animation in a separate thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate)
        self._thread.daemon = True
        self._thread.start()
        
    def stop(self):
        """Stop the progress animation."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
            print("\r" + " " * 50 + "\r", end="", flush=True)  # Clear the line

def run_with_progress(func, *args, **kwargs):
    """Run a function while showing a progress indicator."""
    progress = ProgressIndicator()
    
    try:
        progress.start()
        generator = func(*args, **kwargs)
        chunks = []
        
        for chunk in generator:
            progress.stop()
            
            if "agent" in chunk:
                print(f"\n{Colors.GREEN}{chunk['agent']['messages'][0].content}{Colors.ENDC}")
            elif "tools" in chunk:
                print(f"\n{Colors.YELLOW}{chunk['tools']['messages'][0].content}{Colors.ENDC}")
            print(f"\n{Colors.YELLOW}-------------------{Colors.ENDC}")
            
            chunks.append(chunk)
            progress.start()
        
        return chunks
    finally:
        progress.stop()


def run_chat_mode(agent_executor, config):
    """Run the agent interactively based on user input."""
    print_system("Starting chat mode... Type 'exit' to end.")
    print_system("Commands:")
    print_system("  exit     - Exit the chat")
    print_system("  status   - Check if agent is responsive")
    
    while True:
        try:
            # Simple input handling without readline
            prompt = f"{Colors.BLUE}{Colors.BOLD}User: {Colors.ENDC}"
            user_input = input(prompt)
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                break
            elif user_input.lower() == "status":
                print_system("Agent is responsive and ready for commands.")
                continue
            
            print_system(f"\nStarted at: {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                progress = ProgressIndicator()
                progress.start()
                
                for chunk in agent_executor.stream(
                    {"messages": [HumanMessage(content=user_input)]},
                    config
                ):
                    progress.stop()
                    if "agent" in chunk:
                        print(f"{Colors.GREEN}{chunk['agent']['messages'][0].content}{Colors.ENDC}")
                    elif "tools" in chunk:
                        print(f"{Colors.YELLOW}{chunk['tools']['messages'][0].content}{Colors.ENDC}")
                    progress.start()
                
                progress.stop()
                print_system(f"Completed at: {datetime.now().strftime('%H:%M:%S')}")
                
            except Exception as e:
                print_error(f"\nError: {str(e)}")
                print_system("The agent encountered an error but is still running.")
            
        except KeyboardInterrupt:
            print_system("\nOperation interrupted by user")
            choice = input(f"{Colors.YELLOW}Do you want to exit? (y/N): {Colors.ENDC}")
            if choice.lower() == 'y':
                print_system("Goodbye Agent!")
                sys.exit(0)
            print_system("Continuing...")
            continue


# Autonomous Mode
def run_autonomous_mode(agent_executor, config, interval=10):
    """Run the agent autonomously with specified intervals."""
    print("Starting autonomous mode...")
    while True:
        try:
            # Provide instructions autonomously
            thought = (
                "Be creative and do something interesting with either blockchain operations or compute resources. "
                "Choose an action or set of actions and execute it that highlights your abilities. "
            )

            # Run agent in autonomous mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=thought)]}, config):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

            # Wait before the next action
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Mode Selection
def choose_mode():
    """Choose whether to run in autonomous or chat mode based on user input."""
    while True:
        print("\nAvailable modes:")
        print("1. chat    - Interactive chat mode")
        print("2. auto    - Autonomous action mode")

        choice = input(
            "\nChoose a mode (enter number or name): ").lower().strip()
        if choice in ["1", "chat"]:
            return "chat"
        elif choice in ["2", "auto"]:
            return "auto"
        print("Invalid choice. Please try again.")


def main():
    """Start the chatbot agent."""
    agent_executor, config = initialize_agent()

    mode = choose_mode()
    if mode == "chat":
        run_chat_mode(agent_executor=agent_executor, config=config)
    elif mode == "auto":
        run_autonomous_mode(agent_executor=agent_executor, config=config)


if __name__ == "__main__":
    print("Starting Agent...")
    main()
