import os
import sys
import shutil

import unittest
import gallery_dl_server

ROOT_PATH = 'gallery-dl/'
SUB_ROOT_PATH = 'gallery-dl/test'

class GalleryDlServerTest(unittest.TestCase):

    def setUp(self):
        # Create Gallery Folder
        os.mkdir(ROOT_PATH)

        # Create Sub-root folder
        os.mkdir(SUB_ROOT_PATH)

        file_path = os.path.join(SUB_ROOT_PATH, 'test.jpg')
        with open(file_path, 'w') as new_file:
            new_file.write('Test')

        return super().setUp()

    def tearDown(self):
        # Teardown Gallery Folder
        shutil.rmtree(ROOT_PATH)
        return super().tearDown()

    def test_zip_directories(self):
        gallery_dl_server.zip_directories(ROOT_PATH)

        self.assertTrue(os.path.exists(SUB_ROOT_PATH))

        expected_file = os.path.join(ROOT_PATH, 'test.cbz')
        self.assertTrue(os.path.exists(expected_file))

    def test_find_directories_and_zip(self):
        gallery_dl_server.find_directories_and_zip()

        expected_file = os.path.join(ROOT_PATH, 'test.cbz')
        self.assertTrue(os.path.exists(expected_file))


if __name__ == '__main__':
    cwd = os.getcwd()
    sys.path.insert(0, cwd)

    unittest.main()