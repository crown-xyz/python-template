# Crown API Python Client

Python template for interacting with the [Crown API](https://docs.brl.xyz).

## Prerequisites

- Python 3.10+
- A Crown API key and RSA keypair ([authentication guide](https://docs.brl.xyz/guides/authentication))

## Setup

1. **Clone the repository and enter the directory:**

```bash
cd python-template
```

2. **Create and activate a virtual environment:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -e .
```

4. **Configure environment variables:**

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
CROWN_API_KEY=your_api_key_here
CROWN_PRIVATE_KEY_PATH=./private_key.pem
CROWN_BASE_URL=https://app.brl.xyz
```

5. **Place your RSA private key** at the path configured in `CROWN_PRIVATE_KEY_PATH`.

## Usage

```bash
python main.py
```

`main.py` demonstrates calling the available API endpoints. Edit it to enable or adjust the examples as needed.

## Project Structure

```
├── .env.example        # Environment variable template
├── main.py             # Usage examples
├── pyproject.toml      # Project metadata and dependencies
└── crown/
    ├── __init__.py
    ├── auth.py         # JWT signing (RS256)
    └── client.py       # CrownClient with all API methods
```

## Available Methods

| Method | Description |
|--------|-------------|
| `get_balance(asset)` | Get account balance |
| `list_wallets()` | List wallets |
| `create_wallet(name)` | Create a new wallet |
| `create_quote(...)` | Create a conversion quote |
| `list_orders()` | List all orders |
| `get_order(id)` | Get a specific order |
| `create_order(...)` | Create an order from a quote |
| `list_transfers()` | List token transfers |
| `create_transfer(...)` | Transfer tokens between wallets |
| `list_deposits(asset)` | List deposits |
| `list_withdrawals(asset)` | List withdrawals |
| `get_withdrawal(id)` | Get a specific withdrawal |
| `create_withdrawal_pix(...)` | Withdraw BRL via PIX |
| `create_withdrawal_ted(...)` | Withdraw BRL via TED |
| `list_claims()` | List all claims |
| `simulate_claims()` | Get claimable operations |
| `create_claim(...)` | Execute claims |
