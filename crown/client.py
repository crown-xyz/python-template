import json
from pathlib import Path

import requests

from crown.auth import sign_request


class CrownClient:
    """HTTP client for the Crown API.

    Args:
        api_key: Your Crown API key.
        private_key_path: Path to the RSA private key PEM file.
        base_url: Crown API base URL.
    """

    def __init__(
        self,
        api_key: str,
        private_key_path: str,
        base_url: str = "https://api.brl.xyz",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.private_key = Path(private_key_path).read_text()

    def _headers(self, uri: str, body: dict | None = None) -> dict:
        token = sign_request(
            api_key=self.api_key,
            private_key=self.private_key,
            uri=uri,
            body=body,
        )
        return {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, uri: str, params: dict | None = None) -> dict:
        resp = requests.get(
            f"{self.base_url}{uri}",
            headers=self._headers(uri),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, uri: str, body: dict) -> dict:
        resp = requests.post(
            f"{self.base_url}{uri}",
            headers=self._headers(uri, body),
            data=json.dumps(body),
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------

    def get_balance(self, asset: str = "brl") -> dict:
        """Get account balance for the given asset."""
        return self._get(f"/api/v0/assets/{asset}/balance")

    # ------------------------------------------------------------------
    # Wallets
    # ------------------------------------------------------------------

    def list_wallets(
        self,
        assets: list[str] | None = None,
        addresses: list[str] | None = None,
    ) -> dict:
        """List wallets, optionally filtering by assets or addresses."""
        params = {}
        if assets:
            params["assets"] = assets
        if addresses:
            params["addresses"] = addresses
        return self._get("/api/v0/wallets", params=params)

    def create_wallet(self, name: str) -> dict:
        """Create a new wallet with the given name."""
        return self._post("/api/v0/wallets", {"wallet-name": name})

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------

    def create_quote(
        self,
        source_asset: str,
        target_asset: str,
        *,
        source_amount: str | None = None,
        target_amount: str | None = None,
        trade_reason: str | None = None,
    ) -> dict:
        """Create a conversion quote. Provide either source_amount or target_amount."""
        body: dict = {
            "source-asset": source_asset,
            "target-asset": target_asset,
        }
        if source_amount is not None:
            body["source-amount"] = source_amount
        if target_amount is not None:
            body["target-amount"] = target_amount
        if trade_reason is not None:
            body["trade-reason"] = trade_reason
        return self._post("/api/v0/quotes", body)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def list_orders(self) -> dict:
        """List all orders."""
        return self._get("/api/v0/orders")

    def get_order(self, order_id: str) -> dict:
        """Retrieve a specific order by ID."""
        return self._get(f"/api/v0/orders/{order_id}")

    def create_order(
        self,
        quote_id: str,
        *,
        source_wallet_address: str | None = None,
        target_wallet_address: str | None = None,
        target_end_user_pix_key: str | None = None,
    ) -> dict:
        """Create an order from an accepted quote.

        Wallet addresses are required only for token assets.
        For off-ramp orders settling to PIX, pass ``target_end_user_pix_key``.
        """
        body: dict = {"quote-id": quote_id}
        if source_wallet_address is not None:
            body["source-wallet-address"] = source_wallet_address
        if target_wallet_address is not None:
            body["target-wallet-address"] = target_wallet_address
        if target_end_user_pix_key is not None:
            body["target-end-user-pix-key"] = target_end_user_pix_key
        return self._post("/api/v0/orders", body)

    # ------------------------------------------------------------------
    # Transfers
    # ------------------------------------------------------------------

    def list_transfers(
        self,
        source_address: str | None = None,
        target_address: str | None = None,
        asset: str | None = None,
        state: str | None = None,
    ) -> dict:
        """List token transfers with optional filters."""
        params = {}
        if source_address:
            params["source-address"] = source_address
        if target_address:
            params["target-address"] = target_address
        if asset:
            params["asset"] = asset
        if state:
            params["state"] = state
        return self._get("/api/v0/transfers", params=params)

    def create_transfer(
        self,
        source_address: str,
        target_address: str,
        asset: str,
        amount: str,
    ) -> dict:
        """Transfer tokens between EVM wallets."""
        return self._post(
            "/api/v0/transfers",
            {
                "source-address": source_address,
                "target-address": target_address,
                "asset": asset,
                "amount": amount,
            },
        )

    # ------------------------------------------------------------------
    # Deposits
    # ------------------------------------------------------------------

    def list_deposits(self, asset: str = "brl") -> dict:
        """List deposits for the given asset."""
        return self._get(f"/api/v0/assets/{asset}/deposits")

    # ------------------------------------------------------------------
    # Withdrawals
    # ------------------------------------------------------------------

    def list_withdrawals(self, asset: str = "brl") -> dict:
        """List all withdrawals for the given asset."""
        return self._get(f"/api/v0/assets/{asset}/withdrawals")

    def get_withdrawal(self, withdrawal_id: str, asset: str = "brl") -> dict:
        """Retrieve a specific withdrawal by ID."""
        return self._get(f"/api/v0/assets/{asset}/withdrawals/{withdrawal_id}")

    def create_withdrawal_pix(self, amount: str, pix_key: str) -> dict:
        """Create a BRL withdrawal via PIX."""
        return self._post(
            "/api/v0/assets/brl/withdrawals",
            {
                "amount": amount,
                "method": "pix",
                "pix-key": pix_key,
            },
        )

    def create_withdrawal_ted(
        self,
        amount: str,
        *,
        bank_code: str,
        branch: str,
        account: str,
        account_type: str,
        document: str,
        name: str,
    ) -> dict:
        """Create a BRL withdrawal via TED."""
        return self._post(
            "/api/v0/assets/brl/withdrawals",
            {
                "amount": amount,
                "method": "ted",
                "bank-code": bank_code,
                "branch": branch,
                "account": account,
                "account-type": account_type,
                "document": document,
                "name": name,
            },
        )

    # ------------------------------------------------------------------
    # Claims
    # ------------------------------------------------------------------

    def list_claims(self) -> dict:
        """List all claims."""
        return self._get("/api/v0/claims")

    def simulate_claims(self) -> dict:
        """Get claimable operations with tax information."""
        return self._get("/api/v0/claims/simulate")

    def create_claim(
        self, operation_ids: list[str], wallet_address: str
    ) -> dict:
        """Execute claims for operation IDs to a destination wallet."""
        return self._post(
            "/api/v0/claims",
            {
                "operation-ids": operation_ids,
                "wallet-address": wallet_address,
            },
        )
