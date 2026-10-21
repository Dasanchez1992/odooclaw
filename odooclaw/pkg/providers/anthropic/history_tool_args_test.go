package anthropicprovider

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/nicolasramos/odooclaw/pkg/providers/protocoltypes"
)

// Regression: history tool calls (as stored by the agent loop) carry their
// arguments only in Function.Arguments. They were replayed as `input: {}`,
// so Claude believed its own calls had been sent without parameters.
func TestBuildParamsReplaysHistoryToolCallArguments(t *testing.T) {
	messages := []Message{
		{Role: "user", Content: "¿Abad Dalila tiene ventas?"},
		{Role: "assistant", ToolCalls: []ToolCall{{
			ID:   "toolu_1",
			Type: "function",
			Name: "mcp_odoo-manager_odoo_find_sale_order",
			Function: &protocoltypes.FunctionCall{
				Name:      "mcp_odoo-manager_odoo_find_sale_order",
				Arguments: `{"limit":50,"partner_id":201437}`,
			},
		}}},
		{Role: "tool", ToolCallID: "toolu_1", Content: "[] (the tool ran successfully with the given arguments: 0 records matched)"},
	}

	params, err := buildParams(messages, nil, "claude-sonnet-5-5", map[string]any{})
	if err != nil {
		t.Fatalf("buildParams() error: %v", err)
	}
	raw, _ := json.Marshal(params.Messages)
	body := string(raw)
	if !strings.Contains(body, `"partner_id":201437`) || !strings.Contains(body, `"limit":50`) {
		t.Fatalf("tool_use input lost its arguments: %s", body)
	}
	if strings.Contains(body, `"input":{}`) {
		t.Errorf("tool_use replayed with empty input: %s", body)
	}
}

func TestToolCallArgumentsPrefersMapAndToleratesBadJSON(t *testing.T) {
	m := toolCallArguments(ToolCall{Arguments: map[string]any{"a": 1}, Function: &protocoltypes.FunctionCall{Arguments: `{"b":2}`}})
	if m["a"] != 1 || m["b"] != nil {
		t.Errorf("map arguments should win, got %v", m)
	}
	if got := toolCallArguments(ToolCall{Function: &protocoltypes.FunctionCall{Arguments: "{not json"}}); len(got) != 0 {
		t.Errorf("bad JSON should yield empty map, got %v", got)
	}
}
