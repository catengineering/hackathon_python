# encoding: utf-8

import hashlib

from .common import test

from vendor import (
    create_object_storage_instance,
    object_storage_write,
    object_storage_read,
    object_storage_list,
    object_storage_delete,
)


@test
def test_storage_instance_simple():
    path = "oak is strong and also gives shade"
    data = (
        "Cats and dogs each hate the other. The pipe began to rust "
        "while new. Open the crate but don't break the glass. Add "
        "the sum to the product of these three."
    ).encode()

    computed_hash = hashlib.sha256(data).hexdigest()
    with create_object_storage_instance() as handle:
        object_storage_write(handle, path, data)
        read_data = object_storage_read(handle, path)
        read_data_hash = hashlib.sha256(read_data.strip()).hexdigest()

    assert (
        computed_hash == read_data_hash
    ), "hash of read data does not match written data"


@test
def test_storage_instance_crud():
    data = (
        "Cats and dogs each hate the other. The pipe began to rust "
        "while new. Open the crate but don't break the glass. Add "
        "the sum to the product of these three."
    ).encode()

    with create_object_storage_instance() as handle:

        paths = object_storage_list(handle)
        assert len(paths) == 0, "objects already exist in the object store"

        object_storage_write(handle, "path1", data)

        paths = object_storage_list(handle)
        assert len(paths) == 1, "written object is not present"

        object_storage_write(handle, "path1", data)

        paths = object_storage_list(handle)
        assert len(paths) == 1, "overwriting a file went wrong"

        object_storage_write(handle, "path2", data)

        paths = object_storage_list(handle)
        assert len(paths) == 2, "two files expected, found more than that"

        object_storage_delete(handle, "path2")

        paths = object_storage_list(handle)
        assert len(paths) == 1, "expected 1 files after deleting path2"

        object_storage_delete(handle, "path1")
        paths = object_storage_list(handle)
        assert len(paths) == 0, "expected 0 files after deleting path1"
