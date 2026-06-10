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

### Partner accounts

`test-partner.py` demonstrates the v1 partner account API (sub-account management and account-scoped operations):

```bash
# Create two sub-accounts (with declared external wallets) and Crown wallets
python test-partner.py -c

# Run quote/order flows against existing sub-accounts
python test-partner.py -e SUB_ACCOUNT_ID [SUB_ACCOUNT_ID_2]

# Auto mint: BRL -> BRLV order funded by a dynamic PIX brcode
python test-partner.py -m SUB_ACCOUNT_ID
```

### Examples

Standalone, single-purpose scripts live in `examples/`. They take every
input from environment variables — tax ids, wallets and account ids are
sensitive, so there are no in-code defaults:

```bash
# Create one sub-account (SUB_TAX_ID, SUB_TAX_DOCUMENT_TYPE, ...)
python examples/create_subaccount.py

# Mint BRLV funded by a dynamic PIX brcode (SUB_ACCOUNT_ID, TARGET_BRLV_WALLET, MINT_AMOUNT)
python examples/mint_via_qrcode.py
```

See `.env.example` for the full variable list per script.

## Project Structure

```
├── .env.example        # Environment variable template
├── main.py             # Usage examples
├── test-partner.py     # Partner account (v1) examples
├── pyproject.toml      # Project metadata and dependencies
└── crown/
    ├── __init__.py
    ├── auth.py         # JWT signing (RS256)
    └── client.py       # CrownClient and AccountClient with all API methods
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
| `list_sub_accounts()` | List the partner's sub-accounts |
| `create_sub_account(...)` | Request creation of a sub-account |
| `get_account(id)` | Get an account by id |
| `account(id)` | Get an `AccountClient` scoped to one account |

`AccountClient` (from `client.account(account_id)`) exposes the account-scoped v1 endpoints: `get()`, `get_balance(asset)`, `list_deposits(asset)`, `get_pix_deposit()`, `list_wallets()`, `create_wallet(name, chain)`, `create_quote(...)`, `list_orders()`, `get_order(id)`, `create_order(...)`, `list_transfers()`, `create_transfer(...)`, `list_withdrawals()`, and `get_withdrawal(id)`.
