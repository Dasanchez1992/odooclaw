"""Models copy Odoo's HTML chat and send "&gt;=" instead of ">=" in domains."""

import pytest

from odoo_mcp.core.domains import validate_domain
from odoo_mcp.core.exceptions import OdooSecurityError


@pytest.mark.parametrize("escaped, plain", [("&gt;=", ">="), ("&lt;=", "<="), ("&gt;", ">"), ("&lt;", "<")])
def test_html_escaped_operators_are_unescaped_in_place(escaped, plain):
    domain = [["invoice_date", escaped, "2026-01-01"], ["state", "=", "posted"]]
    validate_domain(domain)
    assert domain == [["invoice_date", plain, "2026-01-01"], ["state", "=", "posted"]]


def test_unknown_operator_still_rejected_after_unescape():
    with pytest.raises(OdooSecurityError, match="Unsupported domain operator"):
        validate_domain([["name", "&amp;", "x"]])
