import chess.pgn
import chess
import chess.svg

from utils import load_pgn, get_section_from_level

def mk_latex_puzzle(puzzle, counter, is_categorized=True, first_page=False):
    board = chess.Board(fen=puzzle["FEN"])

    moves = puzzle["Moves"].split(" ")

    latex = ""
    margin = 2.2
    if counter <= 9:
        margin = 2.0
    
    if not is_categorized:
        margin += 0.1
    if first_page:
        margin += 0

    latex += f"\\vspace{{{margin}cm}} \n \n"

    # calculate number of moves needed for one side to solve the puzzle
    # based on len of moves variable
    # example: len = 1, 2 --> need 1 move
    # len = 3, 4 --> need 2 moves
    num_of_moves = len(moves) // 2
        
    # add section to the puzzle
    puzzle_id = puzzle["PuzzleId"]
    latex += "\\newgame \n"
    latex += "\n \n \n \n \n"
    latex += "\\phantomsection \n"
    latex += f"{counter}. \\textbf{{{turn2str(board.turn)}}}, solved in {num_of_moves} moves \\pageref{{solution-{puzzle_id}}}. \n"
    latex += f"\\label{{puzzle-{puzzle_id}}} \n"
    latex += "\\fenboard{" + board.fen() + "}"
    latex += "\n"
    latex += "\n \n"
    latex += "\\scalebox{0.8}{\\showboard}"
    latex += "\n \n"

    return latex

def mk_latex_puzzle_table_cell(puzzle, counter, is_categorized=True, is_first_page=False):
    board = chess.Board(fen=puzzle["FEN"])

    moves = puzzle["Moves"].split(" ")

    latex = ""
    margin = 1.4
    
    if is_first_page:
        margin = 1.5
    
    latex += f"\\vspace{{{margin}cm}} \n \n"

    # calculate number of moves needed for one side to solve the puzzle
    # based on len of moves variable
    # example: len = 1, 2 --> need 1 move
    # len = 3, 4 --> need 2 moves
    num_of_moves = len(moves) // 2
        
    # add section to the puzzle
    puzzle_id = puzzle["PuzzleId"]
    latex += "\\newgame \n"
    latex += "\n \n \n \n \n"
    latex += "\\phantomsection \n"
    latex += f"{counter}. \\textbf{{{turn2str(board.turn)}}}, solved in {num_of_moves} moves \\pageref{{solution-{puzzle_id}}}. \n"
    latex += f"\\label{{puzzle-{puzzle_id}}} \n"
    latex += "\\fenboard{" + board.fen() + "}"
    latex += "\n"
    latex += "\n \n"
    latex += "\\scalebox{0.8}{\\showboard}"
    latex += "\n \n"

    num_of_cols = 3
    if counter % num_of_cols == 0:
        # end of row
        latex += "\\\\" + "\n"
    else:
        latex += "&" + "\n"

    return latex

def mk_latex_puzzle_solution(puzzle, counter):
    board = chess.Board(fen=puzzle["FEN"])

    moves = puzzle["Moves"].split(" ")
    moves = [chess.Move.from_uci(move) for move in moves]
    board.push(moves[0])
    solution = board.variation_san(moves[1:])
    # escape the # character
    solution = solution.replace("#", "\\#")

    latex = f"\\noindent \\textbf{{{counter}. {turn2str(board.turn)} to move. }}\n"
    latex += "\\phantomsection \n"
    latex += f"\\noindent \\label{{solution-{puzzle['PuzzleId']}}}\n \n"
    latex += "\n \n"
    latex += "\\noindent {" + solution + "} \n \n"
    # show theme of the puzzle
    latex += f"\\noindent Theme: {puzzle['Themes']} \n \n"
    latex += f"\\noindent Puzzle: \\pageref{{puzzle-{puzzle['PuzzleId']}}}"
    latex += "\n \n"
    latex += "\\vspace{0.2cm} \n \n"

    return latex

