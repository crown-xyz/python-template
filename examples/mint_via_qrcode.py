#!/usr/bin/env python3
"""Mint BRLV on a sub-account, funded by a dynamic PIX brcode.

Creates a BRL -> BRLV quote and an order with source-payment-method
"dynamic-brcode": instead of debiting the account's BRL balance, the order
issues a one-time PIX charge for the exact amount. Pay it and the mint
proceeds automatically. The script prints the copy-paste brcode payload
and, when the response carries a QR image, writes mint-qrcode.html so the
code can be scanned.

All inputs come from environment variables. Wallet addresses and account
ids are real, sensitive values — none of them have in-code defaults, and
they must never be committed.

Required environment variables:
    CROWN_API_KEY            partner API key
    CROWN_PRIVATE_KEY_PATH   path to the RSA private key PEM
    CROWN_BASE_URL           e.g. https://api.brl.xyz
    SUB_ACCOUNT_ID           sub-account to mint on
    TARGET_BRLV_WALLET       wallet that receives the minted BRLV
    MINT_AMOUNT              BRL amount, e.g. 4.00

Usage:
    python examples/mint_via_qrcode.py
"""

import json
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from crown import CrownClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

QR_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>PIX QR Code</title>
  <style>
    body {{ display: flex; align-items: center; justify-content: center;
           min-height: 100vh; margin: 0; background: #f5f5f5;
           font-family: -apple-system, sans-serif; }}
    .card {{ background: #fff; padding: 32px; border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); text-align: center; }}
    img {{ width: 300px; height: 300px; image-rendering: pixelated; }}
    h1 {{ font-size: 18px; margin: 0 0 16px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>PIX — scan to pay</h1>
    <img alt="PIX QR code" src="data:image/png;base64,{qr_base64}" />
  </div>
</body>
</html>
"""


def require_env(*names):
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        print("Missing required environment variables:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)
    return [os.environ[name] for name in names]


def main():
    api_key, private_key_path, base_url = require_env(
        "CROWN_API_KEY", "CROWN_PRIVATE_KEY_PATH", "CROWN_BASE_URL"
    )
    sub_account_id, target_wallet, amount = require_env(
        "SUB_ACCOUNT_ID", "TARGET_BRLV_WALLET", "MINT_AMOUNT"
    )

    client = CrownClient(
        api_key=api_key,
        private_key_path=private_key_path,
        base_url=base_url,
    )
    account = client.account(sub_account_id)

    try:
        quote = account.create_quote(
            source_asset="fiat/brl",
            target_asset="eth-base/brlv",
            source_amount=amount,
        )
        print("Quote:", json.dumps(quote, indent=2))

        result = account.create_order(
            quote["id"],
            target_wallet_address=target_wallet,
            source_payment_method="dynamic-brcode",
        )
        print("Order:", json.dumps(result, indent=2))
    except requests.HTTPError as exc:
        print(f"FAILED [{exc.response.status_code}]: {exc.response.text}")
        return 1

    order = result.get("order", {})
    brcode = order.get("brcode")
    if not brcode:
        print(
            "\nOrder created but no brcode in the response — is the "
            "environment running the automint feature?"
        )
        return 1

    print("\n" + "=" * 76)
    print("PIX brcode — copy and pay:")
    print("=" * 76)
    print(brcode)
    print("=" * 76)
    if order.get("expiration"):
        print(f"Expires at: {order['expiration']}")
    print(f"Order id:   {order.get('id')}")

    qr_base64 = order.get("qr-code-base64")
    if qr_base64:
        page = Path("mint-qrcode.html")
        page.write_text(QR_PAGE.format(qr_base64=qr_base64))
        print(f"QR page:    {page.resolve()}")
    elif order.get("picture-url"):
        print(f"QR image:   {order['picture-url']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
