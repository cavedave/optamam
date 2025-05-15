import unittest
from app.core.fair_division import solve_fair_division_mixed
import pytest
from app.core.fair_division import calculate_fair_division

class TestFairDivision(unittest.TestCase):
    def test_only_divisible_items(self):
        """Test case with only divisible items"""
        # Two people, two divisible items
        divisible_matrix = [
            [10, 20],  # Person 1 values: item1=10, item2=20
            [20, 10]   # Person 2 values: item1=20, item2=10
        ]
        indivisible_matrix = []
        
        allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix)
        
        self.assertIsNotNone(allocation)
        self.assertIsNotNone(worst_val)
        
        # Check that each person gets a fair share
        person1_divisible = allocation[0]['divisible']
        person2_divisible = allocation[1]['divisible']
        
        # Total allocation should be 1.0 for each item
        for i in range(len(person1_divisible)):
            total = person1_divisible[i] + person2_divisible[i]
            self.assertAlmostEqual(total, 1.0, places=2)

    def test_only_indivisible_items(self):
        """Test case with only indivisible items"""
        # Two people, two indivisible items
        indivisible_matrix = [
            [10, 20],  # Person 1 values: item1=10, item2=20
            [20, 10]   # Person 2 values: item1=20, item2=10
        ]
        divisible_matrix = []
        
        allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix)
        
        self.assertIsNotNone(allocation)
        self.assertIsNotNone(worst_val)
        
        # Check that each item is assigned to exactly one person
        person1_indivisible = allocation[0]['indivisible']
        person2_indivisible = allocation[1]['indivisible']
        
        # Each item should be assigned to exactly one person
        self.assertEqual(sum(person1_indivisible), 1)
        self.assertEqual(sum(person2_indivisible), 1)

    def test_mixed_items(self):
        """Test case with both divisible and indivisible items"""
        # Two people, one divisible item and one indivisible item
        divisible_matrix = [
            [10],  # Person 1 values divisible item at 10
            [20]   # Person 2 values divisible item at 20
        ]
        indivisible_matrix = [
            [20],  # Person 1 values indivisible item at 20
            [10]   # Person 2 values indivisible item at 10
        ]
        
        allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix)
        
        self.assertIsNotNone(allocation)
        self.assertIsNotNone(worst_val)
        
        # Check allocations
        person1_divisible = allocation[0]['divisible']
        person2_divisible = allocation[1]['divisible']
        person1_indivisible = allocation[0]['indivisible']
        person2_indivisible = allocation[1]['indivisible']
        
        # Divisible item should be fully allocated between both people
        total_divisible = person1_divisible[0] + person2_divisible[0]
        self.assertAlmostEqual(total_divisible, 1.0, places=2)
        
        # Indivisible item should be assigned to exactly one person
        total_indivisible = person1_indivisible[0] + person2_indivisible[0]
        self.assertEqual(total_indivisible, 1)

    def test_equal_valuations(self):
        """Test case where all people value items equally"""
        divisible_matrix = [
            [10, 10],  # Person 1 values both items at 10
            [10, 10]   # Person 2 values both items at 10
        ]
        indivisible_matrix = [
            [10, 10],  # Person 1 values both items at 10
            [10, 10]   # Person 2 values both items at 10
        ]
        
        allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix)
        
        self.assertIsNotNone(allocation)
        self.assertIsNotNone(worst_val)
        
        # Check that allocations are fair
        person1_divisible = allocation[0]['divisible']
        person2_divisible = allocation[1]['divisible']
        
        # With equal valuations, should get roughly equal shares
        # Check total allocation for each item
        for i in range(len(person1_divisible)):
            total = person1_divisible[i] + person2_divisible[i]
            self.assertAlmostEqual(total, 1.0, places=2)

    def test_empty_input(self):
        """Test case with empty input"""
        allocation, worst_val = solve_fair_division_mixed([], [])
        self.assertIsNone(allocation)
        self.assertIsNone(worst_val)

    def test_large_scale(self):
        """Test case with many people and items"""
        # Three people, three divisible items, three indivisible items
        divisible_matrix = [
            [10, 20, 30],  # Person 1
            [20, 30, 10],  # Person 2
            [30, 10, 20]   # Person 3
        ]
        indivisible_matrix = [
            [10, 20, 30],  # Person 1
            [20, 30, 10],  # Person 2
            [30, 10, 20]   # Person 3
        ]
        
        allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix)
        
        self.assertIsNotNone(allocation)
        self.assertIsNotNone(worst_val)
        
        # Check allocations for each item
        for i in range(3):
            # Check divisible items
            total_divisible = sum(allocation[j]['divisible'][i] for j in range(3))
            self.assertAlmostEqual(total_divisible, 1.0, places=2)
            
            # Check indivisible items
            total_indivisible = sum(allocation[j]['indivisible'][i] for j in range(3))
            self.assertEqual(total_indivisible, 1)