def mk_book_from_list(L, level=0, book=True, is_categorized=True) -> str:
    latex = ""
    for l in L:
        if l[1] == "puzzles":
            is_first_page = True

            latex += "\\newpage \n"
            latex += get_section_from_level(l[0], level, book)
            latex += "\n"
            latex += l[3]
            # if is_categorized is False, show the first 6 puzzles in the first page
            if not is_categorized:
                latex += "\\begin{multicols}{3} \n"
                counter = 1
                for p in l[2]:
                    if counter < 7:
                        latex += "\\begin{samepage} \n"
                        latex += mk_latex_puzzle(p, counter, is_categorized, is_first_page)
                        latex += "\\end{samepage}"
                        counter += 1
                # new page after 6 puzzles
                latex += "\\end{multicols} \n"
                latex += "\\newpage \n"
                latex += l[3]

            latex += "\\begin{multicols}{3} \n"
            counter = 1
            for p in l[2]:
                # if is_categorized is False, skip the first 6 puzzles
                # because the first 6 puzzles are already shown in the first page
                if is_first_page:
                    if counter < 7:
                        counter += 1
                        continue
                    else:
                        is_first_page = False
                        counter = 1

                latex += "\\begin{samepage} \n"
                latex += mk_latex_puzzle(p, counter, is_categorized)
                latex += "\\end{samepage}"
                # new page after 9 puzzles
                if counter % 9 == 0 and counter < len(l[2]):
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
            latex += mk_book_from_list(l[2], level=level + 1, book=book, is_categorized=is_categorized)

    return latex

def mk_book_from_list_table_layout(L, level=0, book=True, is_categorized=True) -> str:
    latex = ""
    for l in L:
        if l[1] == "puzzles":
            is_first_page_included = False

            latex += "\\newpage \n"
            latex += get_section_from_level(l[0], level, book)
            latex += "\n"
            latex += l[3]
            # if is_categorized is False, show the first 6 puzzles in the first page
            if not is_categorized:
                is_first_page_included = True
                latex += "\\begin{longtable}{p{0.32\\textwidth}p{0.32\\textwidth}p{0.32\\textwidth}} \n"
                counter = 1
                for p in l[2]:
                    if counter < 7:
                        latex += mk_latex_puzzle_table_cell(p, counter, is_categorized, is_first_page_included)
                        counter += 1
                # new page after 6 puzzles
                latex += "\\end{longtable} \n"
                latex += "\\newpage \n"
                latex += l[3]

            latex += "\\begin{longtable}{p{0.32\\textwidth}p{0.32\\textwidth}p{0.32\\textwidth}} \n"
            counter = 1
            for p in l[2]:
                # if is_categorized is False, skip the first 6 puzzles
                # because the first 6 puzzles are already shown in the first page
                if is_first_page_included:
                    if counter < 7:
                        counter += 1
                        continue

                latex += mk_latex_puzzle_table_cell(p, counter, is_categorized)
                # new page after 9 puzzles
                is_end_of_page = False
                if (is_first_page_included and (counter - 6) % 9 == 0):
                    is_end_of_page = True;
                elif (not is_first_page_included and counter % 9 == 0):
                    is_end_of_page = True;
                if is_end_of_page and counter < len(l[2]):
                    latex += "\\end{longtable} \n"
                    latex += "\\newpage \n"
                    latex += "\n"
                    latex += l[3]
                    latex += "\n"
                    latex += "\\begin{longtable}{p{0.32\\textwidth}p{0.32\\textwidth}p{0.32\\textwidth}} \n"
                counter += 1
            latex += "\\end{longtable} \n"
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
            latex += mk_book_from_list(l[2], level=level + 1, book=book, is_categorized=is_categorized)

    return latex

def turn2str(turn):
    if turn == chess.WHITE:
        return "White"
    else:
        return "Black"