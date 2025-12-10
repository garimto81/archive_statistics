"""
Tests for Worker Statistics API
TDD: RED phase - tests written before implementation
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db, engine
from app.models import Base, Archive, WorkStatus


@pytest.fixture(scope="function")
async def setup_db():
    """Create tables and seed test data"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(setup_db):
    """Async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def seed_work_status(setup_db):
    """Seed test data with multiple workers"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import async_session_maker

    async with async_session_maker() as session:
        # Create archives
        archive1 = Archive(name="WSOP", description="World Series of Poker")
        archive2 = Archive(name="HCL", description="Hustler Casino Live")
        session.add_all([archive1, archive2])
        await session.flush()

        # Create work statuses with different PICs
        work_statuses = [
            # Richie's work
            WorkStatus(archive_id=archive1.id, category="WSOP 2024", pic="Richie",
                      status="completed", total_videos=100, excel_done=100),
            WorkStatus(archive_id=archive1.id, category="WSOP 2023", pic="Richie",
                      status="in_progress", total_videos=80, excel_done=60),
            # David's work
            WorkStatus(archive_id=archive2.id, category="HCL Season 1", pic="David",
                      status="completed", total_videos=50, excel_done=50),
            WorkStatus(archive_id=archive2.id, category="HCL Season 2", pic="David",
                      status="pending", total_videos=40, excel_done=0),
            # Unassigned work
            WorkStatus(archive_id=archive1.id, category="WSOP Paradise", pic=None,
                      status="pending", total_videos=30, excel_done=0),
        ]
        session.add_all(work_statuses)
        await session.commit()

    yield


class TestWorkerStatsAPI:
    """Test cases for /api/worker-stats endpoints"""

    @pytest.mark.asyncio
    async def test_get_worker_stats_summary(self, client, seed_work_status):
        """GET /api/worker-stats should return worker statistics"""
        response = await client.get("/api/worker-stats")

        assert response.status_code == 200
        data = response.json()

        # Should have workers list
        assert "workers" in data
        assert isinstance(data["workers"], list)

        # Should have summary
        assert "summary" in data
        assert "total_workers" in data["summary"]
        assert "total_videos" in data["summary"]
        assert "total_done" in data["summary"]
        assert "overall_progress" in data["summary"]

    @pytest.mark.asyncio
    async def test_worker_stats_contains_pic_data(self, client, seed_work_status):
        """Each worker should have detailed statistics"""
        response = await client.get("/api/worker-stats")

        assert response.status_code == 200
        data = response.json()

        # Find Richie's stats
        richie = next((w for w in data["workers"] if w["pic"] == "Richie"), None)
        assert richie is not None

        # Richie should have correct aggregated stats
        assert richie["total_videos"] == 180  # 100 + 80
        assert richie["total_done"] == 160    # 100 + 60
        assert richie["task_count"] == 2
        assert "progress_percent" in richie

    @pytest.mark.asyncio
    async def test_worker_stats_by_pic(self, client, seed_work_status):
        """GET /api/worker-stats/{pic} should return specific worker details"""
        response = await client.get("/api/worker-stats/Richie")

        assert response.status_code == 200
        data = response.json()

        assert data["pic"] == "Richie"
        assert "tasks" in data
        assert len(data["tasks"]) == 2  # Richie has 2 tasks

        # Tasks should include archive info
        for task in data["tasks"]:
            assert "archive_name" in task
            assert "category" in task
            assert "status" in task
            assert "progress_percent" in task

    @pytest.mark.asyncio
    async def test_worker_stats_nonexistent_pic(self, client, seed_work_status):
        """GET /api/worker-stats/{pic} with invalid pic returns 404"""
        response = await client.get("/api/worker-stats/NonexistentWorker")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_worker_stats_includes_unassigned(self, client, seed_work_status):
        """Unassigned tasks (pic=null) should be included in summary"""
        response = await client.get("/api/worker-stats")

        assert response.status_code == 200
        data = response.json()

        # Check summary includes unassigned videos
        assert data["summary"]["total_videos"] == 300  # 100+80+50+40+30

        # Should have "Unassigned" worker entry
        unassigned = next((w for w in data["workers"] if w["pic"] == "Unassigned"), None)
        assert unassigned is not None
        assert unassigned["total_videos"] == 30

    @pytest.mark.asyncio
    async def test_overall_summary_endpoint(self, client, seed_work_status):
        """GET /api/worker-stats/summary should return overall statistics"""
        response = await client.get("/api/worker-stats/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_workers"] == 3  # Richie, David, Unassigned
        assert data["total_videos"] == 300
        assert data["total_done"] == 210  # 100+60+50+0+0
        assert "overall_progress" in data
        assert "by_status" in data

        # Status breakdown
        assert data["by_status"]["completed"] == 2
        assert data["by_status"]["in_progress"] == 1
        assert data["by_status"]["pending"] == 2


class TestWorkerStatsEdgeCases:
    """Edge case tests"""

    @pytest.mark.asyncio
    async def test_empty_database(self, client, setup_db):
        """Should handle empty database gracefully"""
        response = await client.get("/api/worker-stats")

        assert response.status_code == 200
        data = response.json()

        assert data["workers"] == []
        assert data["summary"]["total_workers"] == 0
        assert data["summary"]["total_videos"] == 0

    @pytest.mark.asyncio
    async def test_special_characters_in_pic(self, client, setup_db):
        """Should handle special characters in PIC name"""
        # URL encoding test
        response = await client.get("/api/worker-stats/John%20Doe")

        # Should return 404 (not found) not 500 (server error)
        assert response.status_code == 404
