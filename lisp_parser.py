import csv
import re
import sys
import unittest
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import Optional

def _parse_value(value: str) -> Any:
    if value == "nil":

        return None

    try:
        n = int(value)

        return n

    except ValueError:
        pass

    list_data = next(csv.reader([value[1:-2]], delimiter=' ', quotechar='"'))

    return list_data


def parse(input: str) -> Any:
    result = re.match('^\(:outline (?P<outline>.+?)(?: :content (?P<content>.*))? :point (?P<point>nil|\d+)\)$', input)
    #print(result)
    if result:
        return {
            'outline': _parse_value(result['outline']),
            'point': _parse_value(result['point']),
        }


def main() -> None:
    print(sys.argv)


if __name__ == "__main__":
    main()


class TestParse(unittest.TestCase):
    def test_all_nil_should_return_nones(self):
        # Given
        input: str = '(:outline nil :point nil)'

        # When
        result: Any = parse(input)

        # Then
        expected = {
            'outline': None,
            'point': None,
        }
        self.assertEqual(expected, result)

    def test_given_point_should_return_none_and_number(self):
        # Given
        input: str = '(:outline nil :point 42)'

        # When
        result: Any = parse(input)

        # Then
        expected = {
            'outline': None,
            'point': 42,
        }
        self.assertEqual(expected, result)

    def test_given_outline_should_return_list_and_none(self):
        # Given
        input: str = '(:outline ("foo") :point nil)'

        # When
        result: Any = parse(input)

        # Then
        expected = {
            'outline': ["foo"],
            'point': None,
        }
        self.assertEqual(expected, result)

    def test_given_content_should_return_list_and_number(self):
        # Given
        input: str = '(:outline ("foo" "bar" "plopp ploop") :content "apa bepa" :point 312)'

        # When
        result: Any = parse(input)

        # Then
        expected = {
            'outline': ["foo", "bar", "plopp ploop"],
            'point': 312,
        }
        self.assertEqual(expected, result)

    def test_given_normal_data_should_return_list_and_number(self):
        # Given
        input: str = '(:outline ("foo" "bar" "plopp ploop") :point 312)'

        # When
        result: Any = parse(input)

        # Then
        expected = {
            'outline': ["foo", "bar", "plopp ploop"],
            'point': 312,
        }
        self.assertEqual(expected, result)
