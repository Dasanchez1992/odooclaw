"""open_invoices must count customer invoices, not POS/payment journal entries."""

from unittest.mock import MagicMock

from odoo_mcp.services.partner_service import get_partner_summary


def test_open_invoices_counts_only_customer_invoices():
    client = MagicMock()
    counts = {}

    def call_kw(model, method, args=None, kwargs=None, sender_id=None):
        if method in ("read", "search_read"):
            return [{"id": 201437, "name": "ABAD BOWEN DALILA MARISOL", "credit": 0, "debit": 0, "user_id": False}]
        if method == "search_count":
            counts[model] = args[0]
            return 0
        return []

    client.call_kw.side_effect = call_kw
    get_partner_summary(client, 2, 201437)

    assert ("move_type", "in", ["out_invoice", "out_refund"]) in counts["account.move"]
