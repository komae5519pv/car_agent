from pathlib import Path

app_name = "car-agent"
app_entrypoint = "car_agent.backend.app:app"
app_slug = "car_agent"
api_prefix = "/api"
dist_dir = Path(__file__).parent / "__dist__"
