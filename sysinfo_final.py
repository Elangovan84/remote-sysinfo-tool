import wmi
import platform
import socket
import tkinter as tk
from tkinter import ttk
from getpass import getpass
import threading
import pythoncom 

# App Configurations
root = tk.Tk()
root.title("System Information")
root.geometry("400x500")


def get_system_info(ip_address, username, password):
    system_info = {}
    try:
        # Get System Name
        system_info["System Name"] = socket.gethostbyaddr(ip_address)[0]

        # Get System Manufacturer and Model
        wmi_obj = wmi.WMI(ip_address, user=username, password=password)
        system = wmi_obj.Win32_ComputerSystem()[0]
        system_info["Manufacturer"] = system.Manufacturer
        system_info["Model"] = system.Model

        # Get System Serial Number
        system_serial = ""
        for bios in wmi_obj.Win32_BIOS():
            system_serial = bios.SerialNumber.strip()
            break  # Assuming there is only one BIOS entry
        system_info["Serial Number"] = system_serial

        # Get Processor Name
        def get_processor_name():
            if platform.system() == 'Windows':
                c = wmi.WMI(ip_address, user=username, password=password)
                for processor in c.Win32_Processor():
                    return processor.Name.strip()
            elif platform.system() == 'Darwin':
                return platform.uname().processor
            elif platform.system() == 'Linux':
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            return line.split(':')[1].strip()
            return 'Unknown'

        system_info["Processor"] = get_processor_name()

        # Get Hard Drive Info
        hard_drives = []
        for disk in wmi_obj.Win32_LogicalDisk(DriveType=3):
            drive_info = {
                "Drive": disk.Caption,
                "Total Size": round(int(disk.Size) / (1024 ** 3), 2),  # Convert to GB
                "Free Space": round(int(disk.FreeSpace) / (1024 ** 3), 2)  # Convert to GB
            }
            hard_drives.append(drive_info)
        system_info["Hard Drives"] = hard_drives

        # Get RAM Info
        total_ram = 0
        ram_modules = []
        for ram_module in wmi_obj.Win32_PhysicalMemory():
            capacity_bytes = int(ram_module.Capacity)
            total_ram += capacity_bytes
            capacity_gb = round(capacity_bytes / (1024 ** 3), 2)  # Convert to GB
            ram_module_info = {
                "Module": ram_module.DeviceLocator,
                "Capacity": capacity_gb
            }
            ram_modules.append(ram_module_info)
        system_info["RAM"] = ram_modules

        # Get OS Info
        os_info = platform.platform()
        system_info["Operating System"] = os_info

        # Get Domain
        system_info["Domain"] = platform.node()

        # Get User Accounts
        user_accounts = []
        wmi_obj = wmi.WMI()
        for user in wmi_obj.Win32_UserAccount():
            user_info = {
                "Name": user.Name.split("\\")[-1],  # Extract only the username
            }
            user_accounts.append(user_info)
        system_info["User Accounts"] = user_accounts

        # Get Last Logon Details
        logon_session = wmi_obj.Win32_ComputerSystem()[0]
        last_logon_user = logon_session.UserName.split("\\")[-1]  # Extract only the username
        system_info["Last Logon User"] = last_logon_user

        # Get IP Address
        system_info["IP Address"] = ip_address

        return system_info
    except Exception as e:
        return f"Error: {str(e)}"


def search():
    ip_address = iptext.get()
    username = usrtext.get()
    password = pwdtext.get()

    # Disable search button
    btnsrc.configure(state=tk.DISABLED)

    # Create progress bar
    progress = ttk.Progressbar(main_frame, orient="horizontal", length=150, mode="indeterminate")
    progress.place(x=120, y=470)

    # Start the progress bar
    progress.start()

    # Create a thread for executing the get_system_info function
    thread = threading.Thread(target=retrieve_system_info, args=(ip_address, username, password, progress))
    thread.start()


def retrieve_system_info(ip_address, username, password, progress):
    pythoncom.CoInitialize()  # Initialize pythoncom in the thread
    system_info = get_system_info(ip_address, username, password)

    # Update the UI using the main thread
    root.after(10, update_ui, system_info, progress)


def update_ui(system_info, progress):
    # Stop the progress bar
    progress.stop()
    progress.place_forget()

    # Enable search button
    btnsrc.configure(state=tk.NORMAL)

    if isinstance(system_info, str):
        Status.delete(1.0, tk.END)
        Status.insert(tk.END, system_info)
    elif isinstance(system_info, dict):
        formatted_info = ""
        for key, value in system_info.items():
            if key == "Hard Drives":
                formatted_info += f"{key}:\n"
                for drive in value:
                    formatted_info += f"- Drive: {drive['Drive']}, Total Size: {drive['Total Size']} GB, Free Space: {drive['Free Space']} GB\n"
            elif key == "RAM":
                formatted_info += f"{key}:\n"
                for ram_module in value:
                    formatted_info += f"- Module: {ram_module['Module']}, Capacity: {ram_module['Capacity']} GB\n"
            else:
                formatted_info += f"{key}: {value}\n"

        Status.delete(1.0, tk.END)
        Status.insert(tk.END, formatted_info)


main_frame = tk.Frame(root, width=399, height=499)
main_frame.place(x=1, y=1)
title = tk.Label(main_frame, text="Get System Info", font=("Tahoma", 12, "bold"))
title.place(x=120, y=3)

iplbl = tk.Label(main_frame, text="IPV4:", font=("Tahoma", 10, "bold"))
iplbl.place(x=20, y=40)

iptext = tk.Entry(main_frame, width=14, font=("Tahoma", 10, "bold"))
iptext.place(x=100, y=40)

acclbl = tk.Label(main_frame, text="Admin Account", font=("Tahoma", 10, "bold"))
acclbl.place(x=100, y=65)

usrlbl = tk.Label(main_frame, text="Username:", font=("Tahoma", 10, "bold"))
usrlbl.place(x=20, y=90)

usrtext = tk.Entry(main_frame, width=15, font=("Tahoma", 10))
usrtext.place(x=100, y=90)

pwdlbl = tk.Label(main_frame, text="Password:", font=("Tahoma", 10, "bold"))
pwdlbl.place(x=20, y=120)

pwdtext = tk.Entry(main_frame, show="*", width=15, font=("Tahoma", 10))
pwdtext.place(x=100, y=120)

btnsrc = tk.Button(main_frame, command=search, text="Search", width=10, height=5, font=("Tahoma", 10, "bold"))
btnsrc.place(x=250, y=35)

Statuslal = tk.Label(main_frame, text="Status", font=("Tahoma", 12, "bold"))
Statuslal.place(x=170, y=140)

Status = tk.Text(main_frame, width=50, height=18, font=("Tahoma", 10))
Status.place(x=20, y=170)

root.mainloop()
