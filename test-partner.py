#!/usr/bin/env python3
"""Partner account API examples.

Exercises the v1 partner account API: sub-account creation and
account-scoped quotes/orders. Two modes:

    # Create two sub-accounts (with external wallets) and Crown wallets
    python test-partner.py -c

    # Run the order flows against existing sub-accounts
    python test-partner.py -e SUB_ACCOUNT_ID [SUB_ACCOUNT_ID_2]

    # Auto mint: BRL -> BRLV order funded by a dynamic PIX brcode
    python test-partner.py -m SUB_ACCOUNT_ID

Setup:
    1. Copy .env.example to .env and fill in your credentials
    2. Place your private key PEM file at the configured path
    3. pip install -e .

Environment variables (tax ids, wallets and account ids are real,
sensitive values — there are no in-code defaults):
    - SUB1_TAX_ID / SUB2_TAX_ID : tax ids used by -c (required)
    - SUB1_EXTERNAL_WALLET / SUB2_EXTERNAL_WALLET : external wallets
      declared at creation time by -c (required)
    - PARTNER_ACCOUNT_ID : partner (parent) account id (required by -e)
    - SUB1_BRLV_WALLET / SUB1_USDC_WALLET : wallets used by -e and -m
      (optional; when unset, the script discovers them from the sub-account)
    - MINT_AMOUNT : BRL amount for the -m auto mint (default 4.00)
"""

import argparse
import json
import logging
import os
import sys
import uuid

import requests
from dotenv import load_dotenv

from crown import CrownClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

# Account ids, tax ids and wallet addresses are real, sensitive values:
# they must come from the environment, never from code.
PARTNER_ACCOUNT_ID = os.environ.get("PARTNER_ACCOUNT_ID")


def show(label, fn, *args, **kwargs):
    """Run an API call, pretty-print the result, and keep going on errors."""
    print(f"\n=== {label} ===")
    try:
        result = fn(*args, **kwargs)
        print(json.dumps(result, indent=2))
        return result
    except requests.HTTPError as exc:
        print(f"FAILED [{exc.response.status_code}]: {exc.response.text}")
        return None


def find_wallet_address(account, asset):
    """Return the address of the account's first wallet supporting asset."""
    wallets = account.list_wallets(assets=[asset]).get("wallets", [])
    return wallets[0]["address"] if wallets else None


# ----------------------------------------------------------------------------
# -c : create sub-accounts
# ----------------------------------------------------------------------------


def create_sub_accounts(client):
    """Create two sub-accounts, each with a declared external wallet and a
    Crown wallet."""
    subs = [
        {
            "label": "sub-account 1",
            "tax_id": os.environ["SUB1_TAX_ID"],
            "external_wallet": os.environ["SUB1_EXTERNAL_WALLET"],
        },
        # {
        #     "label": "sub-account 2",
        #     "tax_id": os.environ["SUB2_TAX_ID"],
        #     "external_wallet": os.environ["SUB2_EXTERNAL_WALLET"],
        # },
    ]

    created_ids = []
    for sub in subs:
        result = show(
            f"Create {sub['label']}",
            client.create_sub_account,
            tax_id=sub["tax_id"],
            tax_document_type="cpf",
            tax_residence="BRA",
            kyc_attestation_id=f"kyc-{uuid.uuid4()}",
            external_wallets=[
                {
                    "address": sub["external_wallet"],
                    "custody-country": "BRA",
                    "custody-type": "self",
                }
            ],
        )
        if result is None:
            continue

        account_id = result["account"]["id"]
        created_ids.append(account_id)

        # Sub-account creation is request-first: it enters compliance review
        # and is provisioned on approval, so wallet creation may fail until
        # the account is active.
        account = client.account(account_id)
        show(
            f"Create Crown wallet for {sub['label']}",
            account.create_wallet,
            f"{sub['label']} wallet",
        )

    if created_ids:
        ids = " ".join(created_ids)
        print(f"\nSub-account ids: {ids}")
        print(f"Run the order flows with: python test-partner.py -e {ids}")


