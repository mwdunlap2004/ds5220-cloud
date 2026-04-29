from src.pipeline import load_config


def test_load_config_has_required_sections():
    cfg = load_config("config/pipeline.yaml")
    assert "firms" in cfg
    assert "gibs" in cfg
    assert "sampling" in cfg
    assert "quality" in cfg
    assert "output" in cfg
