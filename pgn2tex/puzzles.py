import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, Tuple, Optional, List
from string import Template
import os
import math

import chess.pgn
import chess
import chess.svg

from tqdm import tqdm
from argparse import ArgumentParser, HelpFormatter

from dataclasses import dataclass

from utils import load_pgn, get_section_from_level
from datetime import datetime


@dataclass
class PuzzleTheme:
    id: str
    name: str
    desc: str


def open_puzzles(path: Path):
    puzzles = pd.read_csv(
        path,
        encoding='utf-8',
        dtype={
            "Rating": "float64",
            "RatingDeviation": "float64",
            "Popularity": "float64",
            "NbPlays": "float64",
        },
        na_values = ["", "NA", "null"],  # Handle common non-numeric values as NaN
    )
    return puzzles


def open_themes_desc(path: Path) -> Dict[str, PuzzleTheme]:
    tree = ET.parse(path)

    themes = {}
    for child in tree.getroot():
        name = child.attrib["name"]
        d = len("Description")
        if name[-d:] != "Description":
            themes[name] = PuzzleTheme(id=name, name=child.text, desc="")
        else:
            if name[:-d] in themes:
                themes[name[:-d]].desc = child.text
    return themes


def turn2str(turn):
    if turn == chess.WHITE:
        return "White"
    else:
        return "Black"


def mk_latex_puzzle(puzzle, counter):
    board = chess.Board(fen=puzzle["FEN"])

    moves = puzzle["Moves"].split(" ")
    moves = [chess.Move.from_uci(move) for move in moves]
    board.push(moves[0])

    latex = ""
    if counter > 9:
        latex += "\\vspace{2.2cm} \n \n"
    else:
        latex += "\\vspace{2cm} \n \n"
        
    # add section to the puzzle
    puzzle_id = puzzle["PuzzleId"]
    latex += "\\newgame \n"
    latex += "\n \n \n \n \n"
    latex += "\\phantomsection \n"
    latex += f"{counter}. \\textbf{{{turn2str(board.turn)}}} to move \\pageref{{solution-{puzzle_id}}}. \n"
    latex += f"\\label{{puzzle-{puzzle_id}}} \n"
    latex += "\\fenboard{" + board.fen() + "}"
    latex += "\n"
    latex += "\n \n"
    latex += "\\scalebox{0.8}{\\showboard}"
    latex += "\n \n"

    return latex

def mk_latex_puzzle_solution(puzzle, counter):
    board = chess.Board(fen=puzzle["FEN"])

    moves = puzzle["Moves"].split(" ")
    moves = [chess.Move.from_uci(move) for move in moves]
    board.push(moves[0])
    solution = board.variation_san(moves[1:])
    # escape the # character
    solution = solution.replace("#", "\\#")

    latex = f"\\noindent\\textbf{{{counter}. {turn2str(board.turn)} to move. }}\n"
    latex += "\\phantomsection \n"
    latex += f"\\label{{solution-{puzzle['PuzzleId']}}}\n \n"
    latex += "\n \n"
    latex += "{" + solution + "} \n \n"
    latex += f"Puzzle: \\pageref{{puzzle-{puzzle['PuzzleId']}}}"
    latex += "\n \n"
    latex += "\\vspace{0.2cm} \n \n"

    return latex


def mk_book_from_list(L, level=0, book=True) -> str:
    latex = ""
    for l in L:
        if l[1] == "puzzles":
            latex += "\\newpage \n"
            latex += get_section_from_level(l[0], level, book)
            latex += "\n"
            latex += l[3]
            latex += "\\begin{multicols}{3} \n"
            counter = 1
            for p in l[2]:
                latex += "\\begin{samepage} \n"
                latex += mk_latex_puzzle(p, counter)
                latex += "\\end{samepage}"
                # new page after 9 puzzles
                if counter % 9 == 0:
                    latex += "\\end{multicols} \n"
                    latex += "\\newpage \n"
                    latex += "\n"
                    latex += l[3]
                    latex += "\n"
                    latex += "\\begin{multicols}{3} \n"
                counter += 1
            latex += "\\end{multicols} \n"
            # put solution to separate page
            latex += "\\newpage \n"
            latex += f"\\noindent\\textbf{{Solution for {l[0]}}} % Custom heading \n"
            latex += "\n"
            latex += l[3]
            counter = 1
            latex += "\\begin{multicols}{3} \n"
            for p in l[2]:
                latex += "\\begin{samepage} \n"
                latex += mk_latex_puzzle_solution(p, counter)
                latex += "\\end{samepage}"
                latex += "\n \n"

                counter += 1
            latex += "\\end{multicols} \n"

        else:
            latex += get_section_from_level(l[0], level, book)
            latex += "\n"
            latex += l[3]
            latex += mk_book_from_list(l[2], level=level + 1, book=book)

    return latex


