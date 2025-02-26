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

    def clear_slice_statistics(self) -> None:
        """This operation clears statistics of slices"""
        self.api.post('report/slice-statistics/clear', json={'reportUUID': self.uuid})

    def sheets(self) -> List[Dict]:
        """This operation returns a list of sheets of a web report"""
        return self.api.get('report/sheets', params={'reportUUID': self.uuid})
    
    def sharing(self, locale: str) -> None:
        """This operation shares a publication and provides a guest access to the shared publication
        
        param locale: locale of the publication

        raises: ValueError if locale is not set
        """
        loc = ["end", "esp", "fra", "cht", "chs", "kor", "rus"]
        if locale not in loc:
            raise ValueError('The following locale types are supported: end, esp, fra, cht, chs, kor, rus')
        self.api.post('report/share', json={'reportUUID': self.uuid, 'locale': locale})

    def stop_sharing(self) -> None:
        """This operation stops publication sharing if there is a shared publication
        
        raises: APIException if there is not a shared publication
        """
        self.api.post('report/stop-sharing', json={'reportUUID': self.uuid})

    def get_reports(self) -> List[Dict]:
        """This operation returns a list of web reports"""
        return self.api.get('reports')
    
    def report_rename(self, name: str, description: str = "") -> None:
        """This operation allows users to rename a report and give it a new description
        
        param name: parameter must contain a new name of the report
        param description: set a new description
        """
        self.api.post('report/rename', json={'reportUUID': self.uuid, 'name': name, 'description': description})

    def report_move(self, ids: list, folder_path: str = "") -> None:
        """This operation moves a report to a specified folder
        
        param ids: the ids is an array of strings where reportUUID are specified
        param folder_path: the folderPath parameter is a folder where a report is moved
        """
        self.api.post('report/move', json={'ids': ids, 'folderPath': folder_path})

    def report_info(self) -> Dict:
        """This operation returns information about a report"""
        return self.api.get('report/info', params={'reportUUID': self.uuid})
    
    def wrapper_guid(self, slice: int, prj_uuid: str, cid: str) -> Dict:
        """This operation creates a wrapper of a web report component
        
        param slice: ID of the slice
        param prj_uuid: ID of the project
        param cid: ID of a web report component
        """
        return self.api.get('report/dataset/wrapper-guid', params={'sliceId': slice, 'prjUUID': prj_uuid, 'reportUUID': self.uuid, 'CID': cid})
    
    def report_folders(self) -> List[Dict]:
        """This operation allows you to get a list of folders from the Report manager"""
        return self.api.get('report/folders')
    
    def report_folder_rename(self, name: str, folder_id: str, description: str = "") -> None:
        """This operation allows users to rename a folder in the Report manager and give it a new description
        
        param name: new name for a folder
        param folder_id: folderId is an ID of the folder to rename
        param description: sets a new description
        """
        self.api.post('report/folder/rename', json={'folderId': folder_id, 'name': name, 'description': description})

    def report_folder_delete(self, folder_id: str, recursive: bool = False) -> None:
        """This operation deletes a folder from the Report manager
        
        param folder_id: folderId is an ID of the folder to delete
        param recursive: flag to delete subfolders and reports inside the folder
        """
        self.api.post('report/folder/delete', json={'folderId': folder_id, 'recursive': recursive})

    def report_folder_create(self, folder_name: str, parent_id: str, description: str = "") -> Dict:
        """This operation creates a folder in the Report manager
        
        param folder_name: a name of the folder to create
        param parent_id: ID of the parent folder
        param description: set a folder description
        """
        return self.api.post('report/folder/create', json={'folderName': folder_name, 'parentId': parent_id, 'description': description})
