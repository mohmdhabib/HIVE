import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.trend_harvester import trend_harvester_service
from app.services.task_store import task_store
from app.services.video_renderer import video_renderer
from app.schemas.trend import BatchHarvestRequest


@pytest.mark.anyio
async def test_run_batch_harvest_service():
    # Run batch harvest for 2 specific workers with 2 drafts each
    report = await trend_harvester_service.run_batch_harvest(
        worker_ids=["tech", "lifestyle"],
        drafts_per_worker=2,
        llm=None,
    )

    assert report.status == "completed"
    assert report.total_drafts_generated == 4
    assert len(report.drafts) == 4
    assert "tech" in report.workers_covered
    assert "lifestyle" in report.workers_covered
    assert report.execution_time_seconds >= 0

    # Verify each draft was properly indexed and queued in task_store and video_renderer
    for draft in report.drafts:
        assert draft.blueprint_id.startswith("vbp-")
        assert draft.task_id.startswith("task-vbp-")
        assert draft.virality_score >= 60
        assert draft.scenes_count >= 5
        assert draft.duration_seconds > 10.0
        assert len(draft.hook_preview) > 5

        # Check blueprint is in video_renderer memory
        bp = video_renderer.get_or_load_blueprint(draft.blueprint_id)
        assert bp is not None
        assert bp.blueprint_id == draft.blueprint_id

        # Check task is saved in task_store awaiting operator approval
        task = task_store.get_task(draft.task_id)
        assert task is not None
        assert task.status == "needs_approval"
        assert task.approval_required is True
        assert task.content is not None
        assert len(task.content.hook) > 0


def test_harvester_get_status():
    status = trend_harvester_service.get_status()
    assert "status" in status
    assert "schedule" in status
    assert status["schedule"]["enabled"] is True
    assert status["queued_drafts_count"] >= 4
    assert status["recent_batches_count"] >= 1
    assert status["last_batch"] is not None


def test_harvester_update_schedule():
    cfg = trend_harvester_service.update_schedule(
        enabled=True,
        cron_expression="0 7 * * *",
        drafts_per_worker=3,
    )
    assert cfg.enabled is True
    assert cfg.cron_expression == "0 7 * * *"
    assert cfg.drafts_per_worker == 3
    assert cfg.next_run is not None


@pytest.mark.anyio
async def test_batch_harvest_endpoints():
    from app.api.routes import (
        run_batch_harvest_endpoint,
        get_batch_harvest_status,
        update_batch_harvest_schedule,
        UpdateScheduleRequest,
    )

    # 1. Test Status Endpoint
    st = await get_batch_harvest_status()
    assert "status" in st
    assert "queued_drafts_count" in st

    # 2. Test Schedule Update Endpoint
    up_req = UpdateScheduleRequest(enabled=True, cron_expression="0 8 * * *", drafts_per_worker=2)
    up_res = await update_batch_harvest_schedule(up_req)
    assert up_res.cron_expression == "0 8 * * *"

    # 3. Test Batch Harvest Endpoint
    harvest_req = BatchHarvestRequest(worker_ids=["biz"], drafts_per_worker=1)
    harvest_res = await run_batch_harvest_endpoint(req=harvest_req, llm=None)
    assert harvest_res.status == "completed"
    assert len(harvest_res.drafts) == 1
    assert harvest_res.drafts[0].worker_id == "business" or harvest_res.drafts[0].worker_id == "biz"

    # 4. Test Render Blueprint by ID Endpoint
    from app.api.routes import render_blueprint_by_id_endpoint
    bp_id = harvest_res.drafts[0].blueprint_id
    job = await render_blueprint_by_id_endpoint(blueprint_id=bp_id)
    assert job is not None
    assert job.blueprint_id == bp_id
    assert job.status in ("queued", "processing", "generating_tts", "compositing", "encoding", "complete")
