import tkinter as tk
import random
import os
import time
import copy

# --- Configuration ---
SIZE = 400
GRID_LEN = 4
GRID_PADDING = 10
SCORE_FILE = "highscores.txt"

# Animation Settings
ANIMATION_STEPS = 12
ANIMATION_SPEED = 5

BACKGROUND_COLOR_GAME = "#92877d"
BACKGROUND_COLOR_CELL_EMPTY = "#9e948a"

# Updated for Base 3 Sequence: 3, 6, 12, 24...
BACKGROUND_COLOR_DICT = {
    '3': "#eee4da",
    '6': "#ede0c8",
    '12': "#f2b179",
    '24': "#f59563",
    '48': "#f67c5f",
    '96': "#f65e3b",
    '192': "#edcf72",
    '384': "#edcc61",
    '768': "#edc850",
    '1536': "#edc53f",
    '3072': "#edc22e",
    '6144': "#3c3a32",
    '12288': "#3c3a32",
}

CELL_COLOR_DICT = {
    '3': "#776e65",
    '6': "#776e65",
    '12': "#f9f6f2",
    '24': "#f9f6f2",
    '48': "#f9f6f2",
    '96': "#f9f6f2",
    '192': "#f9f6f2",
    '384': "#f9f6f2",
    '768': "#f9f6f2",
    '1536': "#f9f6f2",
    '3072': "#f9f6f2",
    '6144': "#f9f6f2",
    '12288': "#f9f6f2",
}

FONT = ("Verdana", 30, "bold")
SCORE_LABEL_FONT = ("Verdana", 12, "bold")
SCORE_FONT = ("Verdana", 20, "bold")

