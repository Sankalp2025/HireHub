# HireHub backend demo

This demo provides visible, repeatable proof of HireHub's backend using the real
FastAPI application, PostgreSQL database, JWT authentication, and
`POST /api/v1/analyses` endpoint.

The resume, job description, account, and resulting analysis are fictional and
safe for a public portfolio recording.

The headline score is based on category-weighted skill coverage. Hard skills
and domain terms carry more weight than generic keywords. The response also
reports raw TF-IDF lexical similarity as a diagnostic, but that two-document
signal does not currently control the overall score.

From the repository root, run:

```bash
make demo
```

The command creates `.env` from `.env.example` only when `.env` is absent,
starts the existing Docker Compose stack, and displays the analysis with Rich.
It uses an isolated `hirehub-demo` Compose project, database volume, and host
ports `18000` and `15432`; it never deletes Docker volumes or overwrites an
existing `.env`.

Run the lightweight response regression tests separately:

```bash
make demo-test
```

To run the client directly inside the isolated demo backend container:

```bash
DB_CONTAINER_NAME=hirehub_demo_db \
BACKEND_CONTAINER_NAME=hirehub_demo_backend \
POSTGRES_PORT=15432 BACKEND_PORT=18000 \
docker compose -p hirehub-demo exec backend python demo/run_demo.py
```

Optional environment variables:

- `HIREHUB_API_URL`: API base URL, defaulting to `http://localhost:8000`
- `HIREHUB_DEMO_EMAIL`: fictional local account email
- `HIREHUB_DEMO_PASSWORD`: fictional local account password

## Known limitation

The current analyzer does not distinguish requirement priority from job-posting
section labels such as “required” and “preferred.” Extracted terms still receive
category-aware weights, but a preferred hard skill is treated like a required
hard skill. Tier-aware section extraction and weighting is the planned
enhancement. The demo fixtures intentionally present technologies as a flat set
of target signals rather than implying priority the engine cannot model.

TF-IDF cosine similarity is retained as a lexical diagnostic rather than a
semantic match score. Embedding-based similarity is the planned path for a
future semantic component; it should be evaluated before receiving composite
weight.

Each uncategorized fallback keyword has less weight than a known hard skill,
but a large fallback bucket can still carry comparable total weight. Tightening
fallback extraction and evaluating its aggregate weight are planned calibration
work. The demo keeps that conservative scoring behavior visible in the category
breakdown while prioritizing known skills in the matched-skills panel.
