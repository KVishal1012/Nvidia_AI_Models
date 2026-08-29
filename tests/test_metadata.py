from jinja2.compiler import generate
import json 

from src.core.config import (METADATA_FILE, DATA_SUMMARY_FILE)
from src.core.metadata import generate_metadata_files

def test_generate_metadata_files():
    metadata, summary = generate_metadata_files() #type: ignore


    assert metadata is not None
    assert summary is not None
    
    assert "datasets" in metadata
    assert "datasets" in summary
    
    assert METADATA_FILE.exists()
    assert DATA_SUMMARY_FILE.exists()

def test_metadata_contains_expected_datasets():
    metadata, _ = generate_metadata_files()  

    expected = {
        "aoi",
        "roads",
        "buildings",
        "drainage",
        "rainfall",
        "streamflow",
    }

    assert expected.issubset(metadata["datasets"].keys())

def test_metadata_json_is_valid():
    generate_metadata_files()

    with DATA_SUMMARY_FILE.open("r",encoding="utf-8") as f:
        summary = json.load(f)

    assert isinstance(summary,dict)
    assert "city" in summary
    assert "datasets" in summary
    
        
        