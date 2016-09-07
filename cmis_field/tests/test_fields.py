# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock
from openerp.exceptions import UserError
from . import common


class TestCmisFields(common.BaseTestCmis):

    def test_cmis_folder_default_create(self):
        inst = self.env['cmis.test.model'].create({'name': 'folder_name'})
        with mock.patch("openerp.addons.cmis.models.cmis_backend."
                        "CmisBackend.get_cmis_repository"
                        ) as mocked_get_repository:
            mocked_cmis_repository = mock.MagicMock()
            mocked_get_repository.return_value = mocked_cmis_repository
            new_mocked_cmis_folder = mock.MagicMock()
            mocked_cmis_repository.createFolder.return_value = \
                new_mocked_cmis_folder
            mocked_cmis_repository.getObjectByPath.return_value = 'root_id'
            new_mocked_cmis_folder.getObjectId.return_value = 'cmis_id'

            # check the value initialization using the method defined on the
            # field. As result the value must be set on the given record
            inst._fields['cmis_folder'].create_value(inst)
            self.assertEquals(inst.cmis_folder, 'cmis_id')

            # in the initialization process the field will compute a path
            # where to store the new folder. This path is used to request the
            # cmis_repository to retrieve the objectId associated to this path
            # by default the path is computed by concatenating the
            # cmis_backend.initial_directory_write + / + model._name
            mocked_cmis_repository.getObjectByPath.assert_called_once_with(
                '/odoo/cmis_test_model')

            # the name of the folder created into the repository is by default
            # the one returned by the name_get method on the record and the
            # parent directory, the one returned by the method getObjectByPath
            mocked_cmis_repository.createFolder.assert_called_once_with(
                'root_id', 'folder_name', {})
            # a second call to the create_value must raise a UserError since
            # the value is already initialized
            with self.assertRaises(UserError):
                inst._fields['cmis_folder'].create_value(inst)

    def test_cmis_folder_create_x_get(self):
        # Test the use of methods specified on the field to get the
        # parent, the name and the properties to use to create a folder in CMIS
        inst = self.env['cmis.test.model'].create({'name': 'folder_name'})
        with mock.patch("openerp.addons.cmis.models.cmis_backend."
                        "CmisBackend.get_cmis_repository"
                        ) as mocked_get_repository:
            mocked_cmis_repository = mock.MagicMock()
            mocked_get_repository.return_value = mocked_cmis_repository
            new_mocked_cmis_folder = mock.MagicMock()
            mocked_cmis_repository.createFolder.return_value = \
                new_mocked_cmis_folder
            new_mocked_cmis_folder.getObjectId.return_value = 'cmis_id'

            inst._fields['cmis_folder1'].create_value(inst)
            mocked_cmis_repository.createFolder.assert_called_once_with(
                "custom_parent", "custom_name",
                {'cmis:propkey': 'custom value'})
            mocked_cmis_repository.reset_mock()

    def test_cmis_folder_create_multi(self):
        # the create method can be called on a recordset
        inst1 = self.env['cmis.test.model'].create({'name': 'folder_name1'})
        inst2 = self.env['cmis.test.model'].create({'name': 'folder_name2'})
        with mock.patch("openerp.addons.cmis.models.cmis_backend."
                        "CmisBackend.get_cmis_repository"
                        ) as mocked_get_repository:
            mocked_cmis_repository = mock.MagicMock()
            mocked_get_repository.return_value = mocked_cmis_repository

            def my_side_effect(parent, name, prop=None):
                new_object_mock = mock.MagicMock()
                if name == "folder_name1":
                    new_object_mock.getObjectId.return_value = "id1"
                    return new_object_mock
                else:
                    new_object_mock.getObjectId.return_value = "id2"
                    return new_object_mock
            mocked_cmis_repository.createFolder.side_effect = my_side_effect
            inst1._fields['cmis_folder'].create_value(inst1 + inst2)
            self.assertEquals(inst1.cmis_folder, "id1")
            self.assertEquals(inst2.cmis_folder, "id2")

    def test_cmis_folder_create_method(self):
        # if a create_method is declared in the field definition, it's
        # called with the backend as argument to initialize the field value
        # and the value returned by the method is used as field's value
        inst = self.env['cmis.test.model'].create({'name': 'folder_name'})
        inst._fields['cmis_folder2'].create_value(inst)
        self.assertEquals(inst.cmis_folder2, '_create_method')

    def test_cmis_folder_get_desciption(self):
        inst = self.env['cmis.test.model'].create({'name': 'folder_name'})
        # get_description is the method call by the method fields_get
        # to return to the UI the desciption of the UI
        descr = inst._fields['cmis_folder'].get_description(self.env)
        backend_description = descr.get('backend')
        self.assertDictEqual(
            backend_description,
            {'id': self.cmis_backend.id,
             'name': self.cmis_backend.name,
             'location': self.cmis_backend.location})
        self.assertEquals(descr.get('type'), 'cmis_folder')
        self.assertEquals(descr.get('allow_create'), True)
        self.assertEquals(descr.get('allow_delete'), False)
