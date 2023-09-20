from typing import Dict, List, Union, Any


__all__ = ['Report']

# type hints
Publication = Dict[str, Union[str, int]]
Component = Dict[str, Union[str, int, List[int]]]
SliceStatistics = Dict[str, Dict[str, Union[str, Any]]]


class Report():
    """This class maintains all operations with the PolyAnalyst's report.

    :param api: An instance of :class:`API <API>` class
    :param reportUUID: The uuid of the report you want to interact with
    """

    def __repr__(self):
        return f'<Report [{self.reportUUID}]>'

    def __init__(self, api, reportUUID: str):
        self.api = api
        self.reportUUID = reportUUID

    def publications(self) -> Publication:
        return self.api.get('report/publications', params={'reportUUID': self.reportUUID})

    def components(self) -> List[Component]:
        comps = self.api.get('report/components', params={'reportUUID': self.reportUUID})
        return comps

    def export_slice_statistics(self) -> SliceStatistics:
        slice_stats = self.api.get('report/slice-statistics/export', params={'reportUUID': self.reportUUID})
        return slice_stats

    def clear_slice_statistics(self) -> None:
        self.api.get('report/slice-statistics/clear', params={'reportUUID': self.reportUUID})

    def import_slice_statistics(self, slice_stats: SliceStatistics) -> None:
        self.api.post('report/slice-statistics/import',  slice_stats)
