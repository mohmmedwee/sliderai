FR-034 — placeholder plan prices and monthly credits — backend/src/docu/core/config/billing.py plan_price_cents and plan_monthly_credits — replace with the decided price table
FR-037 — data region defaults to local — backend/src/docu/core/config/product.py data_region — set the production region
FR-038 — retention defaults to 30 days — backend/src/docu/core/config/product.py retention_days — set the production retention period
T012 — CI is running on main at https://github.com/mohmmedwee/sliderai/actions/runs/39313281689 and has not finished green — .github/workflows/ci.yml — wait for that run and tick T012 if every job passes, or fix the failing job
T013 — the production image was not built or health-checked; the worker stage installs Playwright and host ports 5432/6379/8000 may already be taken — infra/docker, infra/compose.prod.yaml — build on a free host after T024 adds Alembic, or run the build on CI