# ----------------------------------------------------------------------------
# -m : auto mint funded by a dynamic PIX brcode
# ----------------------------------------------------------------------------


def auto_mint(client, sub_account_id):
    """Create a BRL -> BRLV order funded by a dynamic PIX brcode and print
    the brcode payload to copy and pay. The mint proceeds once it is paid."""
    sub = client.account(sub_account_id)

    brlv_wallet = os.environ.get("SUB1_BRLV_WALLET") or find_wallet_address(
        sub, "eth-base/brlv"
    )
    if not brlv_wallet:
        print("No BRLV wallet found for the sub-account; aborting.")
        return
    print(f"Target BRLV wallet: {brlv_wallet}")

    amount = os.environ.get("MINT_AMOUNT", "4.00")
    quote = show(
        f"BRL -> BRLV quote ({amount})",
        sub.create_quote,
        source_asset="fiat/brl",
        target_asset="eth-base/brlv",
        source_amount=amount,
    )
    if not quote:
        return

    result = show(
        "BRL -> BRLV auto-mint order (dynamic brcode)",
        sub.create_order,
        quote["id"],
        target_wallet_address=brlv_wallet,
        source_payment_method="dynamic-brcode",
    )
    if not result:
        return

    order = result.get("order", {})
    brcode = order.get("brcode")
    if not brcode:
        print("\nOrder created but no brcode in the response — is the "
              "environment running the automint feature?")
        return

    print("\n" + "=" * 76)
    print("PIX brcode — copy and pay:")
    print("=" * 76)
    print(brcode)
    print("=" * 76)
    if order.get("picture-url"):
        print(f"QR image:   {order['picture-url']}")
    if order.get("expiration"):
        print(f"Expires at: {order['expiration']}")
    print(f"Order id:   {order.get('id')}")
    print(f"\nAfter paying, check the order with:")
    print(f"    python test-partner.py -e {sub_account_id}")


# ----------------------------------------------------------------------------
# -e : execute orders for sub-accounts
# ----------------------------------------------------------------------------


