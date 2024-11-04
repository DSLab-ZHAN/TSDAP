from datetime import datetime, timedelta
from TSDAP.utils.dockerstyle import generate_unique_docker_style_name, human_readable_time_difference


def test_generate_unique_docker_style_name():
    name1 = generate_unique_docker_style_name()
    name2 = generate_unique_docker_style_name()

    assert isinstance(name1, str)
    assert isinstance(name2, str)
    assert name1 != name2  # Ensure uniqueness


def test_human_readable_time_difference():
    now = datetime.now()

    assert human_readable_time_difference(now - timedelta(seconds=30)) == "30 seconds ago"
    assert human_readable_time_difference(now - timedelta(minutes=5)) == "5 minutes ago"
    assert human_readable_time_difference(now - timedelta(hours=2)) == "2 hours ago"
    assert human_readable_time_difference(now - timedelta(days=3)) == "3 days ago"
    assert human_readable_time_difference(now - timedelta(days=45)) == "1 months ago"
    assert human_readable_time_difference(now - timedelta(days=400)) == "1 years ago"
