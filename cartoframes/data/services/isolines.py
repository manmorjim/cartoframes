from __future__ import absolute_import

from .service import Service
from ...core.managers.source_manager import SourceManager
from ...io.carto import read_carto, to_carto, delete_table

QUOTA_SERVICE = 'isolines'
DATA_RANGE_KEY = 'data_range'
RANGE_LABEL_KEY = 'range_label'


class Isolines(Service):
    """Time and distance Isoline services using CARTO dataservices.
    """

    def __init__(self, credentials=None):
        super(Isolines, self).__init__(credentials, quota_service=QUOTA_SERVICE)

    def isochrones(self, source, ranges, **args):
        """isochrone areas

        This method computes areas delimited by isochrone lines (lines of constant travel time) based upon public roads.

        Args:
            source (str, DataFrame, GeoDataFrame, :py:class:`CartoDataFrame <cartoframes.CartoDataFrame>`):
                table, SQL query or DataFrame containing the source points for the isochrones: travel routes from the
                source points are computed to determine areas within specified travel times.
            ranges (list): travel time values in seconds; for each range value and source point a result polygon
                will be produced enclosing the area within range of the source.
            exclusive (bool, optional): when False, inclusive range areas are generated, each one
                containing the areas for smaller time values (so the area is reachable from the source
                whithin the given time). When True (the default), areas are exclusive, each one corresponding
                time values between the immediately smaller range value (or zero) and the area range value.
            table_name (str, optional): the resulting areas will be saved in a new
                CARTO table with this name.
            if_exists (str, optional): Behavior for creating new datasets, only applicable
                if table_name isn't None;
                Options are 'fail', 'replace', or 'append'. Defaults to 'fail'.
            dry_run (bool, optional): no actual computattion will be performed,
                and metadata will be returned including the required quota.
            mode (str, optional):  defines the travel mode: ``'car'`` (the default) or ``'walk'``.
            is_destination (bool, optional):  indicates that the source points are to be taken as
                destinations for the routes used to compute the area, rather than origins.
            mode_type (str, optional): type of routes computed: ``'shortest'`` (default) or ``'fastests'``.
            mode_traffic (str, optional): use traffic data to compute routes: ``'disabled'`` (default) or ``'enabled'``.
            resolution (float, optional): level of detail of the polygons in meters per pixel.
                Higher resolution may increase the response time of the service.
            maxpoints (int, optional): Allows to limit the amount of points in the returned polygons.
                Increasing the number of maxpoints may increase the response time of the service.
            quality: (int, optional): Allows you to reduce the quality of the polygons in favor of the response time.
                Admitted values: 1/2/3.
            geom_col (str, optional): string indicating the geometry column name in the source `DataFrame`.

        Returns:
            A named-tuple ``(data, metadata)`` containing a ``data`` :py:class:`CartoDataFrame
            <cartoframes.CartoDataFrame>` and a ``metadata`` dictionary. For dry runs the data will be ``None``.
            The data contains a ``range_data`` column with a numeric value and a ``the_geom``
            geometry with the corresponding area. It will also contain a ``source_id`` column
            that identifies the source point corresponding to each area if the source has a
            ``cartodb_id`` column.
        """
        return self._iso_areas(source, ranges, function='isochrone', **args)

    def isodistances(self, source, ranges, **args):
        """isodistance areas

        This method computes areas delimited by isodistance lines (lines of constant travel distance) based upon public
        roads.

        Args:
            source (str, DataFrame, GeoDataFrame, :py:class:`CartoDataFrame <cartoframes.CartoDataFrame>`):
                table, SQL query or DataFrame containing the source points for the isodistances: travel routes from the
                source points are computed to determine areas within specified travel distances.
            ranges (list): travel distance values in meters; for each range value and source point a result polygon
                will be produced enclosing the area within range of the source.
            exclusive (bool, optional): when False, inclusive range areas are generated, each one
                containing the areas for smaller distance values (so the area is reachable from the source
                whithin the given distance). When True, areas are exclusive (the default), each one corresponding
                distance values between the immediately smaller range value (or zero) and the area range value.
            table_name (str, optional): the resulting areas will be saved in a new
                CARTO table with this name.
            if_exists (str, optional): Behavior for creating new datasets, only applicable
                if table_name isn't None;
                Options are 'fail', 'replace', or 'append'. Defaults to 'fail'.
            dry_run (bool, optional): no actual computattion will be performed,
                and metadata will be returned including the required quota.
            mode (str, optional):  defines the travel mode: ``'car'`` (the default) or ``'walk'``.
            is_destination (bool, optional):  indicates that the source points are to be taken as
                destinations for the routes used to compute the area, rather than origins.
            mode_type (str, optional): type of routes computed: ``'shortest'`` (default) or ``'fastests'``.
            mode_traffic (str, optional): use traffic data to compute routes: ``'disabled'`` (default) or ``'enabled'``.
            resolution (float, optional): level of detail of the polygons in meters per pixel.
                Higher resolution may increase the response time of the service.
            maxpoints (int, optional): Allows to limit the amount of points in the returned polygons.
                Increasing the number of maxpoints may increase the response time of the service.
            quality: (int, optional): Allows you to reduce the quality of the polygons in favor of the response time.
                Admitted values: 1/2/3.
            geom_col (str, optional): string indicating the geometry column name in the source `DataFrame`.

        Returns:
            A named-tuple ``(data, metadata)`` containing a ``data`` :py:class:`CartoDataFrame
            <cartoframes.CartoDataFrame>` and a ``metadata`` dictionary. For dry runs the data will be ``None``.
            The data contains a ``range_data`` column with a numeric value and a ``the_geom``
            geometry with the corresponding area. It will also contain a ``source_id`` column
            that identifies the source point corresponding to each area if the source has a
            ``cartodb_id`` column.
        """
        return self._iso_areas(source, ranges, function='isodistance', **args)

    def _iso_areas(self,
                   source,
                   ranges,
                   dry_run=False,
                   table_name=None,
                   if_exists=None,
                   is_destination=None,
                   mode='car',
                   mode_type=None,
                   mode_traffic=None,
                   resolution=None,
                   maxpoints=None,
                   quality=None,
                   exclusive=True,
                   function=None,
                   geom_col=None):
        metadata = {}

        source_manager = SourceManager(source, self._credentials)

        num_rows = source_manager.get_num_rows()
        metadata['required_quota'] = num_rows * len(ranges)

        if dry_run:
            return self.result(data=None, metadata=metadata)

        if source_manager.is_remote():
            temporary_table_name = False
            source_query = source_manager.get_query()
        else:
            # upload to temporary table
            temporary_table_name = self._new_temporary_table_name()
            source_cdf = source_manager.cdf

            if geom_col:
                source_cdf.set_geometry(geom_col, inplace=True)

            if not source_cdf.has_geometry():
                raise Exception('No valid geometry found. Please provide an input source with ' +
                                'a valid geometry or specify the "geom_col" param with a geometry column.')

            to_carto(source_cdf, temporary_table_name, self._credentials, log_enabled=False)
            source_query = 'SELECT * FROM {table}'.format(table=temporary_table_name)

        source_columns = source_manager.get_column_names()
        source_has_id = 'cartodb_id' in source_columns

        iso_function = '_cdb_{function}_exception_safe'.format(function=function)
        # TODO: use **options argument?
        options = {
            'is_destination': is_destination,
            'mode_type': mode_type,
            'mode_traffic': mode_traffic,
            'resolution': resolution,
            'maxpoints': maxpoints,
            'quality': quality
        }
        iso_options = ["'{}={}'".format(k, v) for k, v in options.items() if v is not None]
        iso_options = "ARRAY[{opts}]".format(opts=','.join(iso_options))
        iso_ranges = 'ARRAY[{ranges}]'.format(ranges=','.join([str(r) for r in ranges]))

        sql = _areas_query(
            source_query, source_columns, iso_function, mode, iso_ranges, iso_options, source_has_id or exclusive)
        if exclusive:
            sql = _rings_query(sql, source_has_id)

        # Execute and download the query to generate the isolines
        cdf = read_carto(sql, self._credentials)

        if exclusive:
            # Add range label column
            cdf[RANGE_LABEL_KEY] = cdf.apply(lambda r: '%.0f min.' % (r[DATA_RANGE_KEY]/60), axis=1)

        if table_name:
            # save result in a table
            to_carto(cdf, table_name, self._credentials, if_exists, log_enabled=dry_run)

        if temporary_table_name:
            delete_table(temporary_table_name, self._credentials, log_enabled=False)

        result = self.result(data=cdf, metadata=metadata)

        print('Success! Isolines created correctly')

        return result


