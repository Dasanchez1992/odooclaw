package tools

import (
	"context"
	"testing"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func executeWithResult(t *testing.T, res *mcp.CallToolResult) *ToolResult {
	t.Helper()
	manager := &MockMCPManager{
		callToolFunc: func(ctx context.Context, serverName, toolName string, arguments map[string]any) (*mcp.CallToolResult, error) {
			return res, nil
		},
	}
	return NewMCPTool(manager, "odoo-manager", &mcp.Tool{Name: "odoo_search_read"}).
		Execute(context.Background(), map[string]any{"model": "sale.order"})
}

// Regression: FastMCP returns zero content items for an empty list. The model
// got "" and concluded its call had been sent without arguments.
func TestMCPTool_Execute_EmptyResultIsExplicit(t *testing.T) {
	got := executeWithResult(t, &mcp.CallToolResult{Content: []mcp.Content{}})
	if got.IsError {
		t.Fatalf("empty result must not be an error: %s", got.ForLLM)
	}
	if got.ForLLM != emptyMCPResultForLLM {
		t.Errorf("expected explicit empty marker, got %q", got.ForLLM)
	}
}

func TestMCPTool_Execute_FallsBackToStructuredContent(t *testing.T) {
	got := executeWithResult(t, &mcp.CallToolResult{
		Content:           []mcp.Content{},
		StructuredContent: map[string]any{"result": []any{}},
	})
	if got.ForLLM != `{"result":[]}` {
		t.Errorf("expected structured content, got %q", got.ForLLM)
	}
}
