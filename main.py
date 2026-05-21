"""Crown API usage examples.

Setup:
    1. Copy .env.example to .env and fill in your credentials
    2. Place your private key PEM file at the configured path
    3. pip install -e .
    4. python main.py

Write operations (order creation) are gated behind CROWN_EXECUTE_ORDERS=1.
Wallet addresses and PIX keys are read from environment variables:
    - INTERNAL_USDC_WALLET        : source wallet for USDC->BRL off-ramp
    - END_USER_PIX_KEY            : end-user PIX key for USDC->BRL off-ramp
    - TARGET_WHITELISTED_WALLET   : destination wallet for BRL->USDC on-ramp
    - EXTERNAL_WHITELISTED_WALLET : destination wallet for BRL->BRLV
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

EXECUTE_ORDERS = os.environ.get("CROWN_EXECUTE_ORDERS") == "1"


# --- Balance ---
balance = client.get_balance("brl")
print("Balance:", balance)

# --- Wallets ---
wallets = client.list_wallets()
print("Wallets:", wallets)

# --- Orders ---
orders = client.list_orders()
print("Orders:", orders)

# --- USDC -> BRL (off-ramp to PIX) ---
usdc_to_brl_quote = client.create_quote(
    source_asset="eth-base/usdc",
    target_asset="fiat/brl",
    source_amount="1.00",
    trade_reason="purchase-or-sale-of-other-services",
)
print("USDC->BRL quote:", usdc_to_brl_quote)

if EXECUTE_ORDERS:
    usdc_to_brl_order = client.create_order(
        quote_id=usdc_to_brl_quote["id"],
        source_wallet_address=os.environ["INTERNAL_USDC_WALLET"],
        target_end_user_pix_key=os.environ["END_USER_PIX_KEY"],
    )
    print("USDC->BRL order:", usdc_to_brl_order)
else:
    print("USDC->BRL order: skipped (set CROWN_EXECUTE_ORDERS=1 to place)")

# --- BRL -> USDC (on-ramp from PIX) ---
brl_to_usdc_quote = client.create_quote(
    source_asset="fiat/brl",
    target_asset="eth-base/usdc",
    source_amount="8.00",
    trade_reason="purchase-or-sale-of-computing-services",
)
print("BRL->USDC quote:", brl_to_usdc_quote)

if EXECUTE_ORDERS:
    brl_to_usdc_order = client.create_order(
        quote_id=brl_to_usdc_quote["id"],
        target_wallet_address=os.environ["TARGET_WHITELISTED_WALLET"],
    )
    print("BRL->USDC order:", brl_to_usdc_order)
else:
    print("BRL->USDC order: skipped (set CROWN_EXECUTE_ORDERS=1 to place)")

# --- BRL -> BRLV ---
brl_to_brlv_quote = client.create_quote(
    source_asset="fiat/brl",
    target_asset="eth-base/brlv",
    source_amount="2.00",
)
print("BRL->BRLV quote:", brl_to_brlv_quote)

if EXECUTE_ORDERS:
    brl_to_brlv_order = client.create_order(
        quote_id=brl_to_brlv_quote["id"],
        target_wallet_address=os.environ["EXTERNAL_WHITELISTED_WALLET"],
    )
    print("BRL->BRLV order:", brl_to_brlv_order)
else:
    print("BRL->BRLV order: skipped (set CROWN_EXECUTE_ORDERS=1 to place)")

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
