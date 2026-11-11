"""Test build.bat + requirements.txt — du buoc build .exe."""
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parents[1]


def test_build_bat_du_buoc():
    text = (GUI_DIR / "build.bat").read_text(encoding="utf-8")
    assert "python -m venv" in text, "thieu buoc tao venv"
    assert "pip install -r requirements.txt" in text, "thieu buoc pip install"
    assert "pyinstaller" in text.lower(), "thieu buoc PyInstaller"
    assert "--onefile" in text, "thieu --onefile"
    assert "--noconsole" in text, "thieu --noconsole"
    assert "--name ToolAF" in text, "thieu --name ToolAF"
    assert "dist\\ToolAF.exe" in text or "dist/ToolAF.exe" in text


def test_requirements_du_thu_vien():
    text = (GUI_DIR / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "customtkinter" in text
    assert "requests" in text
    assert "imageio-ffmpeg" in text
    assert "pyinstaller" in text


def test_app_entry_ton_tai():
    assert (GUI_DIR / "app.py").is_file()
    src = (GUI_DIR / "app.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "def main():" in src
