from __future__ import annotations
import sys
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QPushButton, QTextEdit, QCompleter
)

from .data import load_players
from .core import run_compare

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tennis Compare")

        players_df = load_players()
        self.names = players_df["name"].dropna().astype(str).unique().tolist()

        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        layout.addLayout(form)

        left = QVBoxLayout()
        right = QVBoxLayout()
        form.addLayout(left)
        form.addLayout(right)

        self.p1 = QLineEdit()
        self.p2 = QLineEdit()
        self._set_completer(self.p1)
        self._set_completer(self.p2)

        self.y1 = QSpinBox(); self.y1.setRange(1968, 2030); self.y1.setValue(2011)
        self.y2 = QSpinBox(); self.y2.setRange(1968, 2030); self.y2.setValue(2010)

        left.addWidget(QLabel("Player A"))
        left.addWidget(self.p1)
        left.addWidget(QLabel("Year A"))
        left.addWidget(self.y1)

        right.addWidget(QLabel("Player B"))
        right.addWidget(self.p2)
        right.addWidget(QLabel("Year B"))
        right.addWidget(self.y2)

        opts = QHBoxLayout()
        layout.addLayout(opts)

        self.surface = QComboBox()
        self.surface.addItems(["Hard", "Clay", "Grass", "Indoor"])
        self.bo = QComboBox()
        self.bo.addItems(["3", "5"])

        opts.addWidget(QLabel("Surface"))
        opts.addWidget(self.surface)
        opts.addWidget(QLabel("Best-of"))
        opts.addWidget(self.bo)

        self.run_btn = QPushButton("Compare")
        self.run_btn.clicked.connect(self.on_compare)
        layout.addWidget(self.run_btn)

        self.out = QTextEdit()
        self.out.setReadOnly(True)
        layout.addWidget(self.out)

        self.resize(720, 520)

    def _set_completer(self, line_edit: QLineEdit) -> None:
        model = QStringListModel(self.names)
        comp = QCompleter(model, self)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)  # substring match
        line_edit.setCompleter(comp)

    def on_compare(self):
        p1 = self.p1.text().strip()
        p2 = self.p2.text().strip()
        y1 = int(self.y1.value())
        y2 = int(self.y2.value())
        surface = self.surface.currentText()
        bo = int(self.bo.currentText())

        try:
            res = run_compare(p1, y1, p2, y2, surface, bo)
        except Exception as e:
            self.out.setPlainText(f"Error: {e}")
            return

        lines = []
        lines.append(f"{res.player_a} ({res.year_a}) vs {res.player_b} ({res.year_b})")
        lines.append(f"Surface: {res.surface} | BO{res.best_of}")
        lines.append("")
        lines.append(f"Win Probability: {res.player_a}: {res.p_a_wins:.3f} | {res.player_b}: {1-res.p_a_wins:.3f}")
        if res.elo_a is not None and res.elo_b is not None:
            lines.append(f"Elo (slice): {res.player_a}: {res.elo_a:.1f} ({res.elo_matches_a} matches) | {res.player_b}: {res.elo_b:.1f} ({res.elo_matches_b} matches)")
        lines.append("")
        def fmt_stats(label: str, s: dict | None) -> str:
            if not s:
                return f"{label}: N/A"
            parts = [f"{label}: {s['wins']}-{s['losses']} ({s['win_pct']*100:.1f}%)"]
            if s.get('titles') is not None:
                parts.append(f"Titles: {s['titles']}, Finals: {s['finals']}")
            return " | ".join(parts)
        lines.append(fmt_stats(res.player_a, res.stats_a))
        lines.append(fmt_stats(res.player_b, res.stats_b))

        lines.append("")
        lines.append("===================================")
        lines.append(f"Winner — {res.winner}")
        lines.append("===================================")
        lines.append(f"Confidence — {abs(res.p_a_wins - 0.5)*200:.1f}%")

        if res.notes:
            lines.append("")
            lines.append("Notes:")
            lines.extend([f"- {n}" for n in res.notes])
        self.out.setPlainText("\n".join(lines))

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