class Game2048(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        self.grid()
        self.master.title('2048 - Base 3') 
        
        self.master.bind("<Key>", self.key_down)
        
        self.commands = {
            'Up': 'up',
            'Down': 'down',
            'Left': 'left',
            'Right': 'right'
        }
        
        self.grid_cells = []
        self.matrix = []
        self.score = 0
        self.game_over_frame = None
        self.is_animating = False
        self.is_autoplay = False  # Flag for autoplay
        
        # Layout
        self.game_container = tk.Frame(self)
        self.game_container.grid(row=0, column=0, padx=10, pady=10)
        
        self.info_container = tk.Frame(self)
        self.info_container.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        
        # Init Grid uses Place now
        self.init_grid()
        self.init_score_board()
        self.init_matrix()
        self.update_grid_cells()
        
        self.mainloop()

    def get_cell_pos(self, r, c):
        x = GRID_PADDING + c * (self.cell_size + GRID_PADDING)
        y = GRID_PADDING + r * (self.cell_size + GRID_PADDING)
        return x, y

    def init_grid(self):
        self.background = tk.Frame(self.game_container, bg=BACKGROUND_COLOR_GAME, 
                                   width=SIZE, height=SIZE)
        self.background.grid()
        self.background.grid_propagate(False)
        self.background.pack_propagate(False)

        self.cell_size = (SIZE - (GRID_LEN + 1) * GRID_PADDING) / GRID_LEN

        for i in range(GRID_LEN):
            grid_row = []
            for j in range(GRID_LEN):
                cell = tk.Frame(self.background, bg=BACKGROUND_COLOR_CELL_EMPTY,
                                width=self.cell_size, height=self.cell_size)
                x_pos, y_pos = self.get_cell_pos(i, j)
                cell.place(x=x_pos, y=y_pos, width=self.cell_size, height=self.cell_size)
                t = tk.Label(master=cell, text="",
                             bg=BACKGROUND_COLOR_CELL_EMPTY,
                             justify=tk.CENTER, font=FONT)
                t.pack(expand=True, fill="both")
                grid_row.append(t)
            self.grid_cells.append(grid_row)

    def init_score_board(self):
        # Restart Button
        tk.Button(self.info_container, text="Restart", command=self.restart_game, 
                  font=SCORE_LABEL_FONT, bg="#e74c3c", fg="black",
                  activebackground="#c0392b", activeforeground="black",
                  relief=tk.RAISED, bd=3).pack(pady=(0, 5), fill="x", ipadx=5, ipady=5)

        # Autoplay Button
        self.autoplay_btn = tk.Button(self.info_container, text="Autoplay: OFF", command=self.toggle_autoplay, 
                                      font=SCORE_LABEL_FONT, bg="#3498db", fg="black",
                                      activebackground="#2980b9", activeforeground="black",
                                      relief=tk.RAISED, bd=3)
        self.autoplay_btn.pack(pady=(0, 20), fill="x", ipadx=5, ipady=5)

        tk.Label(self.info_container, text="Score", font=SCORE_LABEL_FONT).pack()
        self.score_label = tk.Label(self.info_container, text="0", font=SCORE_FONT)
        self.score_label.pack(pady=(0, 20))
        
        tk.Label(self.info_container, text="High Scores", font=SCORE_LABEL_FONT).pack()
        self.leaderboard_labels = []
        for i in range(5):
            lbl = tk.Label(self.info_container, text=f"{i+1}. ---", font=("Verdana", 10))
            lbl.pack(anchor="w")
            self.leaderboard_labels.append(lbl)
        self.update_leaderboard_ui()

    def init_matrix(self):
        self.matrix = [[0] * GRID_LEN for _ in range(GRID_LEN)]
        self.add_new_tile()
        self.add_new_tile()

    def add_new_tile(self):
        row, col = random.randint(0, GRID_LEN - 1), random.randint(0, GRID_LEN - 1)
        while self.matrix[row][col] != 0:
            row, col = random.randint(0, GRID_LEN - 1), random.randint(0, GRID_LEN - 1)
        self.matrix[row][col] = random.choice([3, 6])

    def update_grid_cells(self):
        for i in range(GRID_LEN):
            for j in range(GRID_LEN):
                val = self.matrix[i][j]
                if val == 0:
                    self.grid_cells[i][j].configure(text="", bg=BACKGROUND_COLOR_CELL_EMPTY)
                else:
                    n_text = str(val)
                    bg = BACKGROUND_COLOR_DICT.get(n_text, BACKGROUND_COLOR_DICT['12288'])
                    fg = CELL_COLOR_DICT.get(n_text, CELL_COLOR_DICT['12288'])
                    self.grid_cells[i][j].configure(text=n_text, bg=bg, fg=fg)
        self.update_idletasks()

    def restart_game(self):
        self.stop_autoplay() # Stop autoplay on restart
        if self.is_animating: return
        self.score = 0
        self.score_label.configure(text="0")
        self.init_matrix()
        self.update_grid_cells()
        if self.game_over_frame:
            self.game_over_frame.destroy()
            self.game_over_frame = None

    def toggle_autoplay(self):
        if self.is_autoplay:
            self.stop_autoplay()
        else:
            self.is_autoplay = True
            self.autoplay_btn.configure(text="Autoplay: ON", bg="#2ecc71")
            self.autoplay_loop()

    def stop_autoplay(self):
        self.is_autoplay = False
        self.autoplay_btn.configure(text="Autoplay: OFF", bg="#3498db")

    def autoplay_loop(self):
        if not self.is_autoplay:
            return
        if self.game_over_frame: # Stop if game over
            self.stop_autoplay()
            return
        if self.is_animating: # Wait if currently animating
            self.after(100, self.autoplay_loop)
            return

        # AI Logic
        best_move = self.get_best_move()
        if best_move:
            self.process_move(best_move)
        
        # Schedule next move in 500ms (0.5s)
        self.after(500, self.autoplay_loop)

    def get_best_move(self):
        """
        Simulates all 4 moves and picks the best one based on:
        1. Validity (must move).
        2. Priority: Down/Right > Left > Up (Corner Strategy).
        3. Score Gain.
        """
        directions = ['down', 'right', 'left', 'up']
        valid_moves = []

        for direction in directions:
            # Simulate
            temp_matrix = [row[:] for row in self.matrix] # Deep copy
            score_gain = 0
            changed = False
            
            # We need to duplicate the extraction logic to simulate without modifying self.matrix
            # or triggering animation
            for i in range(GRID_LEN):
                if direction == 'left': line = temp_matrix[i]
                elif direction == 'right': line = temp_matrix[i][::-1]
                elif direction == 'up': line = [temp_matrix[r][i] for r in range(GRID_LEN)]
                elif direction == 'down': line = [temp_matrix[r][i] for r in range(GRID_LEN)][::-1]

                new_line, _, score_inc = self.compress_line(line)
                score_gain += score_inc
                
                # Check change
                if direction == 'left':
                    if temp_matrix[i] != new_line: changed = True
                elif direction == 'right':
                    if temp_matrix[i] != new_line[::-1]: changed = True
                elif direction == 'up':
                    col = [temp_matrix[r][i] for r in range(GRID_LEN)]
                    if col != new_line: changed = True
                elif direction == 'down':
                    col = [temp_matrix[r][i] for r in range(GRID_LEN)]
                    if col != new_line[::-1]: changed = True

            if changed:
                valid_moves.append({'dir': direction, 'score': score_gain})

        if not valid_moves:
            return None

        # Strategy: Prefer Down and Right to keep blocks in corner
        # Filter for preferred moves first
        preferred = [m for m in valid_moves if m['dir'] in ['down', 'right']]
        if preferred:
            # Pick the one with highest score
            preferred.sort(key=lambda x: x['score'], reverse=True)
            return preferred[0]['dir']
        
        # If Down/Right not possible, try Left
        left_move = [m for m in valid_moves if m['dir'] == 'left']
        if left_move:
            return 'left'
            
        # Last resort: Up
        return 'up'

    def key_down(self, event):
        # Stop autoplay if user interferes manually
        if self.is_autoplay:
            self.stop_autoplay()
            
        if self.is_animating: return
        if event.keysym in self.commands:
            direction = self.commands[event.keysym]
            self.process_move(direction)

    # --- Logic & Animation Engine ---

    def compress_line(self, line):
        new_line = [0] * len(line)
        moves = []
        score = 0
        non_zeros = [i for i, x in enumerate(line) if x != 0]
        
        insert_pos = 0
        skip = False
        
        for i in range(len(non_zeros)):
            if skip:
                skip = False
                continue
            curr_idx = non_zeros[i]
            curr_val = line[curr_idx]
            
            if i + 1 < len(non_zeros) and line[non_zeros[i+1]] == curr_val:
                next_idx = non_zeros[i+1]
                merged_val = curr_val * 2 
                new_line[insert_pos] = merged_val
                score += (merged_val * curr_val)
                moves.append({'from_idx': curr_idx, 'to_idx': insert_pos, 'val': curr_val})
                moves.append({'from_idx': next_idx, 'to_idx': insert_pos, 'val': curr_val})
                insert_pos += 1
                skip = True
            else:
                new_line[insert_pos] = curr_val
                moves.append({'from_idx': curr_idx, 'to_idx': insert_pos, 'val': curr_val})
                insert_pos += 1
        return new_line, moves, score

    def process_move(self, direction):
        new_matrix = [[0]*GRID_LEN for _ in range(GRID_LEN)]
        all_moves = [] 
        total_score_add = 0
        moved = False
        
        for i in range(GRID_LEN):
            if direction == 'left': line = self.matrix[i]
            elif direction == 'right': line = self.matrix[i][::-1]
            elif direction == 'up': line = [self.matrix[r][i] for r in range(GRID_LEN)]
            elif direction == 'down': line = [self.matrix[r][i] for r in range(GRID_LEN)][::-1]
            
            new_line, line_moves, score_inc = self.compress_line(line)
            total_score_add += score_inc
            
            if direction == 'left':
                new_matrix[i] = new_line
                for m in line_moves:
                    if m['from_idx'] != m['to_idx']: moved = True
                    all_moves.append({'from': (i, m['from_idx']), 'to': (i, m['to_idx']), 'val': m['val']})
            elif direction == 'right':
                new_matrix[i] = new_line[::-1]
                for m in line_moves:
                    if m['from_idx'] != m['to_idx']: moved = True
                    all_moves.append({'from': (i, GRID_LEN-1-m['from_idx']), 'to': (i, GRID_LEN-1-m['to_idx']), 'val': m['val']})
            elif direction == 'up':
                for j, val in enumerate(new_line): new_matrix[j][i] = val
                for m in line_moves:
                    if m['from_idx'] != m['to_idx']: moved = True
                    all_moves.append({'from': (m['from_idx'], i), 'to': (m['to_idx'], i), 'val': m['val']})
            elif direction == 'down':
                for j, val in enumerate(new_line[::-1]): new_matrix[j][i] = val
                for m in line_moves:
                    if m['from_idx'] != m['to_idx']: moved = True
                    all_moves.append({'from': (GRID_LEN-1-m['from_idx'], i), 'to': (GRID_LEN-1-m['to_idx'], i), 'val': m['val']})

        if moved:
            self.animate_moves(all_moves, new_matrix, total_score_add)

    def animate_moves(self, moves, final_matrix, score_add):
        self.is_animating = True
        floating_tiles = []
        
        for m in moves:
            r_old, c_old = m['from']
            r_new, c_new = m['to']
            val = str(m['val'])
            x_start, y_start = self.get_cell_pos(r_old, c_old)
            x_end, y_end = self.get_cell_pos(r_new, c_new)
            
            bg = BACKGROUND_COLOR_DICT.get(val, BACKGROUND_COLOR_DICT['12288'])
            fg = CELL_COLOR_DICT.get(val, CELL_COLOR_DICT['12288'])
            
            lbl = tk.Label(self.background, text=val, bg=bg, fg=fg, font=FONT)
            lbl.place(x=x_start, y=y_start, width=self.cell_size, height=self.cell_size)
            floating_tiles.append({'widget': lbl, 'x': x_start, 'y': y_start, 'tx': x_end, 'ty': y_end})
        
        # Hide moving cells in grid
        for r in range(GRID_LEN):
            for c in range(GRID_LEN):
                if any(m['from'] == (r, c) for m in moves):
                     self.grid_cells[r][c].configure(text="", bg=BACKGROUND_COLOR_CELL_EMPTY)

        for step in range(ANIMATION_STEPS + 1):
            t = step / ANIMATION_STEPS
            for tile in floating_tiles:
                curr_x = tile['x'] + (tile['tx'] - tile['x']) * t
                curr_y = tile['y'] + (tile['ty'] - tile['y']) * t
                tile['widget'].place(x=curr_x, y=curr_y)
            self.update()
            time.sleep(ANIMATION_SPEED / 1000)

        for tile in floating_tiles: tile['widget'].destroy()
        
        self.matrix = final_matrix
        self.score += score_add
        self.score_label.configure(text=str(self.score))
        self.update_grid_cells()
        self.add_new_tile()
        self.update_grid_cells()
        self.check_game_over()
        self.is_animating = False

    def check_game_over(self):
        if any(0 in row for row in self.matrix): return
        for i in range(GRID_LEN):
            for j in range(GRID_LEN - 1):
                if self.matrix[i][j] == self.matrix[i][j + 1]: return
        for i in range(GRID_LEN - 1):
            for j in range(GRID_LEN):
                if self.matrix[i][j] == self.matrix[i + 1][j]: return
        
        self.save_score()
        self.stop_autoplay() # Stop on game over
        self.game_over_frame = tk.Frame(self.game_container, borderwidth=2)
        self.game_over_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self.game_over_frame, text="Game Over!", bg="#ffcc00", font=FONT).pack()

    def load_scores(self):
        if not os.path.exists(SCORE_FILE): return []
        try:
            with open(SCORE_FILE, "r") as f:
                scores = [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]
            return sorted(scores, reverse=True)[:5]
        except: return []

    def save_score(self):
        scores = self.load_scores()
        scores.append(self.score)
        scores = sorted(scores, reverse=True)[:5]
        try:
            with open(SCORE_FILE, "w") as f:
                for s in scores: f.write(f"{s}\n")
            self.update_leaderboard_ui()
        except: pass

    def update_leaderboard_ui(self):
        scores = self.load_scores()
        for i, lbl in enumerate(self.leaderboard_labels):
            if i < len(scores): lbl.configure(text=f"{i+1}. {scores[i]}")
            else: lbl.configure(text=f"{i+1}. ---")

if __name__ == "__main__":
    game = Game2048()