def execute_orders(client, sub_account_ids):
    if not PARTNER_ACCOUNT_ID:
        print("PARTNER_ACCOUNT_ID is required for -e; set it in the environment.")
        return

    sub1_id = sub_account_ids[0]
    sub2_id = sub_account_ids[1] if len(sub_account_ids) > 1 else None

    parent = client.account(PARTNER_ACCOUNT_ID)
    sub1 = client.account(sub1_id)
    sub2 = client.account(sub2_id) if sub2_id else None

    # --- READ: sub-account discovery and lookup ---
    show("[0] List the parent's sub-accounts", client.list_sub_accounts)
    show("[0b] Get sub-account 1 by id", sub1.get)
    if sub2:
        show("[0b] Get sub-account 2 by id", sub2.get)
    show("[0c] Get the parent itself", parent.get)

    # Negative check: a random uuid is not the parent's sub-account -> 404.
    show(
        "[0d] Negative check (random uuid, expect 404)",
        client.get_account,
        str(uuid.uuid4()),
    )

    # --- Balances ---
    show("Parent BRL balance", parent.get_balance, "brl")
    show("Sub 1 BRL balance", sub1.get_balance, "brl")
    if sub2:
        show("Sub 2 BRL balance", sub2.get_balance, "brl")

    # --- PIX deposit QR (BR Code) ---
    show("[0g] Parent PIX deposit QR", parent.get_pix_deposit)
    show("[0g] Sub 1 PIX deposit QR", sub1.get_pix_deposit)
    if sub2:
        show("[0g] Sub 2 PIX deposit QR", sub2.get_pix_deposit)

    # --- Resolve sub 1 wallets ---
    sub1_brlv_wallet = os.environ.get("SUB1_BRLV_WALLET") or find_wallet_address(
        sub1, "eth-base/brlv"
    )
    sub1_usdc_wallet = os.environ.get("SUB1_USDC_WALLET") or find_wallet_address(
        sub1, "eth-base/usdc"
    )
    print(f"\nSub 1 BRLV wallet: {sub1_brlv_wallet}")
    print(f"Sub 1 USDC wallet: {sub1_usdc_wallet}")

    # ------------------------------------------------------------------
    # [1] BRL -> BRLV mint (capability: brlv-mint). Target wallet must be
    # owned by the sub-account (internal) or whitelisted.
    # ------------------------------------------------------------------
    quote = show(
        "[1] BRL -> BRLV quote",
        sub1.create_quote,
        source_asset="fiat/brl",
        target_asset="eth-base/brlv",
        source_amount="4.00",
    )
    if quote and sub1_brlv_wallet:
        show(
            "[1] BRL -> BRLV order",
            sub1.create_order,
            quote["id"],
            target_wallet_address=sub1_brlv_wallet,
        )

    # ------------------------------------------------------------------
    # [2] BRLV -> BRL burn (capability: brlv-burn). Source wallet must be
    # owned by the sub-account; BRL is delivered to its bank account.
    # ------------------------------------------------------------------
    quote = show(
        "[2] BRLV -> BRL quote",
        sub1.create_quote,
        source_asset="eth-base/brlv",
        target_asset="fiat/brl",
        source_amount="2.00",
    )
    if quote and sub1_brlv_wallet:
        show(
            "[2] BRLV -> BRL order",
            sub1.create_order,
            quote["id"],
            source_wallet_address=sub1_brlv_wallet,
        )

    # ------------------------------------------------------------------
    # [3] USDC -> BRL FX (capability: fx-orders). trade-reason is required
    # for FX.
    # ------------------------------------------------------------------
    quote = show(
        "[3] USDC -> BRL quote",
        sub1.create_quote,
        source_asset="eth-base/usdc",
        target_asset="fiat/brl",
        source_amount="1.20",
        trade_reason="transfer-between-same-entity-accounts",
    )
    if quote and sub1_usdc_wallet:
        show(
            "[3] USDC -> BRL order",
            sub1.create_order,
            quote["id"],
            source_wallet_address=sub1_usdc_wallet,
        )

    # ------------------------------------------------------------------
    # [4] BRL -> USDC FX
    # ------------------------------------------------------------------
    quote = show(
        "[4] BRL -> USDC quote",
        sub1.create_quote,
        source_asset="fiat/brl",
        target_asset="eth-base/usdc",
        source_amount="10.00",
        trade_reason="transfer-between-same-entity-accounts",
    )
    if quote and sub1_usdc_wallet:
        show(
            "[4] BRL -> USDC order",
            sub1.create_order,
            quote["id"],
            target_wallet_address=sub1_usdc_wallet,
        )

    # --- [5] List the sub-account's orders ---
    show("[5] Sub 1 orders", sub1.list_orders)


def main():
    parser = argparse.ArgumentParser(description="Partner account API examples")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c",
        "--create-sub-accounts",
        action="store_true",
        help="create two sub-accounts with external wallets and Crown wallets",
    )
    group.add_argument(
        "-e",
        "--execute-orders",
        nargs="+",
        metavar="SUB_ACCOUNT_ID",
        help="run the order flows for the given sub-account ids",
    )
    group.add_argument(
        "-m",
        "--auto-mint",
        metavar="SUB_ACCOUNT_ID",
        help="create a BRL->BRLV order funded by a dynamic PIX brcode "
        "and print the brcode to pay",
    )
    args = parser.parse_args()

    client = CrownClient(
        api_key=os.environ["CROWN_API_KEY"],
        private_key_path=os.environ["CROWN_PRIVATE_KEY_PATH"],
        base_url=os.environ.get("CROWN_BASE_URL", "https://api.brl.xyz"),
    )

    if args.create_sub_accounts:
        create_sub_accounts(client)
    elif args.auto_mint:
        auto_mint(client, args.auto_mint)
    else:
        execute_orders(client, args.execute_orders)


if __name__ == "__main__":
    sys.exit(main())
