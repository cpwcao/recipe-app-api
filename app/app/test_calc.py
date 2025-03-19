"""Test for the calc module"""


from django.test import SimpleTestCase

from . import calc


class CalcTests(SimpleTestCase):
   
    def test_add_numbers(self):
        res = calc.add(5, 6)    
        self.assertEqual(res, 11)

    def test_subtract_numbers(self):
        res = calc.subtract(10, 15)
        self.assertEqual(res, -5)

    def test_multiply_numbers(self):
        res = calc.multiply(5, 6)
        self.assertEqual(res, 30)

    def test_divide_numbers(self):
        res = calc.divide(10, 2)
        self.assertEqual(res, 5)
