"""Unit tests for the Open Knowledge Format (OKF) retrieval tools."""
import pytest
from agent.tools.okf_tool import list_concepts, read_concept

def test_list_concepts_full():
    """Test listing all concepts from knowledge/index.md."""
    result = list_concepts()
    assert "Section 1: PAID TIME OFF & LEAVE OPERATIONS" in result
    assert "Section 4: TRAVEL & EXPENSE (T&E) GUIDELINES" in result
    assert "1.1 Outpatient Sick Time & Hospitalization Leave (Singapore)" in result


def test_list_concepts_with_filter():
    """Test filtering concepts by keyword."""
    result = list_concepts("sick")
    assert "1.1 Outpatient Sick Time & Hospitalization Leave (Singapore)" in result
    # Non-matching sections should not be present
    assert "Section 4: TRAVEL & EXPENSE" not in result


def test_read_concept_valid():
    """Test reading a valid concept document."""
    concept_path = "01-paid-time-off-leave-operations/1.1-outpatient-sick-time-hospitalization-leave-singapore.md"
    content = read_concept(concept_path)
    
    assert "=== POLICY CITATION: [1.1 Outpatient Sick Time & Hospitalization Leave (Singapore)]" in content
    assert "14 days of paid outpatient sick leave" in content
    assert "46 work days of paid hospitalization leave" in content


def test_read_concept_missing():
    """Test reading a non-existent concept document gracefully handles the error."""
    content = read_concept("non_existent_policy.md")
    assert "was not found" in content
    assert "list_concepts()" in content
