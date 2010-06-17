#12345678
from diesel.pipeline import Pipeline, PipelineClosed, PipelineCloseRequest
from cStringIO import StringIO
import py.test


FILE = __file__
if FILE.endswith('.pyc') or FILE.endswith('.pyo'):
    FILE = FILE[:-1]

class TestAdd(object):
    def test_add_string(self):
        p = Pipeline()
        assert p.add("foo") == None
        assert not p.empty

    def test_add_file(self):
        p = Pipeline()
        assert p.add(open(FILE)) == None
        assert not p.empty

    def test_add_filelike(self):
        p = Pipeline()
        sio = StringIO()
        assert p.add(sio) == None
        assert not p.empty

    def test_add_badtypes(self):
        p = Pipeline()
        py.test.raises(ValueError, p.add, 3)
        py.test.raises(ValueError, p.add, [])
        class Whatever(object): pass
        py.test.raises(ValueError, p.add, Whatever())
        assert p.empty


class TestReadSingle(object):
    def test_read_empty(self):
        p = Pipeline()
        assert p.read(500) == ''
            
    def test_read_string(self):
        p = Pipeline()
        p.add("foo")
        assert p.read(3) == "foo"
        assert p.empty

    def test_read_file(self):
        p = Pipeline()
        p.add(open(FILE))
        assert p.read(5) == "#1234"

    def test_read_filelike(self):
        p = Pipeline()
        p.add(StringIO('abcdef'))
        assert p.read(5) == 'abcde'

class TestMultipleReads(object):
    def test_read_twice(self):
        p = Pipeline()
        p.add("foo")
        assert p.read(2) == "fo"
        assert p.read(2) == "o"

    def test_read_twice_empty(self):
        p = Pipeline()
        p.add("foo")
        assert p.read(2) == "fo"
        assert p.read(2) == "o"
        assert p.read(2) == ""

class TestBackup(object):
    def test_read_backup(self):
        p = Pipeline()
        p.add("foo")
        assert p.read(2) == "fo"
        p.backup("fo")
        assert p.read(2) == "fo"
        assert p.read(2) == "o"

    def test_read_backup_extra(self):
        p = Pipeline()
        p.add("foo")
        assert p.read(2) == "fo"
        p.backup("foobar")
        assert p.read(500) == "foobaro"

class TestHybrid(object):
    def test_read_hybrid_objects(self):
        p = Pipeline()
        p.add("foo,")
        p.add(StringIO("bar,"))
        p.add(open(FILE))

        assert p.read(10) == "foo,bar,#1"
        assert p.read(4) == "2345"
        p.backup("rock") # in the middle of the "file"
        assert p.read(6) == "rock67"

class TestClose(object):
    def test_close(self):
        p = Pipeline()
        p.add("foo")
        p.add(StringIO("bar"))
        p.close_request()
        assert p.read(1000) == "foobar"
        py.test.raises(PipelineCloseRequest, p.read, 1000)

class TestLongInteractions(object):
    def test_long_1(self):
        p = Pipeline()
        p.add("foo")
        assert p.read(2) == "fo"
        p.add("bar")
        assert p.read(3) == "oba"
        p.backup("rocko")
        p.add(StringIO("soma"))
        assert p.read(1000) == "rockorsoma"
        assert p.read(1000) == ""
        assert p.empty
        p.add("X" * 10000)
        p.close_request()
        assert p.read(5000) == 'X' * 5000
        p.backup('XXX')
        py.test.raises(PipelineClosed, p.add, "newstuff")
        assert not p.empty
        assert p.read(100000) == 'X' * 5003
        assert not p.empty
        py.test.raises(PipelineCloseRequest, p.read, 1000)
        assert not p.empty
        py.test.raises(PipelineCloseRequest, p.read, 1000)

class TestPriority(object):
    def test_pri_clean(self):
        p = Pipeline()
        p.add("two")
        p.add("three")
        p.add("one")
        assert p.read(18) == "twothreeone"

        p.add("two", 2)
        p.add("three", 3)
        p.add("six", 2)
        p.add("one", 1)
        assert p.read(18) == "threetwosixone"
