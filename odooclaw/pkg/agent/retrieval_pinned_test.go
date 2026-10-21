package agent

import (
	"fmt"
	"testing"

	"github.com/nicolasramos/odooclaw/pkg/providers"
)

func pinnedTestDefs(n int) []providers.ToolDefinition {
	defs := make([]providers.ToolDefinition, 0, n+3)
	for i := 0; i < n; i++ {
		defs = append(defs, providers.ToolDefinition{
			Function: providers.ToolFunctionDefinition{
				Name: fmt.Sprintf("mcp_odoo-manager_odoo_find_sale_order_%d", i),
			},
		})
	}
	for _, name := range []string{
		"mcp_odoo-manager_odoo_read_group",
		"mcp_odoo-manager_odoo_search_read",
		"mcp_odoo-manager_odoo_model_schema",
	} {
		defs = append(defs, providers.ToolDefinition{
			Function: providers.ToolFunctionDefinition{Name: name},
		})
	}
	return defs
}

// The query that reproduced the bug: 128 "sale" tools outscore the generic
// aggregation tool, which then never reaches the cloud top-64.
func TestRetrieveRelevantToolsKeepsPinnedToolsForCloud(t *testing.T) {
	defs := pinnedTestDefs(128)
	top := retrieveRelevantTools(defs, "Hola dame un resumen de ventas agrupado por mes de todo este year", maxCloudToolsInPrompt)

	got := map[string]bool{}
	for _, d := range top {
		got[d.Function.Name] = true
	}
	for _, name := range []string{
		"mcp_odoo-manager_odoo_read_group",
		"mcp_odoo-manager_odoo_search_read",
		"mcp_odoo-manager_odoo_model_schema",
	} {
		if !got[name] {
			t.Errorf("%s missing from cloud top-%d", name, maxCloudToolsInPrompt)
		}
	}
	if len(top) != maxCloudToolsInPrompt {
		t.Errorf("expected %d tools, got %d", maxCloudToolsInPrompt, len(top))
	}
}

func TestRetrieveRelevantToolsDoesNotPinForLocalModels(t *testing.T) {
	defs := pinnedTestDefs(128)
	top := retrieveRelevantTools(defs, "dame las ventas", maxLocalToolsInPrompt)
	for _, d := range top {
		if isPinnedTool(d.Function.Name) {
			t.Errorf("local top-%d should not be forced to include %s", maxLocalToolsInPrompt, d.Function.Name)
		}
	}
}
