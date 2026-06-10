#!/usr/bin/env python3
"""Create a partner sub-account.

All inputs come from environment variables. Tax ids, wallet addresses and
account ids are real, sensitive values — none of them have in-code
defaults, and they must never be committed.

Required environment variables:
    CROWN_API_KEY            partner API key
    CROWN_PRIVATE_KEY_PATH   path to the RSA private key PEM
    CROWN_BASE_URL           e.g. https://api.brl.xyz
    SUB_TAX_ID               sub-account holder's tax id (PII)
    SUB_TAX_DOCUMENT_TYPE    cpf | passport | national-id
    SUB_TAX_RESIDENCE        ISO-3 country, e.g. BRA
    KYC_ATTESTATION_ID       partner's reference to its completed KYC

Optional — declare an external wallet on the sub-account:
    EXTERNAL_WALLET_ADDRESS          0x address
    EXTERNAL_WALLET_CUSTODY_TYPE     self | exchange (required with address)
    EXTERNAL_WALLET_CUSTODY_COUNTRY  ISO-3 (required with address)

Usage:
    python examples/create_subaccount.py
"""

import json
import logging
import os
import sys

import requests
from dotenv import load_dotenv

from crown import CrownClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")


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
    tax_id, tax_document_type, tax_residence, kyc_attestation_id = require_env(
        "SUB_TAX_ID",
        "SUB_TAX_DOCUMENT_TYPE",
        "SUB_TAX_RESIDENCE",
        "KYC_ATTESTATION_ID",
    )

    external_wallets = None
    if os.environ.get("EXTERNAL_WALLET_ADDRESS"):
        address, custody_type, custody_country = require_env(
            "EXTERNAL_WALLET_ADDRESS",
            "EXTERNAL_WALLET_CUSTODY_TYPE",
            "EXTERNAL_WALLET_CUSTODY_COUNTRY",
        )
        external_wallets = [
            {
                "address": address,
                "custody-type": custody_type,
                "custody-country": custody_country,
            }
        ]

    client = CrownClient(
        api_key=api_key,
        private_key_path=private_key_path,
        base_url=base_url,
    )

    try:
        result = client.create_sub_account(
            tax_id=tax_id,
            tax_document_type=tax_document_type,
            tax_residence=tax_residence,
            kyc_attestation_id=kyc_attestation_id,
            external_wallets=external_wallets,
        )
    except requests.HTTPError as exc:
        print(f"FAILED [{exc.response.status_code}]: {exc.response.text}")
        return 1

    print(json.dumps(result, indent=2))
    account = result.get("account", {})
    print(f"\nSub-account id: {account.get('id')}")
    print(f"Status:         {account.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
