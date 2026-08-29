"""
General helper functions and utility methods.
"""

def format_summary_stats(stats: dict) -> str:
    """Format summary statistics dictionary into a clean display string."""
    return "\n".join([f"{k}: {v}" for k, v in stats.items()])
