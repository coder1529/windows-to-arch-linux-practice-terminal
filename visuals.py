from importlib.resources import path
import os
import re
import time
import tkinter as tk
import subprocess

root = tk.Tk()
root.title("ArchTerminal@archterminal")
root.configure(bg="#000000")
root.geometry("1200x700")
container = tk.Frame(root, bg="#000000")
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, bg="#000000", highlightthickness=0)
scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

term = tk.Frame(canvas, bg="#000000")
canvas.create_window((0, 0), window=term, anchor="nw")

def on_frame_resize(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.yview_moveto(1.0)  # stick to the bottom like a real terminal
term.bind("<Configure>", on_frame_resize)

def on_mousewheel(event):
    canvas.yview_scroll(int(-event.delta / 120), "units")
term.bind_all("<MouseWheel>", on_mousewheel)

cur_label = 0

# Arch Linux <-> Windows 11 Pro command equivalents, grouped by use type.
# Structure: COMMANDS[category][task] = {"arch": [...], "windows": [...]}
# Categories and tasks are sorted alphabetically.
# Windows entries mix cmd and PowerShell; PowerShell ones are the Verb-Noun style.
# None = no real built-in equivalent on that OS.
# Placeholders: pkg, file, dir, svc, user, host, PID, etc.

ARCH_TO_WINDOWS = {
    '7z a out.7z dir':                                                      '7z a out.7z dir',
    '7z x file.7z':                                                         '7z x file.7z',
    "alias ll='ls -la'":                                                    'doskey ll=dir $*',
    "awk -F, '{print $1}' file":                                            'Import-Csv file | Select-Object col',
    'blkid':                                                                'Get-Partition',
    'bootctl install':                                                      'bcdboot C:\\Windows',
    'cat /etc/os-release':                                                  'winver',
    'cat /sys/class/power_supply/BAT0/capacity':                            'powercfg /batteryreport',
    'cat file':                                                             'type file',
    'cd':                                                                   'cd',
    'cfdisk /dev/sdX':                                                      'diskpart',
    'chattr +i file':                                                       'attrib file',
    'chmod 755 file':                                                       'icacls file /grant user:F',
    'chown user:group file':                                                'takeown /f file',
    'clear':                                                                'cls',
    'cmd &':                                                                'Start-Job { cmd }',
    'cmd --help':                                                           'cmd /?',
    'cmd | tee file':                                                       'cmd | Tee-Object file',
    'cmp a b':                                                              'fc a b',
    'cp -r dir dst':                                                        'copy file dst',
    'cp file dst':                                                          'copy file dst',
    'crontab -e':                                                           'schtasks /create /sc daily /st 09:00 /tn name /tr "cmd"',
    'crontab -l':                                                           'schtasks /query',
    'crontab -r':                                                           'schtasks /delete /tn name /f',
    'cryptsetup luksFormat /dev/sdX1':                                      'manage-bde -on C:',
    'curl -LO url':                                                         'curl.exe -LO url',
    'cut -d, -f1 file':                                                     'Import-Csv file | Select-Object col',
    'date':                                                                 'date /t',
    'df -h':                                                                'Get-Volume',
    'dhcpcd -n eth0':                                                       'ipconfig /release',
    'diff a b':                                                             'fc a b',
    'dig example.com':                                                      'nslookup example.com',
    'dmesg':                                                                "Get-WinEvent -LogName System | Where-Object ProviderName -like 'Microsoft-Windows-Kernel*'",
    'dmidecode -t bios':                                                    'Get-CimInstance Win32_BIOS',
    'docker run -it archlinux':                                             'docker run -it ubuntu',
    'du -sh dir':                                                           '(Get-ChildItem dir -Recurse -File | Measure-Object Length -Sum).Sum',
    'echo $VAR':                                                            'echo %VAR%',
    "echo 'export VAR=val' >> ~/.bashrc":                                   'setx VAR val',
    'echo cmd | at 09:00':                                                  'schtasks /create /sc once /st 09:00 /tn name /tr "cmd"',
    'efibootmgr':                                                           'bcdedit /enum all',
    'efibootmgr -o 0001,0002':                                              'bcdedit /enum all',
    'env':                                                                  'set',
    'export VAR=val':                                                       'set VAR=val',
    'fastfetch':                                                            'systeminfo',
    'fdisk -l':                                                             'Get-Disk',
    'fdisk /dev/sdX':                                                       'diskpart',
    'file file':                                                            'Get-Item file | Format-List *',
    "find / -name '*.txt'":                                                 'dir C:\\ /s /b *.txt',
    'firejail app':                                                         'WindowsSandbox.exe',
    'free -h':                                                              'Get-CimInstance Win32_PhysicalMemory',
    'fsck /dev/sdX1':                                                       'chkdsk C: /f',
    'fstrim -av':                                                           'Optimize-Volume -DriveLetter C -ReTrim',
    'getent passwd':                                                        'net user',
    'getfacl file':                                                         'icacls file',
    'gnome-logs':                                                           'eventvwr',
    'grep -rn pattern dir':                                                 'findstr /s /n pattern *',
    'grep pattern file':                                                    'findstr pattern file',
    'groups user':                                                          'whoami /groups',
    'grub-install --target=x86_64-efi --efi-directory=/boot':               'bcdboot C:\\Windows',
    'grub-mkconfig -o /boot/grub/grub.cfg':                                 'bootrec /rebuildbcd',
    'head -n 10 file':                                                      'Get-Content file -TotalCount 10',
    'history':                                                              'doskey /history',
    'hostname':                                                             'hostname',
    'hostnamectl':                                                          'hostname',
    'hostnamectl set-hostname name':                                        'Rename-Computer -NewName name',
    'htop':                                                                 'taskmgr',
    'id user':                                                              'whoami /all',
    'inxi -Fxz':                                                            'msinfo32',
    'ip addr':                                                              'ipconfig /all',
    'ip link':                                                              'Get-NetAdapter',
    'ip link set eth0 down':                                                'Disable-NetAdapter -Name Ethernet',
    'ip link set eth0 up':                                                  'Enable-NetAdapter -Name Ethernet',
    'ip neigh':                                                             'arp -a',
    'ip route':                                                             'route print',
    'iwctl station wlan0 connect SSID':                                     'netsh wlan connect name=SSID',
    'iwctl station wlan0 get-networks':                                     'netsh wlan show networks mode=bssid',
    'jobs':                                                                 'Get-Job',
    'journalctl':                                                           'Get-WinEvent -LogName System',
    'journalctl --vacuum-time=2weeks':                                      'wevtutil cl System',
    'journalctl -b':                                                        "Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime}",
    'journalctl -k':                                                        "Get-WinEvent -LogName System | Where-Object ProviderName -like 'Microsoft-Windows-Kernel*'",
    'journalctl -p err -b':                                                 "Get-WinEvent -FilterHashtable @{LogName='System'; Level=2}",
    'journalctl -u svc':                                                    "Get-WinEvent -LogName System | Where-Object ProviderName -eq 'Service Control Manager'",
    'kill -9 PID':                                                          'taskkill /PID PID /F',
    'kill PID':                                                             'taskkill /PID PID /F',
    'killall name':                                                         'taskkill /IM name.exe /F',
    'less file':                                                            'more file',
    'ln -s target link':                                                    'mklink link target',
    'ln target link':                                                       'mklink /H link target',
    'localectl set-locale LANG=en_US.UTF-8':                                'Set-WinSystemLocale en-US',
    'locate name':                                                          'dir C:\\ /s /b *.txt',
    'loginctl lock-session':                                                'rundll32.exe user32.dll,LockWorkStation',
    'loginctl terminate-user $USER':                                        'shutdown /l',
    'ls -l file':                                                           'icacls file',
    'ls -la':                                                               'dir /a',
    'ls /dev/ttyUSB* /dev/ttyACM*':                                         '[System.IO.Ports.SerialPort]::GetPortNames()',
    'ls ~/.config/autostart':                                               'explorer shell:startup',
    'lsattr file':                                                          'attrib file',
    'lsblk':                                                                'Get-Disk',
    'lsblk -f':                                                             'Get-Partition',
    'lscpu':                                                                'Get-CimInstance Win32_Processor',
    'lshw -short':                                                          'msinfo32',
    'lsmod':                                                                'driverquery',
    'lsof -p PID':                                                          'resmon',
    'lspci':                                                                'Get-PnpDevice -PresentOnly',
    'lspci -k | grep -A3 VGA':                                              'Get-CimInstance Win32_VideoController',
    'lsusb':                                                                "Get-PnpDevice -PresentOnly | Where-Object InstanceId -like 'USB*'",
    'man cmd':                                                              'cmd /?',
    'mkdir -p a/b/c':                                                       'mkdir a\\b\\c',
    'mkfs.ext4 /dev/sdX1':                                                  'format E: /FS:NTFS /Q',
    'mkfs.fat -F32 /dev/sdX1':                                              'format E: /FS:NTFS /Q',
    'modprobe -r module':                                                   'pnputil /delete-driver oem0.inf /uninstall',
    'modprobe module':                                                      'pnputil /add-driver driver.inf /install',
    'mount -o loop file.iso /mnt':                                          'Mount-DiskImage -ImagePath C:\\file.iso',
    'mount -t cifs //server/share /mnt -o username=user':                   'net use Z: \\\\server\\share',
    'mount /dev/sdX1 /mnt':                                                 'Add-PartitionAccessPath -DiskNumber 1 -PartitionNumber 1 -AccessPath E:',
    'mv old new':                                                           'ren old new',
    'mv src dst':                                                           'move src dst',
    'nc -zv host 22':                                                       'Test-NetConnection host -Port 22',
    'neofetch':                                                             'systeminfo',
    'nft add rule inet filter input tcp dport 22 accept':                   'New-NetFirewallRule -DisplayName SSH -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow',
    'nft list ruleset':                                                     'Get-NetFirewallProfile',
    'nice -n 10 cmd':                                                       'start /LOW cmd',
    'nmcli connection show':                                                'netsh wlan show profiles',
    'nmcli connection up id <name>':                                        'ipconfig /release',
    'nmcli device wifi connect SSID password PASS':                         'netsh wlan connect name=SSID',
    'nmcli device wifi list':                                               'netsh wlan show networks mode=bssid',
    'nohup cmd &':                                                          'Start-Process cmd -WindowStyle Hidden',
    'nslookup example.com':                                                 'nslookup example.com',
    'pacman -Q':                                                            'winget list',
    'pacman -Qi pkg':                                                       'winget show pkg',
    'pacman -Qkk':                                                          'sfc /scannow',
    'pacman -Rns pkg':                                                      'winget uninstall pkg',
    'pacman -S pkg':                                                        'winget install pkg',
    'pacman -S qemu-full libvirt virt-manager':                             'Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All',
    'pacman -Si pkg':                                                       'winget show pkg',
    'pacman -Ss term':                                                      'winget search term',
    'pacman -Syu':                                                          'winget upgrade --all',
    'pacman -U file.pkg.tar.zst':                                           'msiexec /i file.msi',
    'parted /dev/sdX':                                                      'diskpart',
    'paru -S pkg':                                                          'choco install pkg',
    'passwd user':                                                          'net user user *',
    'pgrep name':                                                           'Get-Process name | Select-Object Id',
    'ping -c 4 host':                                                       'ping host',
    'pkill name':                                                           'taskkill /IM name.exe /F',
    'podman run -it archlinux':                                             'docker run -it ubuntu',
    'powerprofilesctl list':                                                'powercfg /list',
    'powerprofilesctl set performance':                                     'powercfg /setactive SCHEME_MIN',
    'printenv':                                                             'set',
    'ps aux':                                                               'tasklist',
    'pstree':                                                               'Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name',
    'pwd':                                                                  'cd',
    'qemu-system-x86_64 -enable-kvm -m 4G -hda disk.qcow2':                 'New-VM -Name vm -MemoryStartupBytes 4GB -NewVHDPath vm.vhdx -NewVHDSizeBytes 60GB',
    'reboot':                                                               'shutdown /r /t 0',
    'renice -n 10 -p PID':                                                  'start /LOW cmd',
    'resolvectl flush-caches':                                              'ipconfig /flushdns',
    'rm -r dir':                                                            'rmdir /S /Q dir',
    'rm file':                                                              'del file',
    'rmdir dir':                                                            'rmdir /S /Q dir',
    'rsync -av --delete src/ dst/':                                         'robocopy src dst /MIR',
    'scp file user@host:/path':                                             'scp file user@host:/path',
    "sed -i 's/old/new/g' file":                                            "(Get-Content file) -replace 'old','new' | Set-Content file",
    'setsid cmd':                                                           'Start-Process cmd -WindowStyle Hidden',
    'sha256sum file':                                                       'certutil -hashfile file SHA256',
    'shutdown +30':                                                         'shutdown /s /t 1800',
    'shutdown -c':                                                          'shutdown /a',
    'shutdown now':                                                         'shutdown /s /t 0',
    'sleep 5':                                                              'timeout /t 5',
    'smartctl -a /dev/sda':                                                 'Get-PhysicalDisk | Get-StorageReliabilityCounter',
    'sort file':                                                            'sort file',
    'sort file | uniq':                                                     'Get-Content file | Sort-Object -Unique',
    'source ~/.bashrc':                                                     '. $PROFILE',
    'ss -tulpn':                                                            'netstat -ano',
    'ssh user@host':                                                        'ssh user@host',
    'stat file':                                                            'Get-Item file | Format-List *',
    'su - user':                                                            'runas /user:user cmd',
    'sudo cmd':                                                             'sudo cmd',
    'systemctl --failed':                                                   "Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' }",
    'systemctl --user enable app.service':                                  'explorer shell:startup',
    'systemctl disable --now name.timer':                                   'schtasks /delete /tn name /f',
    'systemctl disable svc':                                                'Set-Service svc -StartupType Disabled',
    'systemctl enable --now libvirtd':                                      'Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All',
    'systemctl enable --now name.timer':                                    'schtasks /create /sc daily /st 09:00 /tn name /tr "cmd"',
    'systemctl enable svc':                                                 'Set-Service svc -StartupType Automatic',
    'systemctl hibernate':                                                  'shutdown /h',
    'systemctl list-timers':                                                'schtasks /query',
    'systemctl list-units --type=service':                                  'sc query',
    'systemctl poweroff':                                                   'shutdown /s /t 0',
    'systemctl reboot':                                                     'shutdown /r /t 0',
    'systemctl reboot --firmware-setup':                                    'shutdown /r /fw /t 0',
    'systemctl restart svc':                                                'Restart-Service svc',
    'systemctl start name.service':                                         'schtasks /run /tn name',
    'systemctl start svc':                                                  'net start svc',
    'systemctl status svc':                                                 'sc query svc',
    'systemctl stop svc':                                                   'net stop svc',
    'systemctl suspend':                                                    'rundll32.exe powrprof.dll,SetSuspendState 0,1,0',
    'systemd-run --on-calendar="2026-11-02 09:00" cmd':                     'schtasks /create /sc once /st 09:00 /tn name /tr "cmd"',
    'tail -f file':                                                         'Get-Content file -Wait -Tail 10',
    'tail -n 10 file':                                                      'Get-Content file -Tail 10',
    'tar -czf out.tar.gz dir':                                              'tar -czf out.tar.gz dir',
    'tar -tf file.tar.gz':                                                  'tar -tf file.zip',
    'tar -xzf file.tar.gz':                                                 'tar -xzf file.tar.gz',
    'time cmd':                                                             'Measure-Command { cmd }',
    'timedatectl':                                                          'tzutil /g',
    'timedatectl set-ntp true':                                             'w32tm /resync',
    'timedatectl set-timezone Asia/Seoul':                                  'tzutil /s "Korea Standard Time"',
    'top':                                                                  'taskmgr',
    'touch file':                                                           'type nul > file',
    'tracepath host':                                                       'tracert host',
    'traceroute host':                                                      'tracert host',
    'tree':                                                                 'tree /F',
    'ufw allow 22/tcp':                                                     'New-NetFirewallRule -DisplayName SSH -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow',
    'ufw status verbose':                                                   'Get-NetFirewallProfile',
    'umount /mnt':                                                          'mountvol E: /D',
    'uname -a':                                                             'winver',
    'uname -r':                                                             'ver',
    'unzip -l file.zip':                                                    'tar -tf file.zip',
    'unzip file.zip':                                                       'Expand-Archive file.zip -DestinationPath dir',
    'upower -i $(upower -e | grep BAT)':                                    'powercfg /batteryreport',
    'uptime':                                                               '(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime',
    'useradd -m user':                                                      'net user user /add',
    'userdel -r user':                                                      'net user user /delete',
    'usermod -aG group user':                                               'net localgroup group user /add',
    'virsh list --all':                                                     'Get-VM',
    'virsh shutdown vm':                                                    'Stop-VM vm',
    'virsh start vm':                                                       'Start-VM vm',
    'virt-install --name vm --memory 4096 --disk size=40 --cdrom file.iso': 'New-VM -Name vm -MemoryStartupBytes 4GB -NewVHDPath vm.vhdx -NewVHDSizeBytes 60GB',
    'watch -n 2 cmd':                                                       'while ($true) { cmd; Start-Sleep 2; Clear-Host }',
    'wc -l file':                                                           'find /c /v "" file',
    'wget url':                                                             'curl.exe -LO url',
    'which cmd':                                                            'where cmd',
    'who':                                                                  'query user',
    'whoami':                                                               'whoami',
    'wl-copy < file':                                                       'clip < file',
    'wl-paste':                                                             'Get-Clipboard',
    'xclip -selection clipboard -o':                                        'Get-Clipboard',
    'xclip -selection clipboard < file':                                    'clip < file',
    'xdg-open file':                                                        'start file',
    'xfreerdp /v:host':                                                     'mstsc /v:host',
    'yay -S pkg':                                                           'choco install pkg',
    'zip -r out.zip dir':                                                   'Compress-Archive -Path dir -DestinationPath out.zip',
}

def type_text(text, index=0, delay=50, target_label=None):
    if target_label is None:
        target_label = cur_label
    if not target_label.winfo_exists():
        return
    if index < len(text):
        target_label.config(text=text[:index + 1])
        term.after(delay, type_text, text, index + 1, delay, target_label)

label = tk.Label(term, text="", font=("Pretendard", 10, ), fg = "#ffffff", bg = "#000000", anchor="nw", justify="left")
label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
# label.pack(expand=True)

opening_message = "[ArchTerminal@archterminal] "

cur_label = label

type_text(opening_message)

busy = False

def new_prompt():
    global cur_label, busy
    busy = False
    new_label = tk.Label(term, text="", font=("Pretendard", 10), fg="#ffffff", bg="#000000", anchor="nw", justify="left")
    new_label.grid(row=cur_row, column=0, padx=10, pady=10, sticky="nw")
    cur_label = new_label
    input_zone.grid(row=cur_row, column=1, padx=0, pady=10, sticky="nw")
    input_zone.delete("1.0", tk.END)
    type_text(opening_message, 0, 50)


def run_command(command, raw_command):
    if raw_command == "pwd":
        return os.getcwd()
    if raw_command == "cd" or raw_command.startswith("cd "):
        target = os.path.expanduser(raw_command[3:].strip() or "~")
        try:
            os.chdir(target)
            return f"Changed directory to {os.getcwd()}"
        except OSError as e:
            return f"cd: {e.strerror}: {target}"
    is_ps = re.search(r"\b[A-Z][a-z]+-[A-Z]", command) or command[:1] in "($[."
    if is_ps:
        command = f'powershell -NoProfile -Command "{command}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="cp949", errors="replace")
    out = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        out += f"\nEXIT CODE {result.returncode}"
    return out or "(no output)"

def new_line_check(event):
    global cur_row, busy
    if busy:
        return "break"
    user_command = input_zone.get("1.0", "end-1c").strip()
    history_label = tk.Label(term, text=user_command, font=("Pretendard", 10), fg="#ffffff", bg="#000000", anchor="nw")
    history_label.grid(row=cur_row, column=1, padx=0, pady=10, sticky="nw")
    cur_row += 1
    if user_command and user_command not in ARCH_TO_WINDOWS and not user_command.startswith("cd"):
        msg = "FAILED: NO SUCH COMMAND, EXIT CODE 127"
        out_label = tk.Label(term, text="", font=("Pretendard", 10), fg="#ffffff", bg="#000000", anchor="nw", justify="left")
        out_label.grid(row=cur_row, column=0, columnspan=2, padx=10, pady=10, sticky="nw")
        type_text(msg, target_label=out_label)
        cur_row += 1
        input_zone.delete("1.0", tk.END)
        busy = True
        term.after(len(msg * 50), new_prompt)
    elif user_command == 'clear':
        for widget in term.winfo_children():
            if widget is not input_zone:
                widget.destroy()
        cur_row = 0
        new_prompt()
    elif user_command:
        result = run_command(ARCH_TO_WINDOWS.get(user_command, ""), user_command)
        out_label = tk.Label(term, text="", font=("Pretendard", 10), fg="#ffffff", bg="#000000", anchor="nw", justify="left")
        out_label.grid(row=cur_row, column=0, columnspan=2, padx=10, pady=10, sticky="nw")
        type_text(result, 0, delay=10, target_label=out_label)
        cur_row += 1
        input_zone.delete("1.0", tk.END)
        busy = True
        term.after(len(result) * 50, new_prompt)
    else:
        new_prompt()
    return "break"

cur_row = 0
input_zone = tk.Text(term, height=1, font=("Pretendard", 10), fg="#ffffff", bg="#000000", insertbackground="#ffffff", borderwidth=0)
input_zone.grid(row=0, column=1, padx=0, pady=10, sticky="nw")
input_zone.bind("<Return>", new_line_check)
input_zone.focus_set()
root.bind("<FocusIn>", lambda e: input_zone.focus_set())
root.bind("<Button-1>", lambda e: input_zone.focus_set())

root.mainloop()