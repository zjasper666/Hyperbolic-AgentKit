import os
import time
from collections.abc import Callable

from pydantic import BaseModel

from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.remote_shell import execute_remote_command


SPIN_UP_SNAP_NODE_PROMPT = """
This tool will spin up a snapnode on the ethereum mainnet on Hyperbolic GPU service.

Important notes:
- A GPU will need to be rented through Hyperbolic platform.
- A SSH Connection must be connected before running any node. Help the user SSH connect to the GPU they just rented.
- Provide feedback or errors encountered during each step.
"""


class SpinUpSnapNodeInput(BaseModel):
    """Input argument schema for spinning up snap node."""


def _update_system_install_utilities():
    try:
        print(
            "\nUpdating the system and installing necessary utilities. This step will take some time for the first time running."
        )
        commands = [
            "sudo apt update && sudo apt upgrade -y",
            "sudo apt install -y curl wget openssl software-properties-common",
        ]
        for each in commands:
            execute_remote_command(each)
        print("\nSystem updated and installation completed!")
    except Exception as e:
        return f"Error during system update and utilities installations: {e.output}"


def _install_geth_and_lighthouse():
    try:
        print(
            "\nWe need two clients for spinning up the snap node. Installing Geth and Lighthouse for this."
        )
        commands = [
            "sudo add-apt-repository -y ppa:ethereum/ethereum",
            "sudo apt update",
            "sudo apt install -y ethereum",
            "curl -LO https://github.com/sigp/lighthouse/releases/download/v4.0.1/lighthouse-v4.0.1-x86_64-unknown-linux-gnu.tar.gz",
            "tar -xvf lighthouse-v4.0.1-x86_64-unknown-linux-gnu.tar.gz",
            "sudo cp lighthouse /usr/bin",
        ]
        for each in commands:
            execute_remote_command(each)
        print("\nGeth and Lighthouse installation completed!")
    except Exception as e:
        return f"Error during Geth and Lighthouse installations: {e.output}"


def _generate_jwt_secret() -> str:
    try:
        print("\nGenerating JWT secret.")
        secrets_dir = "./.secrets"
        jwt_path = os.path.join(secrets_dir, "jwt.hex")
        commands = [
            f"mkdir -p {secrets_dir}",
            f"openssl rand -hex 32 | tr -d '\\n' | sudo tee {jwt_path}",
        ]
        for each in commands:
            execute_remote_command(each)
        print("\nJWT secret generated!")
        return jwt_path
    except Exception as e:
        return f"Error during Geth and Lighthouse installations: {e.output}"


def _start_geth(jwt_path: str) -> str:
    try:
        print("\nStaring Geth.")
        data_dir = os.path.expanduser("./.ethereum")
        log_file = os.path.expanduser("./.ethereum/geth.log")
        commands = [f"mkdir -p {data_dir}", f"touch {log_file}"]
        for each in commands:
            execute_remote_command(each)
        geth_command = [
            "nohup",
            "geth",
            "--mainnet",
            "--syncmode",
            "snap",
            "--datadir",
            data_dir,
            "--http",
            "--authrpc.addr",
            "localhost",
            "--authrpc.vhosts",
            "localhost",
            "--authrpc.port",
            "8551",
            "--authrpc.jwtsecret",
            jwt_path,
            f"> {log_file}",
            "2>&1 &",
        ]
        execute_remote_command(" ".join(geth_command))
        print("\nGeth is running!")
        return data_dir
    except Exception as e:
        return f"Error during execution layer Geth starting : {e.output}"


def _start_lighthouse(jwt_path: str, data_dir: str):
    try:
        print("\nStaring Lighthouse.")
        log_file = os.path.expanduser("./.ethereum/lighthouse.log")
        execute_remote_command(f"touch {log_file}")

        lighthouse_command = [
            "nohup",
            "lighthouse",
            "beacon_node",
            "--network",
            "mainnet",
            "--http",
            "--execution-endpoint",
            "http://localhost:8551",
            "--datadir",
            data_dir,
            "--execution-jwt",
            jwt_path,
            f"> {log_file}",
            "2>&1 &",
        ]
        execute_remote_command(" ".join(lighthouse_command))
        time.sleep(5)  # give it some time before the validation check
        print("\nLighthouse is running!")
    except Exception as e:
        return f"Error during consensus layer Lighthouse starting : {e.output}"


def _start_snap_node(jwt_path: str):
    data_dir = _start_geth(jwt_path)
    _start_lighthouse(jwt_path, data_dir)


def _validate_geth():
    try:
        print("\nValidating Geth connection.")
        curl_command = (
            "curl -X POST "
            '-H "Content-Type: application/json" '
            '--data \'{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":1}\' '
            "http://localhost:8545"
        )
        response = execute_remote_command(curl_command)
        if response.startswith("Error:"):
            _, *output_lines = response.split("\nOutput:", maxsplit=1)
            if output_lines:
                print("\nGeth is running and responding properly:", output_lines[0])
        else:
            print("\nGeth is running and responding properly:", response)
    except Exception as e:
        print(f"Unexpected error during Geth validation: {e}")


def _validate_lighthouse():
    try:
        print("\nValidating Lighthouse connection.")
        curl_command = ["curl", "-X", "GET", "http://localhost:5052/eth/v1/node/health"]
        response = execute_remote_command(" ".join(curl_command))
        if response.startswith("Error:"):
            _, *output_lines = response.split("\nOutput:", maxsplit=1)
            if output_lines:
                print(
                    "\nLighthouse is running and responding properly:", output_lines[0]
                )
        else:
            print("\nLighthouse is running and responding properly:", response)
    except Exception as e:
        print(f"Unexpected error during Lighthouse validation: {e}")


def _validate_connection():
    _validate_geth()
    _validate_lighthouse()


def spin_up_snap_nodes():
    # Updating the system and installing necessary utilities
    _update_system_install_utilities()

    # Installing Geth and Lighthouse
    _install_geth_and_lighthouse()

    # Generating JWT secret
    jwt_path = _generate_jwt_secret()

    # Starting Geth and Lighthouse and Verifying the setup
    _start_snap_node(jwt_path)

    # validate the connection
    _validate_connection()


class SpinUpSnapNodeAction(HyperbolicAction):
    """Spin up snap node."""

    name: str = "spin_up_snap_node"
    description: str = SPIN_UP_SNAP_NODE_PROMPT
    args_schema: type[BaseModel] | None = SpinUpSnapNodeInput
    func: Callable[..., str] = spin_up_snap_nodes
