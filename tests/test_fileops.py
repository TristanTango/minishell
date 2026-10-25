"""Unit tests for the file built-ins (run by tests/run_tests.py, or with
python -m unittest discover -s tests). Each test works in its own temp folder."""
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shell import fileops
from shell.fileops import (cmd_cat, cmd_chmod, cmd_cp, cmd_ls, cmd_mkdir,
                           cmd_mv, cmd_rm, cmd_rmdir, cmd_touch)
from shell.state import STATE


class FileOpsTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="minishell_unit_")
        os.chdir(self.tmp)
        STATE["modes"].clear()

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cmd(self, fn, *args, stdin_text=""):
        out, err = io.StringIO(), io.StringIO()
        code = fn(list(args), io.StringIO(stdin_text), out, err)
        return code, out.getvalue(), err.getvalue()

    def write(self, name, text="data\n"):
        with open(name, "w") as f:
            f.write(text)

    def read(self, name):
        with open(name) as f:
            return f.read()

    # ---- mkdir / rmdir / touch
    def test_mkdir(self):
        self.assertEqual(self.run_cmd(cmd_mkdir, "a")[0], 0)
        self.assertTrue(os.path.isdir("a"))
        code, _, err = self.run_cmd(cmd_mkdir, "a")
        self.assertEqual(code, 1)
        self.assertIn("File exists", err)
        self.assertEqual(self.run_cmd(cmd_mkdir, "-p", "a/b/c")[0], 0)
        self.assertTrue(os.path.isdir("a/b/c"))
        self.assertEqual(self.run_cmd(cmd_mkdir, "x/y")[0], 1)       # parent missing
        self.assertEqual(self.run_cmd(cmd_mkdir)[0], 1)              # no operand

    def test_rmdir(self):
        os.makedirs("full/sub")
        os.mkdir("empty")
        self.assertEqual(self.run_cmd(cmd_rmdir, "empty")[0], 0)
        self.assertFalse(os.path.exists("empty"))
        self.assertEqual(self.run_cmd(cmd_rmdir, "full")[0], 1)      # not empty
        self.assertTrue(os.path.isdir("full"))
        self.write("f")
        self.assertIn("Not a directory", self.run_cmd(cmd_rmdir, "f")[2])
        self.assertIn("No such file", self.run_cmd(cmd_rmdir, "nope")[2])

    def test_touch(self):
        self.assertEqual(self.run_cmd(cmd_touch, "f", "g")[0], 0)
        self.assertTrue(os.path.isfile("f") and os.path.isfile("g"))
        self.assertEqual(self.run_cmd(cmd_touch)[0], 1)
        self.assertEqual(self.run_cmd(cmd_touch, "nodir/f")[0], 1)

    # ---- cat
    def test_cat(self):
        self.write("f", "hi\nthere\n")
        self.assertEqual(self.run_cmd(cmd_cat, "f")[1], "hi\nthere\n")
        self.assertEqual(self.run_cmd(cmd_cat, "f", "f")[1], "hi\nthere\nhi\nthere\n")
        self.assertEqual(self.run_cmd(cmd_cat, stdin_text="piped\n")[1], "piped\n")
        code, out, err = self.run_cmd(cmd_cat, "nosuch")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("No such file", err)
        os.mkdir("d")
        self.assertIn("Is a directory", self.run_cmd(cmd_cat, "d")[2])

    # ---- cp
    def test_cp_file(self):
        self.write("a", "AAA\n")
        self.assertEqual(self.run_cmd(cmd_cp, "a", "b")[0], 0)
        self.assertEqual(self.read("b"), "AAA\n")
        self.assertTrue(os.path.exists("a"))                          # source kept
        os.mkdir("d")
        self.assertEqual(self.run_cmd(cmd_cp, "a", "b", "d")[0], 0)
        self.assertTrue(os.path.exists("d/a") and os.path.exists("d/b"))
        self.assertIn("same file", self.run_cmd(cmd_cp, "a", "a")[2])

    def test_cp_errors(self):
        os.mkdir("d")
        self.write("f")
        self.assertEqual(self.run_cmd(cmd_cp, "nosuch", "x")[0], 1)
        self.assertEqual(self.run_cmd(cmd_cp, "d", "e")[0], 1)       # needs -r
        self.assertEqual(self.run_cmd(cmd_cp, "f")[0], 1)            # no destination
        self.assertEqual(self.run_cmd(cmd_cp, "f", "f2", "f3")[0], 1)  # dest not a dir

    def test_cp_recursive(self):
        os.makedirs("src/sub")
        self.write("src/a.txt", "1")
        self.write("src/sub/b.txt", "2")
        self.assertEqual(self.run_cmd(cmd_cp, "-r", "src", "dst")[0], 0)
        self.assertEqual(self.read("dst/sub/b.txt"), "2")
        self.assertEqual(self.run_cmd(cmd_cp, "-r", "src", "dst")[0], 0)   # into existing dir
        self.assertTrue(os.path.exists("dst/src/a.txt"))
        code, _, err = self.run_cmd(cmd_cp, "-r", "src", "src/sub/copy")
        self.assertEqual(code, 1)
        self.assertIn("into itself", err)

    # ---- mv
    def test_mv(self):
        self.write("a", "A")
        self.assertEqual(self.run_cmd(cmd_mv, "a", "b")[0], 0)
        self.assertFalse(os.path.exists("a"))
        self.assertEqual(self.read("b"), "A")
        os.mkdir("d")
        self.assertEqual(self.run_cmd(cmd_mv, "b", "d")[0], 0)
        self.assertTrue(os.path.exists("d/b"))
        self.assertEqual(self.run_cmd(cmd_mv, "nosuch", "x")[0], 1)
        self.assertEqual(self.run_cmd(cmd_mv, "d", "d/inner")[0], 1)   # into itself

    # ---- rm
    def test_rm(self):
        self.write("f")
        self.assertEqual(self.run_cmd(cmd_rm, "f")[0], 0)
        self.assertFalse(os.path.exists("f"))
        self.assertEqual(self.run_cmd(cmd_rm, "f")[0], 1)            # missing
        self.assertEqual(self.run_cmd(cmd_rm, "-f", "f")[0], 0)      # -f ignores missing
        self.assertEqual(self.run_cmd(cmd_rm)[0], 1)
        os.makedirs("d/sub")
        self.write("d/sub/x")
        code, _, err = self.run_cmd(cmd_rm, "d")
        self.assertEqual(code, 1)
        self.assertIn("Is a directory", err)
        self.assertEqual(self.run_cmd(cmd_rm, "-r", "d")[0], 0)
        self.assertFalse(os.path.exists("d"))
        os.mkdir("e")
        self.assertEqual(self.run_cmd(cmd_rm, "-rf", "e")[0], 0)     # combined flags

    def test_rm_refuses_dangerous_paths(self):
        self.assertEqual(self.run_cmd(cmd_rm, "-r", ".")[0], 1)
        self.assertEqual(self.run_cmd(cmd_rm, "-r", "..")[0], 1)
        self.assertEqual(self.run_cmd(cmd_rm, "-r", os.path.abspath(os.sep))[0], 1)
        self.assertTrue(os.path.isdir(self.tmp))

    # ---- ls
    def test_ls(self):
        for name in ["b.txt", "A.txt", ".hidden"]:
            self.write(name)
        self.assertEqual(self.run_cmd(cmd_ls)[1], "A.txt\nb.txt\n")
        self.assertEqual(self.run_cmd(cmd_ls, "-a")[1], ".\n..\n.hidden\nA.txt\nb.txt\n")
        self.assertEqual(self.run_cmd(cmd_ls, "b.txt")[1], "b.txt\n")
        code, _, err = self.run_cmd(cmd_ls, "nosuch")
        self.assertEqual(code, 1)
        self.assertIn("No such file", err)
        self.assertEqual(self.run_cmd(cmd_ls, "-z")[0], 1)           # bad option

    def test_ls_several_directories(self):
        os.makedirs("one")
        os.makedirs("two")
        self.write("one/x")
        self.write("two/y")
        self.assertEqual(self.run_cmd(cmd_ls, "one", "two")[1], "one:\nx\n\ntwo:\ny\n")

    def test_ls_long_marks_directories(self):
        os.mkdir("d")
        self.write("f")
        lines = self.run_cmd(cmd_ls, "-l")[1].splitlines()
        self.assertTrue(lines[0].startswith("d") and lines[0].endswith(" d"))
        self.assertTrue(lines[1].startswith("-") and lines[1].endswith(" f"))

    # ---- chmod + ls -l (real modes on Linux/macOS, simulated modes on Windows)
    def check_chmod_ls(self):
        self.write("f")
        self.assertEqual(self.run_cmd(cmd_chmod, "755", "f")[0], 0)
        self.assertTrue(self.run_cmd(cmd_ls, "-l", "f")[1].startswith("-rwxr-xr-x "))
        self.assertEqual(self.run_cmd(cmd_chmod, "600", "f")[0], 0)
        self.assertTrue(self.run_cmd(cmd_ls, "-l", "f")[1].startswith("-rw------- "))
        self.assertEqual(self.run_cmd(cmd_chmod, "644", "f")[0], 0)
        self.assertTrue(self.run_cmd(cmd_ls, "-l", "f")[1].startswith("-rw-r--r-- "))

    def test_chmod_native(self):
        if os.name == "nt":
            self.skipTest("native permission bits are not available on Windows")
        self.check_chmod_ls()

    def test_chmod_simulated(self):
        with mock.patch.object(fileops, "SIMULATE_MODES", True):
            self.check_chmod_ls()
            os.mkdir("d")
            line = [l for l in self.run_cmd(cmd_ls, "-l")[1].splitlines() if l.endswith(" d")][0]
            self.assertTrue(line.startswith("drwxr-xr-x "))

    def test_chmod_errors(self):
        self.write("f")
        self.assertEqual(self.run_cmd(cmd_chmod, "999", "f")[0], 1)    # not octal
        self.assertEqual(self.run_cmd(cmd_chmod, "rwx", "f")[0], 1)
        self.assertEqual(self.run_cmd(cmd_chmod, "75", "f")[0], 1)     # too short
        self.assertEqual(self.run_cmd(cmd_chmod, "755")[0], 1)         # no file
        self.assertEqual(self.run_cmd(cmd_chmod, "755", "nosuch")[0], 1)


if __name__ == "__main__":
    unittest.main()
