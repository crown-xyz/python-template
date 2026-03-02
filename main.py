"""Crown API usage examples.

Setup:
    1. Copy .env.example to .env and fill in your credentials
    2. Place your private key PEM file at the configured path
    3. pip install -e .
    4. python main.py
"""

import os

from dotenv import load_dotenv

from crown import CrownClient

load_dotenv()

client = CrownClient(
    api_key=os.environ["CROWN_API_KEY"],
    private_key_path=os.environ["CROWN_PRIVATE_KEY_PATH"],
    base_url=os.environ.get("CROWN_BASE_URL", "https://api.brl.xyz"),
)


# --- Balance ---
balance = client.get_balance("brl")
print("Balance:", balance)

# --- Wallets ---
wallets = client.list_wallets()
print("Wallets:", wallets)

# --- Orders ---
orders = client.list_orders()
print("Orders:", orders)

# --- Create a quote (BRL -> BRLV) ---
quote = client.create_quote(
    source_asset="fiat/brl",
    target_asset="eth-base/brlv",
    source_amount="100",
)
print("Quote:", quote)

# --- Create an order from a quote ---
# order = client.create_order(
#     quote_id=quote["id"],
#     target_wallet_address="0xYourWalletAddress",
# )
# print("Order:", order)

# --- Transfers ---
transfers = client.list_transfers()
print("Transfers:", transfers)

# --- Deposits ---
deposits = client.list_deposits("brl")
print("Deposits:", deposits)

# --- Withdrawals ---
withdrawals = client.list_withdrawals("brl")
print("Withdrawals:", withdrawals)

# --- Claims ---
claims = client.list_claims()
print("Claims:", claims)

claimable = client.simulate_claims()
print("Claimable:", claimable)
