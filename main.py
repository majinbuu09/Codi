import tkinter as tk
from coding_bot_ui import Codi, generate_response, clear_conversation
def main():
    root = tk.Tk()
    coding_bot_ui = Codi(root, generate_response, clear_conversation)
    root.mainloop()
if __name__ == "__main__":
    root = tk.Tk()
    ui = Codi(root, generate_response, clear_conversation)
    root.mainloop()
