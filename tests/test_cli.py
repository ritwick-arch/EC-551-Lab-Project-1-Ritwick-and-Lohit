import pytest

from logicsyn.cli import main, shorten


def test_one_shot_expression(capsys):
    assert main(["-e", "F(a,b,c) = m(1,3,5) + d(7)", "--op", "1", "--op", "9"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Loaded F: inputs a, b, c; outputs F")
    assert "Op 1  Canonical SOP" in out and "Op 9  ON-set minterms of F: 3" in out
    assert "Op 2" not in out


def test_file_and_saved_report(tmp_path):
    pla = tmp_path / "two.pla"
    pla.write_text(".i 2\n.o 2\n.ob F G\n11 10\n0- 01\n")
    saved = tmp_path / "report.txt"
    assert main([str(pla), "--op", "10", "-o", str(saved)]) == 0
    text = saved.read_text(encoding="utf-8")
    assert "OFF-set maxterms of F: 3" in text and "OFF-set maxterms of G: 2" in text


def test_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit, match="error"):
        main([str(tmp_path / "missing.eqn")])


def test_shorten():
    out = shorten("      F = " + " + ".join(["abc"] * 100))
    first = out.splitlines()[0]
    assert len(first) < 210 and first.endswith(" ...") and "--full" in out


def test_interactive(monkeypatch, capsys):
    lines = iter(["F(a,b) = ab", "op 9 10", "op 13", "load nope.blif", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Loaded F: inputs a, b; outputs F" in out
    assert "ON-set minterms of F: 1" in out and "OFF-set maxterms of F: 3" in out
    assert "usage: op N" in out and "error:" in out


def test_all_ops_implemented(capsys):
    assert main(["-e", "F(a,b,c) = ab' + bc", "--all"]) == 0
    out = capsys.readouterr().out
    assert "not implemented" not in out and "Op 12 Gate count" in out


def test_verilog_and_fpga_files(tmp_path, capsys):
    v, board = tmp_path / "f.v", tmp_path / "board"
    assert main(["-e", "F(a,b,c) = ab' + bc", "--verilog", str(v), "--fpga", str(board)]) == 0
    out = capsys.readouterr().out
    assert "Op 1" not in out and f"wrote {v}" in out and "F_sop.xdc" in out
    assert v.read_text() == (board / "F_sop.v").read_text() and "module F_sop" in v.read_text()
    assert main(["-e", "F(a,b) = ab", "--verilog", str(v), "--op", "9"]) == 0
    assert "Op 9" in capsys.readouterr().out


def test_interactive_verilog(tmp_path, monkeypatch, capsys):
    lines = iter(["verilog x.v", "F(a,b) = ab", f"verilog {tmp_path / 'x.v'}", "fpga", f"fpga {tmp_path}", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "error: load a function first" in out and "usage: fpga DIR" in out
    assert (tmp_path / "x.v").exists() and (tmp_path / "F_sop.xdc").exists()
