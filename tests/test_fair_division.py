import unittest
from app.core.fair_division import solve_fair_division_mixed

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
        self.assertAlmostEqual(sum(person1_divisible), 1.0, places=2)
        self.assertAlmostEqual(sum(person2_divisible), 1.0, places=2)

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

if __name__ == '__main__':
    unittest.main() 