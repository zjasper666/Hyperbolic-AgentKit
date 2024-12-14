# CDP and Hyperbolic Agentkit x X (Twitter) Chatbot

A template for running an AI agent with both blockchain and compute capabilities, plus X posting using:
- [Coinbase Developer Platform (CDP) Agentkit](https://github.com/coinbase/cdp-agentkit/)
- Hyperbolic Compute Platform

This template demonstrates a terminal-based chatbot that can:

Blockchain Operations (via CDP):
- Deploy tokens (ERC-20 & NFTs)
- Manage wallets
- Execute transactions
- Interact with smart contracts
- Post on X

Compute Operations (via Hyperbolic):
- Rent GPU compute resources
- Check GPU availability
- Monitor GPU status

## Prerequisites

1. **Python Version**
   - This project requires Python 3.12
   - If using Poetry, you can ensure the correct version with:
   ```bash
   poetry env use python3.12
   poetry install
   ```

2. **API Keys**
   - OpenAI API key from the [OpenAI Portal](https://platform.openai.com/api-keys)
   - CDP API credentials from [CDP Portal](https://portal.cdp.coinbase.com/access/api)
   - X Social API (Account Key and secret, Access Key and Secret)
   - Hyperbolic API Key from [Hyperbolic Portal](https://app.hyperbolic.xyz/settings)

## Quick Start

1. **Set Up Environment Variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```
   Then edit `.env` file and add your API keys:
   ```bash
   # OpenAI
   OPENAI_API_KEY=your-openai-key
   
   # CDP
   CDP_API_KEY_NAME=your-cdp-key-name
   CDP_API_KEY_PRIVATE_KEY=your-cdp-private-key
   
   # Hyperbolic
   HYPERBOLIC_API_KEY=your-hyperbolic-key
   
   # Twitter/X
   TWITTER_API_KEY=your-twitter-api-key
   TWITTER_API_SECRET=your-twitter-api-secret
   TWITTER_ACCESS_TOKEN=your-twitter-access-token
   TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Run the Bot**
   ```bash
   poetry run python chatbot.py
   ```
   - Choose between chat mode or autonomous mode
   - Start interacting with blockchain and compute resources!

## Features
- Interactive chat mode for guided interactions
- Autonomous mode for self-directed operations
- Full CDP Agentkit integration for blockchain operations
- Hyperbolic integration for compute operations
- Persistent wallet management
- X (Twitter) integration

## Source
The CDP functionality is based on the CDP Agentkit examples. For more information, visit:
https://github.com/coinbase/cdp-agentkit