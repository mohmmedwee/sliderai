FR-034 — placeholder plan prices and monthly credits — backend/src/docu/core/config/billing.py plan_price_cents and plan_monthly_credits — replace with the decided price table
FR-037 — data region defaults to local — backend/src/docu/core/config/product.py data_region — set the production region
FR-038 — retention defaults to 30 days — backend/src/docu/core/config/product.py retention_days — set the production retention period
T006 — docker compose up fails because host ports 5432 and 6379 are already taken by other containers named postgres and redis — infra/compose.yaml — stop those containers so Docu can bind the card ports, or publish Docu on alternate host ports
T010 — the three-check success path was not run because no working UPSTREAM is configured; a dead endpoint prints three ✗ and exits 1 — backend/src/docu/scripts/check_endpoint.py — point UPSTREAM at a tool-capable model and rerun, or treat the failure path as enough
