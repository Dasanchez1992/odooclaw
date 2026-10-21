"""The delegated RPC error reason must reach the agent instead of a bare HTTP 500."""

from unittest.mock import MagicMock

import pytest
import requests

from odoo_mcp.core.client import OdooClient
from odoo_mcp.core.exceptions import OdooRPCError


def _client_returning(status, body=None, text=""):
    response = MagicMock()
    response.status_code = status
    if body is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = body
    response.raise_for_status.side_effect = (
        requests.HTTPError(f"{status} Server Error") if status >= 400 else None
    )
    session = MagicMock()
    session.session.post.return_value = response
    client = OdooClient.__new__(OdooClient)
    client.odoo_session = session
    return client


def test_error_reason_is_surfaced():
    client = _client_returning(
        500,
        {"status": "error", "reason": "Odoo ORM error: ValueError: Invalid field 'x'"},
    )
    with pytest.raises(OdooRPCError, match=r"\(500\): Odoo ORM error: ValueError: Invalid field 'x'"):
        client._do_post("http://odoo/odooclaw/call_kw_as_user", {})


def test_non_json_error_keeps_network_error():
    client = _client_returning(502)
    with pytest.raises(OdooRPCError, match="Network error during RPC call: 502"):
        client._do_post("http://odoo/odooclaw/call_kw_as_user", {})
