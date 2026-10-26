"""Guard against accidentally replacing published M11 release artifacts.

The M12 workflow must introduce its own tag and assets after validation.
"""

from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
M11_TAG_GUARD = "if: github.ref == 'refs/tags/v0.11.0-rc1'"


def test_historical_windows_release_upload_is_tag_gated_and_no_clobber():
    content = (WORKFLOWS / "windows-release-smoke.yml").read_text(encoding="utf-8")
    publish_job = content.split("  publish-windows:\n", 1)[1]
    assert M11_TAG_GUARD in publish_job
    assert "gh release upload v0.11.0-rc1" in publish_job
    assert "--clobber" not in publish_job


def test_historical_bundle_publication_not_enabled_on_main():
    content = (WORKFLOWS / "bundle-release.yml").read_text(encoding="utf-8")
    build_job = content.split("  bundle-smoke:\n", 1)[1].split(
        "  publish-tagged-release:\n", 1
    )[0]
    publish_job = content.split("  publish-tagged-release:\n", 1)[1]
    assert M11_TAG_GUARD in build_job
    assert M11_TAG_GUARD in publish_job
    assert "refs/heads/main" not in publish_job
