"""odoo_find_partner must return enough data to confirm the contact, not a bare id."""

from unittest.mock import MagicMock

from odoo_mcp import server


def test_find_partner_returns_identifying_fields(monkeypatch):
    client = MagicMock()
    client.odoo_session.get_uid.return_value = 18
    client.odoo_session.url = "https://erp.example.com"
    monkeypatch.setattr(server, "get_odoo_client", lambda: client)
    monkeypatch.setattr(server.partners, "odoo_find_partner", lambda c, uid, name, vat, email: 201019)
    read_calls = []

    def fake_read(c, uid, model, ids, fields):
        read_calls.append((uid, model, ids, fields))
        return [{"id": 201019, "name": "Consumidor final", "vat": "9999999999999", "email": False}]

    monkeypatch.setattr(server.records, "odoo_read", fake_read)

    res = server.odoo_find_partner(name="Consumidor Final", vat="9999999999999", sender_id=2)

    assert res == {"id": 201019, "name": "Consumidor final", "vat": "9999999999999", "email": False}
    assert read_calls == [(2, "res.partner", [201019], ["name", "vat", "email"])]