def _areas_query(source_query, source_columns, iso_function, mode, iso_ranges, iso_options, with_source_id):
    select_source_id = 'source_id,' if with_source_id else ''
    source_id = ''
    if with_source_id:
        if 'cartodb_id' in source_columns:
            source_id = '_source.cartodb_id AS source_id,'
        else:
            source_id = 'row_number() over () AS source_id,'

    return """
        WITH _source AS ({source_query}),
        _iso_areas AS (
            SELECT
              {source_id}
              {iso_function}(
                  _source.the_geom,
                  '{mode}',
                  {iso_ranges}::integer[],
                  {iso_options}::text[]
              ) AS _area
            FROM _source
        )
        SELECT
          row_number() OVER () AS cartodb_id,
          {select_source_id}
          (_area).data_range,
          (_area).the_geom
        FROM _iso_areas
    """.format(
        iso_function=iso_function,
        source_query=source_query,
        source_id=source_id,
        select_source_id=select_source_id,
        mode=mode,
        iso_ranges=iso_ranges,
        iso_options=iso_options
    )


def _rings_query(areas_query, with_source_id):
    if with_source_id:
        select_source_id = 'source_id,'
    else:
        select_source_id = 'row_number() OVER () AS source_id,'

    return """
        SELECT
            cartodb_id,
            {select_source_id}
            data_range,
            COALESCE(
              LAG(data_range, 1) OVER (PARTITION BY source_id ORDER BY data_range),
              0
            ) AS lower_data_range,
            COALESCE(
              ST_DIFFERENCE(the_geom, LAG(the_geom, 1) OVER (PARTITION BY source_id ORDER BY data_range)),
              the_geom
            ) AS the_geom
        FROM ({areas_query}) _areas_query
    """.format(
        select_source_id=select_source_id,
        areas_query=areas_query
    )
