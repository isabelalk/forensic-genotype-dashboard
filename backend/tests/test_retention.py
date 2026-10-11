import os
import tempfile
from pathlib import Path
from unittest import TestCase

from app.services.retention import (
    directory_bytes,
    sweep_artifacts,
    sweep_uploads,
    touch_last_use,
)

NOW = 1_000_000.0


def set_times(path: Path, atime: float, mtime: float) -> None:
    os.utime(path, ns=(int(atime * 1e9), int(mtime * 1e9)))


class UploadSweepTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _upload(self, name: str, uploaded_at: float, last_used: float, size: int = 10) -> Path:
        path = self.dir / name
        path.write_bytes(b"x" * size)
        set_times(path, atime=last_used, mtime=uploaded_at)
        return path

    def test_idle_expired_upload_is_removed(self) -> None:
        self._upload("idle.vcf", uploaded_at=NOW - 600, last_used=NOW - 301)
        removed = sweep_uploads(self.dir, idle_ttl_seconds=300, max_age_seconds=1800, now=NOW)
        self.assertEqual(removed, 1)
        self.assertFalse((self.dir / "idle.vcf").exists())

    def test_active_upload_is_kept(self) -> None:
        self._upload("active.vcf", uploaded_at=NOW - 1200, last_used=NOW - 60)
        removed = sweep_uploads(self.dir, idle_ttl_seconds=300, max_age_seconds=1800, now=NOW)
        self.assertEqual(removed, 0)
        self.assertTrue((self.dir / "active.vcf").exists())

    def test_hard_cap_removes_active_upload(self) -> None:
        self._upload("old.vcf", uploaded_at=NOW - 1801, last_used=NOW - 1)
        removed = sweep_uploads(self.dir, idle_ttl_seconds=300, max_age_seconds=1800, now=NOW)
        self.assertEqual(removed, 1)
        self.assertFalse((self.dir / "old.vcf").exists())

    def test_touch_last_use_updates_atime_only(self) -> None:
        path = self._upload("touch.vcf", uploaded_at=NOW - 100, last_used=NOW - 100)
        touch_last_use(path, now=NOW)
        stat = path.stat()
        self.assertAlmostEqual(stat.st_atime, NOW, places=3)
        self.assertAlmostEqual(stat.st_mtime, NOW - 100, places=3)

    def test_directory_bytes_sums_files(self) -> None:
        self._upload("a.vcf", NOW, NOW, size=10)
        self._upload("b.vcf", NOW, NOW, size=15)
        self.assertEqual(directory_bytes(self.dir), 25)
        self.assertEqual(directory_bytes(self.dir / "missing"), 0)

    def test_missing_directory_is_a_noop(self) -> None:
        self.assertEqual(sweep_uploads(self.dir / "nope", 300, 1800, now=NOW), 0)


class ArtifactSweepTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _artifact(self, name: str, generated_at: float, size: int) -> Path:
        folder = self.dir / name
        folder.mkdir()
        (folder / "payload.zip").write_bytes(b"x" * size)
        set_times(folder, atime=generated_at, mtime=generated_at)
        return folder

    def test_age_expiry(self) -> None:
        self._artifact("old", NOW - 1861, 10)
        self._artifact("fresh", NOW - 10, 10)
        removed = sweep_artifacts(self.dir, max_age_seconds=1800, max_count=100, max_bytes=10_000, now=NOW)
        self.assertEqual(removed, 1)
        self.assertFalse((self.dir / "old").exists())
        self.assertTrue((self.dir / "fresh").exists())

    def test_byte_quota_evicts_oldest_first(self) -> None:
        self._artifact("oldest", NOW - 300, 400)
        self._artifact("middle", NOW - 200, 400)
        self._artifact("newest", NOW - 100, 400)
        removed = sweep_artifacts(self.dir, max_age_seconds=1800, max_count=100, max_bytes=1000, now=NOW)
        self.assertEqual(removed, 1)
        self.assertFalse((self.dir / "oldest").exists())
        self.assertTrue((self.dir / "middle").exists())
        self.assertTrue((self.dir / "newest").exists())

    def test_reserve_bytes_makes_room_for_new_artifact(self) -> None:
        self._artifact("a", NOW - 300, 400)
        self._artifact("b", NOW - 200, 400)
        removed = sweep_artifacts(
            self.dir, max_age_seconds=1800, max_count=100, max_bytes=1000, now=NOW, reserve_bytes=300
        )
        self.assertEqual(removed, 1)
        self.assertFalse((self.dir / "a").exists())

    def test_count_limit_keeps_newest(self) -> None:
        for index in range(4):
            self._artifact(f"art{index}", NOW - (100 - index), 1)
        removed = sweep_artifacts(self.dir, max_age_seconds=1800, max_count=2, max_bytes=10_000, now=NOW)
        self.assertEqual(removed, 2)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["art2", "art3"])


class UploadLookupTouchTest(TestCase):
    def test_lookup_refreshes_atime_and_keeps_mtime(self) -> None:
        from uuid import uuid4

        from app.services.upload_lookup import find_uploaded_vcf

        with tempfile.TemporaryDirectory() as tmp:
            upload_dir = Path(tmp)
            file_id = str(uuid4())
            path = upload_dir / f"{file_id}.vcf"
            path.write_bytes(b"x")
            set_times(path, atime=NOW - 500, mtime=NOW - 500)

            found = find_uploaded_vcf(file_id, upload_dir)

            self.assertEqual(found, path)
            stat = path.stat()
            self.assertGreater(stat.st_atime, NOW)
            self.assertAlmostEqual(stat.st_mtime, NOW - 500, places=3)
            self.assertIsNone(find_uploaded_vcf("not-a-uuid", upload_dir))
