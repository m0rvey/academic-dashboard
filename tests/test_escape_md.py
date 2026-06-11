from src.bot.utils import escape_md


def test_escape_md_none():
    assert escape_md(None) is None


def test_escape_md_empty():
    assert escape_md("") == ""


def test_escape_md_no_special_chars():
    assert escape_md("Hello World") == "Hello World"


def test_escape_md_underscore():
    assert escape_md("hello_world") == "hello\\_world"


def test_escape_md_asterisk():
    assert escape_md("bold*text") == "bold\\*text"


def test_escape_md_backtick():
    assert escape_md("code`block") == "code\\`block"


def test_escape_md_brackets():
    assert escape_md("[link](url)") == "\\[link\\]\\(url\\)"


def test_escape_md_tilde():
    assert escape_md("strike~through") == "strike\\~through"


def test_escape_md_angle_bracket():
    assert escape_md("quote>text") == "quote\\>text"


def test_escape_md_hash():
    assert escape_md("#heading") == "\\#heading"


def test_escape_md_plus_minus():
    assert escape_md("list+item") == "list\\+item"


def test_escape_md_exclamation():
    assert escape_md("alert!important") == "alert\\!important"


def test_escape_md_dot():
    assert escape_md("file.txt") == "file\\.txt"


def test_escape_md_combined():
    text = "Check [this](url) for _bold_ and *italic*"
    expected = "Check \\[this\\]\\(url\\) for \\_bold\\_ and \\*italic\\*"
    assert escape_md(text) == expected


def test_escape_md_cyrillic():
    text = "Задача по математике (домашка)"
    expected = "Задача по математике \\(домашка\\)"
    assert escape_md(text) == expected


def test_escape_md_preserves_normal_chars():
    text = "Математика 123 абвгде"
    assert escape_md(text) == text
