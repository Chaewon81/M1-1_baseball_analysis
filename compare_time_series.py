"""월별 승률(계절성 관찰)과 최근 10경기 승률(단기 추세)을 비교한다."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DATA_DIR = Path("data/processed")
IMAGE_DIR = Path("images")
TEAMS = ("KIA", "삼성")
COLORS = {"KIA": "#E62E2E", "삼성": "#1F5AA6", "월별 승률": "#5F6368"}


def get_font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf")
    if path.exists():
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_comparison_rows() -> list[dict[str, str]]:
    monthly = {
        (row["team"], row["month"]): row["win_rate"]
        for row in read_csv("monthly_summary.csv")
        if row["season"] == "2025"
    }
    rolling = [row for row in read_csv("rolling_win_rate.csv") if row["season"] == "2025"]
    rows: list[dict[str, str]] = []
    for team in TEAMS:
        team_rows = [row for row in rolling if row["team"] == team]
        for game_number, row in enumerate(team_rows, start=1):
            rows.append(
                {
                    "team": team,
                    "game_number": str(game_number),
                    "date": row["date"],
                    "month": row["month"],
                    "monthly_win_rate": monthly[(team, row["month"])],
                    "rolling_10_win_rate": row["rolling_win_rate"],
                }
            )
    output = DATA_DIR / "monthly_vs_rolling_2025.csv"
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return rows


def center(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, font, fill="#202124") -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((x - (box[2] - box[0]) / 2, y), text, font=font, fill=fill)


def draw_grid(draw: ImageDraw.ImageDraw, left: int, top: int, right: int, bottom: int) -> None:
    small = get_font(14)
    for index in range(6):
        value = index / 5
        y = bottom - (bottom - top) * value
        draw.line((left, y, right, y), fill="#D9DEE5")
        label = f"{value:.0%}"
        box = draw.textbbox((0, 0), label, font=small)
        draw.text((left - 12 - (box[2] - box[0]), y - 9), label, font=small, fill="#5F6368")


def dashed_line(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], fill: str) -> None:
    for start, end in zip(points, points[1:]):
        distance = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
        steps = max(1, int(distance / 8))
        for step in range(0, steps, 2):
            ratio1, ratio2 = step / steps, min(step + 1, steps) / steps
            draw.line(
                (
                    start[0] + (end[0] - start[0]) * ratio1,
                    start[1] + (end[1] - start[1]) * ratio1,
                    start[0] + (end[0] - start[0]) * ratio2,
                    start[1] + (end[1] - start[1]) * ratio2,
                ),
                fill=fill,
                width=2,
            )


def draw_chart(rows: list[dict[str, str]]) -> None:
    image = Image.new("RGB", (1300, 680), "white")
    draw = ImageDraw.Draw(image)
    center(draw, 650, 22, "2025년 월별 승률(계절 패턴)과 최근 10경기 승률(단기 추세) 비교", get_font(28, True))
    draw.line((875, 88, 915, 88), fill="#5F6368", width=3)
    draw.text((925, 76), "월별 승률", font=get_font(16), fill="#202124")
    draw.line((1065, 88, 1105, 88), fill="#202124", width=4)
    draw.text((1115, 76), "최근 10경기", font=get_font(16), fill="#202124")
    for index, team in enumerate(TEAMS):
        panel_left, panel_right = 40 + index * 630, 620 + index * 630
        center(draw, (panel_left + panel_right) / 2, 120, team, get_font(22, True), COLORS[team])
        left, top, right, bottom = panel_left + 68, 170, panel_right - 24, 570
        draw_grid(draw, left, top, right, bottom)
        team_rows = [row for row in rows if row["team"] == team]
        x = [left + (right - left) * index / (len(team_rows) - 1) for index in range(len(team_rows))]
        monthly_points = [(point_x, bottom - (bottom - top) * float(row["monthly_win_rate"])) for point_x, row in zip(x, team_rows)]
        dashed_line(draw, monthly_points, COLORS["월별 승률"])
        segment: list[tuple[float, float]] = []
        for point_x, row in zip(x, team_rows):
            if not row["rolling_10_win_rate"]:
                continue
            segment.append((point_x, bottom - (bottom - top) * float(row["rolling_10_win_rate"])))
        draw.line(segment, fill=COLORS[team], width=3)
        for point_x, point_y in segment[::10]:
            draw.ellipse((point_x - 3, point_y - 3, point_x + 3, point_y + 3), fill=COLORS[team])
        for game_number in (1, 36, 72, 108, 144):
            point_x = left + (right - left) * (game_number - 1) / 143
            center(draw, point_x, bottom + 15, str(game_number), get_font(14), "#5F6368")
        center(draw, (left + right) / 2, bottom + 42, "2025년 경기 순서", get_font(14), "#5F6368")
    center(draw, 650, 625, "월별 승률은 달 단위의 반복 패턴을, 최근 10경기 승률은 짧은 기간의 상승·하락을 보여 준다.", get_font(16), "#5F6368")
    image.save(IMAGE_DIR / "07_monthly_vs_rolling_2025.png")


def main() -> None:
    IMAGE_DIR.mkdir(exist_ok=True)
    rows = write_comparison_rows()
    draw_chart(rows)
    print("월별·최근 10경기 비교 CSV와 그래프를 저장했습니다.")


if __name__ == "__main__":
    main()
