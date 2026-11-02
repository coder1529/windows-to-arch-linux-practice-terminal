# ArchTerminal

I wanted to use Arch commands on my Windows laptop, so I built a terminal that pretends to be Arch. You type something like `ls -la`, it figures out the Windows version (`dir /a`), runs it for real, and shows you the output.

It's a Python + tkinter app. It isn't a real shell, just a translator with a terminal look.

```
[ArchTerminal@archterminal] ls -la
 Volume in drive C has no label.
 Directory of C:\Users\...
```

## What it can do

- Knows 241 Arch commands and what they map to on Windows. `ps aux` becomes `tasklist`, `ip addr` becomes `ipconfig /all`, and `pacman -Syu` becomes `winget upgrade --all`.
- Actually runs them and shows the output. If something fails, you see the error and the exit code.
- Figures out on its own whether a command needs cmd or PowerShell. This took me a while: half the commands were silently failing because cmd can't run PowerShell stuff.
- `cd` and `pwd` work. `cd` really changes the folder, so commands after it run there. Plain `cd` takes you home, like on Arch.
- `clear` clears the screen.
- If you type something it doesn't know, it says `EXIT CODE 127`, the same as bash.
- Output types itself out character by character, because it looks cool.

## Running it

You need Windows and Python 3.8 or newer. tkinter already comes with Python.

```bash
git clone https://github.com/coder1529/ArchTerminal.git
cd ArchTerminal
python main.py
```

It uses the [Pretendard](https://github.com/orioncactus/pretendard) font. If you don't have it, tkinter just uses a default font and everything still works.

Some things to try:

| You type | What actually runs |
|---|---|
| `ls -la` | `dir /a` |
| `pwd` | prints the current folder |
| `cd ~` | goes to your home folder |
| `ps aux` | `tasklist` |
| `ip addr` | `ipconfig /all` |
| `df -h` | `Get-Volume` |
| `uname -r` | `ver` |

## Heads up

The commands are real. `shutdown now` will actually shut your PC down, and `reboot` will reboot it. I found that out the fun way. `journalctl --vacuum-time=2weeks` wipes your Windows System event log. Be careful what you type.

## Stuff that doesn't work (yet)

- Commands have to match exactly. `ls -la` works, but `ls -la Desktop` doesn't, because it doesn't handle arguments yet (except for `cd`).
- Some mappings have placeholders like `cat file` or `kill PID`. Those run literally, so they fail.
- Long commands freeze the window until they finish, because there's no threading yet.
- Commands that open an app, like `htop` opening Task Manager, freeze the window until you close that app.

## How it works

It's simpler than it sounds:

1. Look up what you typed in a big dict (`ARCH_TO_WINDOWS`).
2. If the Windows command looks like PowerShell, wrap it in `powershell -Command`.
3. Run it with `subprocess`.
4. Type the output out one character at a time with tkinter's `after()`.

The biggest thing I learned is that you can never block tkinter's main loop. My first try at a delay was a `while` loop, and it froze the whole window.
