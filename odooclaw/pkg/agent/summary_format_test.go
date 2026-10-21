package agent

import (
	"strings"
	"testing"

	"github.com/nicolasramos/odooclaw/pkg/providers"
)

// Regression: the summarizer only saw Content, which is empty for tool calls,
// and persisted "calls were sent without arguments" into the session summary.
func TestFormatMessageForSummaryKeepsToolCallArguments(t *testing.T) {
	call := providers.Message{
		Role: "assistant",
		ToolCalls: []providers.ToolCall{{
			ID: "1",
			Function: &providers.FunctionCall{
				Name:      "mcp_odoo-manager_odoo_read_group",
				Arguments: `{"model":"account.move.line","domain":[["partner_id","=",201019],["product_id","=",50146]]}`,
			},
		}},
	}
	got := formatMessageForSummary(call)
	for _, want := range []string{"[tool call] mcp_odoo-manager_odoo_read_group(", `["partner_id","=",201019]`, `["product_id","=",50146]`} {
		if !strings.Contains(got, want) {
			t.Errorf("summary line %q missing %q", got, want)
		}
	}

	result := formatMessageForSummary(providers.Message{Role: "tool", Content: `[{"__count": 201, "price_subtotal": 689.77}]`})
	if !strings.Contains(result, "[tool result]") || !strings.Contains(result, "689.77") {
		t.Errorf("tool result not rendered: %q", result)
	}
}

func TestFormatMessageForSummaryTruncatesLongToolResultsOnRuneBoundary(t *testing.T) {
	long := strings.Repeat("ñ", summaryToolResultMaxChars+50)
	got := formatMessageForSummary(providers.Message{Role: "tool", Content: long})
	if !strings.Contains(got, "…[truncated]") {
		t.Fatalf("expected truncation marker, got %d bytes", len(got))
	}
	if strings.ContainsRune(got, '�') {
		t.Errorf("truncation split a multi-byte rune")
	}
}

func TestFormatMessageForSummaryPlainMessages(t *testing.T) {
	if got := formatMessageForSummary(providers.Message{Role: "user", Content: "hola"}); got != "user: hola\n" {
		t.Errorf("user message rendered as %q", got)
	}
}
