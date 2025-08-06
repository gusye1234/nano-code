import os
import tempfile
from nano_code.utils import file as file_utils
import pytest


def test_get_file_extname():
    assert file_utils.get_file_extname("foo.txt") == ".txt"
    assert file_utils.get_file_extname("bar.md") == ".md"
    assert file_utils.get_file_extname("no_ext") == ""

def test_get_filename():
    assert file_utils.get_filename("/abc/def/ghi.py") == "ghi.py"
    assert file_utils.get_filename("test.txt") == "test.txt"

def test_mime_file_type():
    assert file_utils.mime_file_type("foo.txt") == "text/plain"
    assert file_utils.mime_file_type("foo.png").startswith("image/")

def test_is_text_file_known_text():
    # Known text extension
    tf = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
    tf.close()
    is_text, label = file_utils.is_text_file(tf.name)
    os.unlink(tf.name)
    assert is_text
    assert label == ".md"

def test_is_text_file_unknown_extension():
    tf = tempfile.NamedTemporaryFile(suffix=".abcunknown", delete=False)
    tf.close()
    is_text, label = file_utils.is_text_file(tf.name)
    os.unlink(tf.name)
    # Could be False or True depending on MIME, don't assert value
    assert isinstance(label, (str, type(None)))

def test_is_text_file_special():
    # Should recognize .gitignore as a text file even if not existing
    for name in file_utils.SPECIAL_FILE_NAME:
        is_text, label = file_utils.is_text_file(name)
        assert is_text
        assert label == name