def test_break_up_scenario():
    """Test fair division in a break-up scenario with mixed divisible and indivisible items."""
    # Test data
    items = [
        {"name": "Car", "is_divisible": False},
        {"name": "Cash", "is_divisible": True},
        {"name": "Cat", "is_divisible": False},
        {"name": "Air Fryer", "is_divisible": False},
        {"name": "Games Computer", "is_divisible": False},
        {"name": "Washing Machine", "is_divisible": False},
        {"name": "Painting", "is_divisible": False},
        {"name": "TV", "is_divisible": False}
    ]
    
    people = ["Alex", "Bob"]
    
    # Create valuations dictionary in the correct format
    valuations = {
        "Car": {"Alex": 10, "Bob": 32},
        "Cash": {"Alex": 15, "Bob": 8},
        "Cat": {"Alex": 30, "Bob": 10},
        "Air Fryer": {"Alex": 5, "Bob": 5},
        "Games Computer": {"Alex": 8, "Bob": 20},
        "Washing Machine": {"Alex": 12, "Bob": 8},
        "Painting": {"Alex": 15, "Bob": 5},
        "TV": {"Alex": 5, "Bob": 12}
    }
    
    # Calculate fair division
    result = calculate_fair_division(items, people, valuations)
    
    # Verify the result structure
    assert "allocations" in result
    assert "worst_satisfaction" in result
    
    # Verify allocations
    allocations = result["allocations"]
    assert len(allocations) == len(people)
    
    # Verify that each person gets at least one item
    for person in people:
        assert person in allocations
        person_alloc = allocations[person]
        assert len(person_alloc["indivisible"]) > 0 or len(person_alloc["divisible"]) > 0
    
    # Verify that Cash (divisible item) is properly allocated
    cash_allocated = False
    for person in people:
        if "Cash" in allocations[person]["divisible"]:
            cash_allocated = True
            break
    assert cash_allocated, "Cash should be allocated to someone"
    
    # Verify that the worst satisfaction is reasonable (should be at least 50%)
    assert result["worst_satisfaction"] >= 50.0

# New test function for Clare and Dave scenario
def test_clare_dave_scenario():
    """Test fair division where Clare values the car at 100 and Dave values the cat at 100."""
    items = [
        {"name": "Car", "is_divisible": False},
        {"name": "Cat", "is_divisible": False}
    ]
    people = ["Clare", "Dave"]
    valuations = {
        "Car": {"Clare": 100, "Dave": 0},
        "Cat": {"Clare": 0, "Dave": 100},
    }
    result = calculate_fair_division(items, people, valuations)
    print("Allocations:")
    for person in people:
        print(f"{person} receives:")
        if "indivisible" in result["allocations"][person]:
            print(f"  Indivisible: {result['allocations'][person]['indivisible']}")
        if "divisible" in result["allocations"][person]:
            print(f"  Divisible: {result['allocations'][person]['divisible']}")
    print(f"Worst satisfaction: {result['worst_satisfaction']}%")
    assert result["worst_satisfaction"] == 100.0, "Each person should get 100% satisfaction"
    assert "Car" in result["allocations"]["Clare"]["indivisible"], "Clare should get the car"
    assert "Cat" in result["allocations"]["Dave"]["indivisible"], "Dave should get the cat"

def test_clare_dave_with_cash():
    """Test fair division where Clare and Dave both value cash at 20 and their preferred item at 80."""
    items = [
        {"name": "Car", "is_divisible": False},
        {"name": "Cat", "is_divisible": False},
        {"name": "Cash", "is_divisible": True}
    ]
    people = ["Clare", "Dave"]
    valuations = {
        "Car": {"Clare": 80, "Dave": 0},
        "Cat": {"Clare": 0, "Dave": 80},
        "Cash": {"Clare": 20, "Dave": 20}
    }
    result = calculate_fair_division(items, people, valuations)
    assert result["worst_satisfaction"] == 90.0, "Each person should get 90% satisfaction"
    # Each should get their preferred indivisible item
    assert "Car" in result["allocations"]["Clare"]["indivisible"], "Clare should get the car"
    assert "Cat" in result["allocations"]["Dave"]["indivisible"], "Dave should get the cat"
    # Each should get half the cash
    #assert abs(result["allocations"]["Clare"]["divisible"]["Cash"] - 0.5) < 1e-6, "Clare should get half the cash"
    #assert abs(result["allocations"]["Dave"]["divisible"]["Cash"] - 0.5) < 1e-6, "Dave should get half the cash"

if __name__ == '__main__':
    unittest.main() 