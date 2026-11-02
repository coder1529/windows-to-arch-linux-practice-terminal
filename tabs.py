import tkinter as tk
import tkinter.ttk as ttk

root = tk.Tk()
root.geometry("1200x800")
root.title("TABS")
root.config(background="#000000")

label = tk.Label(root, text="ARCHSHELL tab 1", font=("Arial", 30), fg="#FFFFFF", bg="#000000")

label.pack(pady=20)

def on_tab_change(event):
    selected_tab = event.widget.select()
    tab_text = event.widget.tab(selected_tab, "text")
    label.config(text=f"ARCHSHELL {tab_text}")

tab_control = tk.ttk.Notebook(root)
tab1 = tk.Frame(tab_control, bg="#000000")
tab_control.add(tab1, text="tab 1")
tab_control.pack(expand=1, fill="both")
tab_control.bind("<<NotebookTabChanged>>", on_tab_change)

def make_new_tab():
    new_tab = tk.Frame(tab_control, bg="#000000")
    tab_control.add(new_tab, text=f"tab {len(tab_control.tabs()) + 1}")
    tab_control.select(new_tab)

button = tk.Button(root, text="Make New Tab", command=make_new_tab, font=("Arial", 20), fg="#FFFFFF", bg="#000000")
button.pack(pady=20)


root.mainloop()