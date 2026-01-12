import tkinter as tk
import psutil
import os
import shutil
import threading
import time
import ctypes
from tkinter import messagebox

# =================================================
# CONFIGURACIÓN GENERAL – PERFIL CRÍTICO 4GB RAM
# =================================================

COLOR_BG = "#1e1e1e"
COLOR_FG = "#ffffff"
COLOR_BTN = "#2d2d2d"
COLOR_OK = "#4caf50"
COLOR_WARN = "#ff9800"
COLOR_BAD = "#f44336"

AUTO_MODE = True

RAM_CRITICA = 60
RAM_EMERGENCIA = 85
DISCO_CRITICO = 75
DISCO_EMERGENCIA = 95

# =================================================
# UTILIDADES DEL SISTEMA
# =================================================

def estado_sistema():
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage("C:\\").percent
        return cpu, ram, disco
    except:
        return 0, 0, 0

def tipo_disco():
    try:
        return "SSD (probable)" if psutil.disk_io_counters().read_time < 100 else "HDD (probable)"
    except:
        return "Desconocido"

def detectar_cuello(cpu, ram, disco):
    if ram >= RAM_EMERGENCIA:
        return "🔴 RAM EN ESTADO CRÍTICO (4 GB)", COLOR_BAD
    if disco >= DISCO_EMERGENCIA:
        return "🔴 DISCO AL 100% (FREEZE)", COLOR_BAD
    if ram > RAM_CRITICA:
        return "🟠 RAM ALTA", COLOR_WARN
    if disco > DISCO_CRITICO:
        return "🟠 DISCO ALTO", COLOR_WARN
    if cpu > 90:
        return "🟡 CPU ALTA", COLOR_WARN
    return "🟢 Sistema estable", COLOR_OK

# =================================================
# LIMPIEZAS
# =================================================

def limpiar_temporales():
    rutas = [os.getenv("TEMP"), "C:\\Windows\\Temp"]
    for r in rutas:
        if r and os.path.exists(r):
            for f in os.listdir(r):
                try:
                    p = os.path.join(r, f)
                    if os.path.isfile(p):
                        os.remove(p)
                    else:
                        shutil.rmtree(p)
                except:
                    pass

def limpiar_cache():
    rutas = [
        os.path.expanduser("~\\AppData\\Local\\Temp"),
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\INetCache")
    ]
    for r in rutas:
        try:
            shutil.rmtree(r)
            os.makedirs(r)
        except:
            pass


def limpiar_papelera():
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        messagebox.showinfo("Éxito", "La papelera fue vaciada correctamente.")
    except:
        messagebox.showerror("Error", "No se pudo vaciar la papelera.")



# =================================================
# OPTIMIZACIÓN WINDOWS 11
# =================================================

def optimizar_windows_11():
    comandos = [
        "ipconfig /flushdns",
        "net stop SysMain",
        "net stop DiagTrack"
    ]
    for c in comandos:
        try:
            os.system(c + " >nul 2>&1")
        except:
            pass

# =================================================
# MODOS AUTOMÁTICOS
# =================================================

def modo_emergencia(cpu, ram, disco):
    if ram >= RAM_EMERGENCIA or disco >= DISCO_EMERGENCIA:
        limpiar_temporales()
        limpiar_cache()

def modo_automatico():
    while AUTO_MODE:
        cpu, ram, disco = estado_sistema()
        if ram > RAM_CRITICA:
            limpiar_temporales()
        if disco > DISCO_CRITICO:
            limpiar_cache()
        modo_emergencia(cpu, ram, disco)
        time.sleep(10)

# =================================================
# INTERFAZ
# =================================================

def actualizar_ui():
    while AUTO_MODE:
        cpu, ram, disco = estado_sistema()
        lbl_cpu.config(text=f"CPU: {cpu}%")
        lbl_ram.config(text=f"RAM: {ram}%")
        lbl_disco.config(text=f"Disco: {disco}%")
        estado, color = detectar_cuello(cpu, ram, disco)
        lbl_estado.config(text=estado, fg=color)
        time.sleep(2)

def salir_app():
    global AUTO_MODE
    AUTO_MODE = False
    root.destroy()

root = tk.Tk()
root.title("⚡ Optimizador Ávila PRO – 4GB RAM")
root.geometry("500x580")
root.configure(bg=COLOR_BG)
root.resizable(False, False)

def crear_label(text):
    return tk.Label(root, text=text, bg=COLOR_BG, fg=COLOR_FG, font=("Segoe UI", 11))

lbl_cpu = crear_label("CPU:")
lbl_cpu.pack(pady=5)
lbl_ram = crear_label("RAM:")
lbl_ram.pack(pady=5)
lbl_disco = crear_label("Disco:")
lbl_disco.pack(pady=5)

lbl_estado = tk.Label(root, bg=COLOR_BG, fg=COLOR_OK, font=("Segoe UI", 12, "bold"))
lbl_estado.pack(pady=10)

tk.Label(root, text=f"💽 Tipo de disco: {tipo_disco()}", bg=COLOR_BG, fg=COLOR_FG).pack(pady=5)

def boton(text, cmd, color=COLOR_BTN):
    return tk.Button(root, text=text, command=cmd, bg=color, fg=COLOR_FG, width=30)

boton("🧹 Limpiar temporales", limpiar_temporales).pack(pady=5)
boton("🧼 Limpiar caché", limpiar_cache).pack(pady=5)
boton("🗑️ Vaciar papelera", limpiar_papelera).pack(pady=5)
boton("⚡ Optimizar Windows 11", optimizar_windows_11, COLOR_OK).pack(pady=10)
boton("❌ Salir de la aplicación", salir_app, COLOR_BAD).pack(pady=10)

tk.Label(root, text="🤖 Modo automático inteligente ACTIVO", bg=COLOR_BG, fg=COLOR_WARN).pack(pady=5)

tk.Label(root, text="👨‍💻 DESARROLLADO POR CECILIO ÁVILA", bg=COLOR_BG, fg=COLOR_WARN).pack(pady=10)

threading.Thread(target=actualizar_ui, daemon=True).start()
threading.Thread(target=modo_automatico, daemon=True).start()

root.mainloop()
