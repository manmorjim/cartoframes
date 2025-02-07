from __future__ import absolute_import

import pandas as pd
import geopandas as gpd

from shapely import wkt

from carto.exceptions import CartoException

from .entity import CatalogEntity
from .repository.dataset_repo import get_dataset_repo
from .repository.geography_repo import get_geography_repo
from .repository.variable_repo import get_variable_repo
from .repository.variable_group_repo import get_variable_group_repo
from .repository.constants import DATASET_FILTER
from .summary import dataset_describe, head, tail, counts, fields_by_type, geom_coverage
from . import subscription_info
from . import subscriptions
from . import utils
from ....auth import Credentials, defaults

DATASET_TYPE = 'dataset'


class Dataset(CatalogEntity):
    """A Dataset represents the metadata of a particular dataset in the catalog.

    If you have Data Observatory enabled in your CARTO account you can:

      - Use any public dataset to enrich your data with the variables in it by means of the :obj:`Enrichment`
        functions.
      - Subscribe (:py:attr:`Dataset.subscribe`) to any premium dataset, to get a license, that grants you
        the right to enrich your data with the variables (:obj:`Variable`) in it.

    See the enrichment guides for more information about datasets, variables and
    enrichment functions.

    The metadata of a dataset allows you to understand the underlying data,
    from variables (the actual columns in the dataset, data types, etc.), to a
    description of the provider, source, country, geography available, etc.

    See the attributes reference in this class to understand the metadata available
    for each dataset in the catalog.

    Examples:
        There are many different ways to explore the available datasets in the
        catalog.

        You can just list all the available datasets:

        .. code::

            from cartoframes.data.observatory import Catalog

            catalog = Catalog()
            datasets = catalog.datasets

        Since the catalog contains thousands of datasets, you can convert the
        list of `datasets` to a pandas DataFrame for further filtering:

        .. code::

            from cartoframes.data.observatory import Catalog

            catalog = Catalog()
            dataframe = catalog.datasets.to_dataframe()

        The catalog supports nested filters for a hierarchical exploration.
        This way you could list the datasets available for different hierarchies:
        country, provider, category, geography or a combination of them.

        .. code::

            from cartoframes.data.observatory import Catalog

            catalog = Catalog()
            catalog.country('usa').category('demographics').geography('ags_blockgroup_1c63771c').datasets

    """

    _entity_repo = get_dataset_repo()

    @property
    def variables(self):
        """Get the list of :obj:`Variable` that corresponds to this dataset. Variables are used in the
        :obj:`Enrichment` functions to augment your local `DataFrames` with columns from a `Dataset` in the
        Data Observatory.

        Returns:
            :py:class:`CatalogList <cartoframes.data.observatory.entity.CatalogList>` List of Variable instances.

        :raises CartoException: If there's a problem when connecting to the catalog.
        """

        return get_variable_repo().get_all({DATASET_FILTER: self.id})

    @property
    def variables_groups(self):
        """Get the list of :obj:`VariableGroup` related to this dataset.

        Returns:
            :py:class:`CatalogList <cartoframes.data.observatory.entity.CatalogList>` List of VariableGroup instances.

        :raises CartoException: If there's a problem when connecting to the catalog.
        """
        return get_variable_group_repo().get_all({DATASET_FILTER: self.id})

    @property
    def name(self):
        """Name of this dataset."""

        return self.data['name']

    @property
    def description(self):
        """Description of this dataset."""

        return self.data['description']

    @property
    def provider(self):
        """Id of the :obj:`Provider` of this dataset.
        """

        return self.data['provider_id']

    @property
    def provider_name(self):
        """Name of the :obj:`Provider` of this dataset."""

        return self.data['provider_name']

    @property
    def category(self):
        """Get the :obj:`Category` ID assigned to this dataset.sets
        """

        return self.data['category_id']

    @property
    def category_name(self):
        """Name of the :obj:`Category` assigned to this dataset."""

        return self.data['category_name']

    @property
    def data_source(self):
        """Id of the data source of this dataset."""

        return self.data['data_source_id']

    @property
    def country(self):
        """ISO 3166-1 alpha-3 code of the :obj:`Country`
        of this dataset.
        """

        return self.data['country_id']

    @property
    def language(self):
        """ISO 639-3 code of the language that corresponds to the data
        of this dataset.
        """

        return self.data['lang']

    @property
    def geography(self):
        """Get the :obj:`Geography` ID associated to this dataset."""

        return self.data['geography_id']

    @property
    def geography_name(self):
        """Get the name of the :obj:`Geography` associated to this dataset."""

        return self.data['geography_name']

    @property
    def geography_description(self):
        """Description of the :obj:`Geography` associated to this dataset."""

        return self.data['geography_description']

    @property
    def temporal_aggregation(self):
        """Time amount in which data is aggregated in this dataset.

        This is a free text field in this form: seconds, daily, hourly, monthly, yearly, etc.
        """

        return self.data['temporal_aggregation']

    @property
    def time_coverage(self):
        """Time range that covers the data of this dataset.

        Returns:
            List of str

        Example: [2015-01-01,2016-01-01)

        """

        return self.data['time_coverage']

    @property
    def update_frequency(self):
        """Frequency in which the dataset is updated.

        Returns:
            str

        Example: monthly, yearly, etc.
        """

        return self.data['update_frequency']

    @property
    def version(self):
        """Internal version info of this dataset.

        Returns:
            str
        """

        return self.data['version']

    @property
    def is_public_data(self):
        """Allows to check if the content of this dataset can be accessed with
        public credentials or if it is a premium dataset that needs a
        subscription.

        Returns:
            A boolean value:
                * ``True`` if the dataset is public
                * ``False`` if the dataset is premium
                    (it requires to :py:attr:`Dataset.subscribe`)
        """

        return self.data['is_public_data']

    @property
    def summary(self):
        """JSON object with extra metadata that summarizes different properties of the dataset content."""

        return self.data['summary_json']

    def head(self):
        """Returns a sample of the 10 first rows of the dataset data.

        If a dataset has fewer than 10 rows (e.g., zip codes of small countries), this method will return None

        Returns:
            pandas.DataFrame
        """

        data = self.data['summary_json']
        return head(self.__class__, data)

    def tail(self):
        """"Returns the last ten rows of the dataset"

        If a dataset has fewer than 10 rows (e.g., zip codes of small countries), this method will return None

        Returns:
            pandas.DataFrame
        """
        data = self.data['summary_json']
        return tail(self.__class__, data)

    def counts(self):
        """Returns a summary of different counts over the actual dataset data.

        Returns:
            pandas.Series

        Example:

            .. code::

                # rows:         number of rows in the dataset
                # cells:        number of cells in the dataset (rows * columns)
                # null_cells:   number of cells with null value in the dataset
                # null_cells_percent:   percent of cells with null value in the dataset
        """

        data = self.data['summary_json']
        return counts(data)

    def fields_by_type(self):
        """Returns a summary of the number of columns per data type in the dataset.

        Returns:
            pandas.Series

        Example:

            .. code::

                # float        number of columns with type float in the dataset
                # string       number of columns with type string in the dataset
                # integer      number of columns with type integer in the dataset
        """
        data = self.data['summary_json']
        return fields_by_type(data)

    def geom_coverage(self):
        """Shows a map to visualize the geographical coverage of the dataset.

        Returns:
            cartoframes.viz.Map
        """
        return geom_coverage(self.geography)

    def describe(self):
        """Shows a summary of the actual stats of the variables (columns) of the dataset.
        Some of the stats provided per variable are: avg, max, min, sum, range,
        stdev, q1, q3, median and interquartile_range

        Returns:
            pandas.DataFrame

        Example:

            .. code::

                # avg                    average value
                # max                    max value
                # min                    min value
                # sum                    sum of all values
                # range
                # stdev                  standard deviation
                # q1                     first quantile
                # q3                     third quantile
                # median                 median value
                # interquartile_range
        """
        return dataset_describe(self.variables)

    @classmethod
    def get_all(cls, filters=None, credentials=None):
        """Get all the Dataset instances that comply with the indicated filters (or all of them if no filters
        are passed). If credentials are given, only the datasets granted for those credentials are returned.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If provided, only datasets granted for those credentials are
                returned.

            filters (dict, optional):
                Dict containing pairs of dataset properties and its value to be used as filters to query the available
                datasets. If none is provided, no filters will be applied to the query.

        Returns:
            :py:class:`CatalogList <cartoframes.data.observatory.entity.CatalogList>` List of Dataset instances.

        :raises DiscoveryException: When no datasets are found.
        :raises CartoException: If there's a problem when connecting to the catalog.
        """

        return cls._entity_repo.get_all(filters, credentials)

    def download(self, credentials=None):
        """Download dataset data as a local file. You need Data Observatory enabled in your CARTO
        account, please contact us at support@carto.com for more information.

        For premium geographies (those with `is_public_data` set to False), you need a subscription to the geography.
        Check the subscription guides for more information.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If not provided,
                a default credentials (if set with :py:meth:`set_default_credentials
                <cartoframes.auth.set_default_credentials>`) will be used.

        Returns:
            os.path with the local file path with the file downloaded

        :raises CartoException: If you have not a valid license for the dataset being downloaded.
        :raises ValueError: If the credentials argument is not valud.
        """
        if not self._is_subscribed(credentials):
            raise CartoException('You are not subscribed to this Dataset yet. Please, use the subscribe method first.')

        return self._download(credentials)

    @classmethod
    def get_datasets_spatial_filtered(cls, filter_dataset):
        user_gdf = cls._get_user_geodataframe(filter_dataset)

        # TODO: check if the dataframe has a geometry column if not exception
        # Saving memory
        user_gdf = user_gdf[[user_gdf.geometry.name]]
        catalog_geographies_gdf = get_geography_repo().get_geographies_gdf()
        matched_geographies_ids = cls._join_geographies_geodataframes(catalog_geographies_gdf, user_gdf)

        # Get Dataset objects
        return get_dataset_repo().get_all({'geography_id': list(matched_geographies_ids)})

    @staticmethod
    def _get_user_geodataframe(filter_dataset):
        if isinstance(filter_dataset, gpd.GeoDataFrame):
            # Geopandas dataframe
            return filter_dataset

        if isinstance(filter_dataset, str):
            # String WKT
            df = pd.DataFrame([{'geometry': filter_dataset}])
            df['geometry'] = df['geometry'].apply(wkt.loads)
            return gpd.GeoDataFrame(df)

    @staticmethod
    def _join_geographies_geodataframes(geographies_gdf1, geographies_gdf2):
        join_gdf = gpd.sjoin(geographies_gdf1, geographies_gdf2, how='inner', op='intersects')
        return join_gdf['id'].unique()

    def subscribe(self, credentials=None):
        """Subscribe to a dataset. You need Data Observatory enabled in your CARTO account, please contact us at
        support@carto.com for more information.

        Datasets with `is_public_data` set to True do not need a license (i.e., a subscription) to be used.
        Datasets with `is_public_data` set to False do need a license (i.e., a subscription) to be used. You'll get a
        license to use this `dataset` depending on the `estimated_delivery_days` set for this specific dataset.

        See :py:meth:`subscription_info <cartoframes.data.observatory.Dataset.subscription_info>` for more
        info

        Once you subscribe to a dataset, you can :py:attr:`Dataset.download` its data and use the
        :obj:`Enrichment` functions. See the enrichment guides for more info.

        You can check the status of your subscriptions by calling the
        :py:meth:`subscriptions <cartoframes.data.observatory.Catalog.subscriptions>` method in the :obj:`Catalog` with
        your CARTO :obj:`Credentials`.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If not provided,
                a default credentials (if set with :py:meth:`set_default_credentials
                <cartoframes.auth.set_default_credentials>`) will be used.

        :raises CartoException: If there's a problem when connecting to the catalog.
        """

        _credentials = self._get_credentials(credentials)
        _subscribed_ids = subscriptions.get_subscription_ids(_credentials)

        if self.id in _subscribed_ids:
            utils.display_existing_subscription_message(self.id, DATASET_TYPE)
        else:
            utils.display_subscription_form(self.id, DATASET_TYPE, _credentials)

    def subscription_info(self, credentials=None):
        """Get the subscription information of a Dataset, which includes the license, Terms of Service, rights, price, and
        estimated time of delivery, among other metadata of interest during the :py:attr:`Dataset.subscription` process.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If not provided,
                a default credentials (if set with :py:meth:`set_default_credentials
                <cartoframes.auth.set_default_credentials>`) will be used.

        Returns:
            :py:class:`SubscriptionInfo <cartoframes.data.observatory.SubscriptionInfo>` SubscriptionInfo instance.

        :raises CartoException: If there's a problem when connecting to the catalog.
        """

        _credentials = self._get_credentials(credentials)

        return subscription_info.SubscriptionInfo(
            subscription_info.fetch_subscription_info(self.id, DATASET_TYPE, _credentials))

    def _is_subscribed(self, credentials=None):
        if self.is_public_data:
            return True

        _credentials = credentials or defaults.get_default_credentials()

        if not isinstance(_credentials, Credentials):
            raise ValueError('`credentials` must be a Credentials class instance')

        datasets = Dataset.get_all({}, _credentials)

        return self in datasets
