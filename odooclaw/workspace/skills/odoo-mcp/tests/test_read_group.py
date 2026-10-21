"""Unit tests for odoo_read_group and the offset parameter of odoo_search_read."""

from unittest.mock import MagicMock

import pytest

from odoo_mcp.core.exceptions import OdooRPCError
from odoo_mcp.tools.records import odoo_read_group, odoo_search_read

FIELDS_GET = {
    "id": {"type": "integer"},
    "name": {"type": "char"},
    "invoice_date": {"type": "date"},
    "partner_id": {"type": "many2one"},
    "amount_total_signed": {"type": "monetary"},
}

AUGUST = [
    ["move_type", "=", "out_invoice"],
    ["invoice_date", ">=", "2026-08-01"],
    ["invoice_date", "<=", "2026-08-31"],
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "odoo_mcp.tools.records.guard_model_access", lambda *a, **k: None
    )
    monkeypatch.setattr("odoo_mcp.tools.records._field_cache", {})
    client = MagicMock()
    client.odoo_session.url = "https://erp.example.com"
    calls = []

    def call_kw(model, method, args=None, kwargs=None, sender_id=None):
        if method == "fields_get":
            return FIELDS_GET
        calls.append((model, method, args, kwargs, sender_id))
        if method == "read_group":
            return [
                {
                    "invoice_date:month": "agosto 2026",
                    "amount_total_signed": 34213.77,
                    "__count": 2340,
                    "__domain": AUGUST,
                    "__range": {},
                }
            ]
        return [{"id": 1, "name": "INV/1"}]

    client.call_kw.side_effect = call_kw
    client.calls = calls
    return client


def test_read_group_sends_odoo_payload(client):
    res = odoo_read_group(
        client,
        2,
        "account.move",
        AUGUST,
        ["amount_total_signed:sum", "__count"],
        ["invoice_date:month"],
        orderby="amount_total_signed desc",
    )

    assert client.calls == [
        (
            "account.move",
            "read_group",
            [AUGUST, ["amount_total_signed:sum", "__count"], ["invoice_date:month"]],
            {"lazy": False, "orderby": "amount_total_signed desc"},
            2,
        )
    ]
    assert res == [
        {
            "invoice_date:month": "agosto 2026",
            "amount_total_signed": 34213.77,
            "__count": 2340,
            "__range": {},
        }
    ]


def test_read_group_without_groupby_returns_grand_total(client):
    odoo_read_group(client, 2, "account.move", AUGUST, ["amount_total_signed:sum"])
    assert client.calls[0][2] == [AUGUST, ["amount_total_signed:sum"], []]


@pytest.mark.parametrize(
    "fields, groupby, message",
    [
        (["amount_total_signed:median"], [], "invalid aggregator"),
        (["amount_total_signed:sum"], ["invoice_date:hour"], "invalid granularity"),
        (["not_a_field:sum"], [], "unknown fields"),
        (["amount_total_signed:sum"], ["not_a_field"], "unknown fields"),
        ([], [], "fields is required"),
    ],
)
def test_read_group_rejects_bad_specs(client, fields, groupby, message):
    with pytest.raises(OdooRPCError, match=message):
        odoo_read_group(client, 2, "account.move", AUGUST, fields, groupby)
    assert client.calls == []


def test_search_read_passes_offset(client):
    odoo_search_read(client, 2, "account.move", AUGUST, ["name"], limit=80, offset=160)
    assert client.calls[0][3] == {"limit": 80, "offset": 160, "fields": ["name"]}


def test_search_read_omits_offset_by_default(client):
    odoo_search_read(client, 2, "account.move", AUGUST, ["name"], limit=80)
    assert client.calls[0][3] == {"limit": 80, "fields": ["name"]}


@pytest.mark.parametrize(
    "raw, sent",
    [
        ('"invoice_date:month asc"', "invoice_date:month asc"),
        ("'amount_total_signed desc'", "amount_total_signed desc"),
        ('"invoice_date:month asc", "partner_id"', "invoice_date:month asc, partner_id"),
    ],
)
def test_read_group_strips_quotes_from_orderby(client, raw, sent):
    """LLMs wrap orderby in quotes; Odoo rejects that with 'Invalid order'."""
    odoo_read_group(
        client, 2, "account.move", AUGUST, ["amount_total_signed:sum"],
        ["invoice_date:month"], orderby=raw,
    )
    assert client.calls[0][3] == {"lazy": False, "orderby": sent}


def test_read_group_rejects_malformed_orderby(client):
    with pytest.raises(OdooRPCError, match="invalid orderby term"):
        odoo_read_group(
            client, 2, "account.move", AUGUST, ["amount_total_signed:sum"],
            orderby="invoice_date; DROP TABLE x",
        )
    assert client.calls == []
