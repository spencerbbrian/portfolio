"""
Entry point Dagster looks for when you run `dagster dev`. This turns the
existing churn_radar dbt project (staging -> intermediate -> marts) into
real Dagster assets -- one asset per dbt model, wired together in the same
dependency graph dbt already knows about.
"""
from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# Path to the dbt project, relative to this file.
DBT_PROJECT_DIR = Path(__file__).joinpath("..", "..", "dbt", "churn_radar").resolve()

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=str(Path.home() / ".dbt"),
)

# In dev, this makes sure dbt's manifest.json (the file describing every
# model and how they depend on each other) is freshly generated before
# Dagster tries to read it.
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def churn_radar_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    """One Dagster asset per dbt model. Running this asset runs `dbt build`."""
    yield from dbt.cli(["build"], context=context).stream()


defs = dg.Definitions(
    assets=[churn_radar_dbt_assets],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=str(Path.home() / ".dbt"),
        ),
    },
)