themes = open_themes_desc(Path("data/puzzleTheme.xml"))

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Generate latex with chess puzzles from the lichess database"
    )

    parser.add_argument(
        "--problems",
        "-p",
        type=int,
        default=0,
        help="Max number of problems to sample in each theme/rating range.",
    )
    parser.add_argument(
        "--theme",
        nargs="+",
        type=str,
        help="Name of the themes to be used.",
        choices=[tag for tag, _ in themes.items()],
    )
    parser.add_argument(
        "-m",
        "--min-rating",
        type=int,
        help="Minimum rating of the problems.",
        default=1000,
    )
    parser.add_argument(
        "-s",
        "--step-size",
        type=int,
        help="Step size from problem ratings",
        default=500,
    )
    parser.add_argument(
        "-M",
        "--max-rating",
        type=int,
        help="Maximum rating of the problems.",
        default=2500,
    )
    parser.add_argument(
        "--template",
        "-t",
        type=Path,
        help="Template file to use, if none only the latex content is generated with headers / document class, it can be input later on in any latex document.",
        default=None,
    )

    parser.add_argument(
        "--front-page", "-f", help="Path to a pdf frontpage", default=None
    )

    parser.add_argument("--output", "-o", type=Path, help="Output file", default=None)

    # add argument page, default = 1
    parser.add_argument(
        "--page",
        "-page",
        type=int,
        default=1,
    )

    # add argument page_number, default = 5000
    parser.add_argument(
        "--page_number",
        "-page_number",
        type=int,
        default=500,
    )

    # print current start time
    current_time = datetime.now().time()
    print("Start Time:", current_time)

    args = parser.parse_args()

    puzzles = open_puzzles(Path("data/lichess_db_puzzle.csv"))

    L = []

    for diff in range(args.min_rating, args.max_rating, args.step_size):
        # puzzles[Themes] is a string with themes separated by space
        # remove all the themes except the first one
        puzzles["Themes"] = puzzles["Themes"].str.split(" ").str[0]

        p = puzzles[puzzles["Rating"] <= diff]

        if len(p) < args.page_number:
            p = p.sample(len(p))
        else:
            p = p.sample(
                args.page_number
            )  # We take a subsample of the puzzles so the filtering is not too slow

        diff_L = []
        for tag, theme in themes.items():
            if args.theme is not None and tag not in args.theme:
                continue

            pt = p[p["Themes"].str.contains(tag)]

            if len(pt):
                if (args.problems is not None and args.problems > 0):
                    sample_count = min(len(pt), args.problems)
                else:
                    sample_count = len(pt)
                # puzzles are displayed in 3 columns
                # so we need to make sure that the number of puzzles is divisible by 3
                sample_count = sample_count - sample_count % 3
                if sample_count == 0:
                    continue
                pt = pt.sample(sample_count).to_dict("records")
                diff_L.append((theme.name, "puzzles", pt, theme.desc))

        L.append((f"{diff} rated problems.", "list", diff_L, ""))

    content = mk_book_from_list(L, level=0, book=True)

    if args.template is None:
        template = "$content"
    else:
        with args.template.open("r") as f:
            template = f.read()

    template = Template(template)

    frontpage_path = os.path.abspath(args.front_page) if args.front_page else None
    # change path from \ to / for latex to work in Windows
    frontpage_path = frontpage_path.replace("\\", "/")

    frontpage = (
        ("\\includepdf[pages=1, noautoscale]{%s}" % frontpage_path)
        if args.front_page
        else ""
    )
    with open(args.output, "w", encoding='utf-8') as fd:
        fd.write(template.substitute(frontpage=frontpage, content=content))

    # print current end time and total time taken
    end_time = datetime.now().time()
    print("End Time:", end_time)


