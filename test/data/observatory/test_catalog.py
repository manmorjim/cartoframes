import unittest

from cartoframes.data.observatory.geography import Geography
from cartoframes.data.observatory.country import Country
from cartoframes.data.observatory.category import Category
from cartoframes.data.observatory.dataset import Dataset
from cartoframes.data.observatory.catalog import Catalog
from .examples import test_country2, test_country1, test_category1, test_category2, test_dataset1, test_dataset2, \
    test_geographies, test_datasets, test_categories, test_countries

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


class TestCatalog(unittest.TestCase):

    @patch.object(Country, 'get_all')
    def test_countries(self, mocked_countries):
        # Given
        expected_countries = [test_country1, test_country2]
        mocked_countries.return_value = expected_countries
        catalog = Catalog()

        # When
        countries = catalog.countries

        # Then
        assert countries == expected_countries

    @patch.object(Category, 'get_all')
    def test_categories(self, mocked_categories):
        # Given
        expected_categories = [test_category1, test_category2]
        mocked_categories.return_value = expected_categories
        catalog = Catalog()

        # When
        categories = catalog.categories

        # Then
        assert categories == expected_categories

    @patch.object(Dataset, 'get_all')
    def test_datasets(self, mocked_datasets):
        # Given
        expected_datasets = [test_dataset1, test_dataset2]
        mocked_datasets.return_value = expected_datasets
        catalog = Catalog()

        # When
        datasets = catalog.datasets

        # Then
        assert datasets == expected_datasets

    @patch.object(Country, 'get_all')
    def test_filters_on_countries(self, mocked_countries):
        # Given
        mocked_countries.return_value = test_countries
        catalog = Catalog()

        # When
        countries = catalog.category('demographics').countries

        # Then
        mocked_countries.called_once_with({'category_id': 'demographics'})
        assert countries == test_countries

    @patch.object(Category, 'get_all')
    def test_filters_on_categories(self, mocked_categories):
        # Given
        mocked_categories.return_value = test_categories
        catalog = Catalog()

        # When
        categories = catalog.country('usa').categories

        # Then
        mocked_categories.called_once_with({'country_id': 'usa'})
        assert categories == test_categories

    @patch.object(Dataset, 'get_all')
    def test_filters_on_datasets(self, mocked_datasets):
        # Given
        mocked_datasets.return_value = test_datasets
        catalog = Catalog()

        # When
        datasets = catalog.country('usa').category('demographics').datasets

        # Then
        mocked_datasets.called_once_with({'country_id': 'usa', 'category_id': 'demographics'})
        assert datasets == test_datasets

    @patch.object(Geography, 'get_all')
    def test_filters_on_geographies(self, mocked_geographies):
        # Given
        mocked_geographies.return_value = test_geographies
        catalog = Catalog()

        # When
        geographies = catalog.country('usa').category('demographics').geographies

        # Then
        mocked_geographies.called_once_with({'country_id': 'usa', 'category_id': 'demographics'})
        assert geographies == test_geographies
