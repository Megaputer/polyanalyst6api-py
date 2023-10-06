from typing import Dict, List, Union, Any


__all__ = ['Report']

# type hints
Publication = Dict[str, Union[str, int]]
Component = Dict[str, Union[str, int, List[int]]]
SliceStatistics = Dict[str, Dict[str, Union[str, Any]]]


class Report:
    """This class maintains all operations with the PolyAnalyst's report.

    :param api: An instance of :class:`API <API>` class
    :param uuid: The uuid of the report you want to interact with

    .. versionadded:: 0.30.0
    """

    def __repr__(self):
        return f'<Report [{self.uuid}]>'

    def __init__(self, api, uuid: str):
        self.api = api
        self.uuid = uuid

    def publications(self) -> List[Publication]:
        """Return publications list info."""
        return self.api.get('report/publications', params={'reportUUID': self.uuid})

    def components(self) -> List[Component]:
        """Return components list info."""
        return self.api.get('report/components', params={'reportUUID': self.uuid})

    def get_slice_statistics(self) -> SliceStatistics:
        """
        Get slice statistics.

        :return: Slice statistics
        """
        return self.api.get('report/slice-statistics/export', params={'reportUUID': self.uuid})

    def import_slice_statistics(self, slice_stats: SliceStatistics) -> None:
        """
        Import slice statistics.

        :param slice_stats: Slice statistics
        """
        self.api.post('report/slice-statistics/import',  params={'reportUUID': self.uuid}, json=slice_stats)
