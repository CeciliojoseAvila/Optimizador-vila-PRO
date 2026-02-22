import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import shutil
import platform
import threading
import time
import gc
import logging
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import subprocess
import ctypes

# Configuración de tema
THEME = {
    "bg_dark": "#050505",
    "bg_light": "#0a0a0a",
    "accent": "#00ff41",
    "danger": "#ff003c",
    "text_light": "white"
}

# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

def ejecutar_comando_seguro(comando: list) -> bool:
    """Ejecuta un comando del sistema de forma segura."""
    try:
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.SubprocessError:
        return False


def eliminar_contenido_directorio(ruta: str) -> int:
    """Elimina el contenido de un directorio. Retorna cantidad de elementos eliminados."""
    eliminados = 0
    if not ruta or not os.path.exists(ruta):
        return 0
    
    for elemento in os.listdir(ruta):
        ruta_completa = os.path.join(ruta, elemento)
        try:
            if os.path.isfile(ruta_completa) or os.path.islink(ruta_completa):
                os.remove(ruta_completa)
            elif os.path.isdir(ruta_completa):
                shutil.rmtree(ruta_completa)
            eliminados += 1
        except (PermissionError, OSError):
            continue
    
    return eliminados

class NexusUltra:
    """Optimizador de sistema con interfaz gráfica avanzada."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA OPTIMIZADOR INTEL CJAR")
        self.root.geometry("900x650")
        self.root.configure(bg=THEME["bg_dark"])
        
        # Configurar logging
        self._setup_logging()

        # Variables de control con thread safety
        self.running = True
        self.cpu_history = [0] * 30
        self.lock = threading.Lock()
        
        # Configurar comportamiento al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        
        # Iniciar hilo de actualización
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
    
    def _setup_logging(self):
        """Configurar sistema de logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_ui(self):
        """Configurar interfaz gráfica."""
        # --- HEADER ---
        header = tk.Frame(self.root, bg=THEME["accent"], height=5)
        header.pack(fill="x")
        
        title_frame = tk.Frame(self.root, bg=THEME["bg_dark"])
        title_frame.pack(fill="x", pady=10)
        tk.Label(title_frame, text="SISTEMA OPTIMIZADOR INTEL CJAR", font=("Courier New", 24, "bold"), 
                 bg=THEME["bg_dark"], fg=THEME["accent"]).pack()

        # --- PANEL SUPERIOR: GRAFICA Y PROCESOS ---
        upper_panel = tk.Frame(self.root, bg=THEME["bg_dark"])
        upper_panel.pack(fill="both", expand=True, padx=20)

        # Gráfica de CPU
        self.fig, self.ax = plt.subplots(figsize=(5, 3), facecolor=THEME["bg_dark"])
        self.ax.set_facecolor(THEME["bg_dark"])
        self.line, = self.ax.plot(self.cpu_history, color=THEME["accent"])
        self.ax.set_ylim(0, 100)
        self.ax.axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=upper_panel)
        self.canvas.get_tk_widget().pack(side="left", padx=10)

        # Monitor de Procesos
        proc_frame = tk.LabelFrame(upper_panel, text=" [ TOP PROCESSES ] ", 
                                   bg=THEME["bg_dark"], fg=THEME["accent"], 
                                   font=("Consolas", 10))
        proc_frame.pack(side="right", fill="both", expand=True)
        
        self.proc_tree = ttk.Treeview(proc_frame, columns=("PID", "Name", "RAM"), 
                                      show="headings", height=8)
        self.proc_tree.heading("PID", text="PID")
        self.proc_tree.heading("Name", text="PROCESO")
        self.proc_tree.heading("RAM", text="MEMORIA %")
        self.proc_tree.column("PID", width=70)
        self.proc_tree.pack(fill="both", expand=True)
        
        btn_kill = tk.Button(proc_frame, text="TERMINAR PROCESO SELECCIONADO", 
                            bg=THEME["danger"], fg=THEME["text_light"], 
                            font=("Consolas", 9, "bold"), command=self.kill_process)
        btn_kill.pack(fill="x", pady=5)
        
        # Frame para botones de acción (debajo del botón de terminar proceso)
        action_buttons_frame = tk.Frame(proc_frame, bg=THEME["bg_dark"])
        action_buttons_frame.pack(fill="x", pady=5)

        btn_style = {
            "font": ("Consolas", 9, "bold"), 
            "fg": THEME["bg_dark"], 
            "bg": THEME["accent"], 
            "padx": 15, 
            "pady": 8
        }
        
        tk.Button(action_buttons_frame, text="LIMPIEZA NÚCLEO", command=self.deep_clean, 
                 **btn_style).pack(side="left", padx=3)
        tk.Button(action_buttons_frame, text="FLUSH RAM", command=self.optimize_ram, 
                 **btn_style).pack(side="left", padx=3)
        tk.Button(action_buttons_frame, text="LIMPIAR CACHÉ", command=self.limpiar_cache, 
                 **btn_style).pack(side="left", padx=3)
        tk.Button(action_buttons_frame, text="PAPELERA", command=self.vaciar_papelera, 
                 **btn_style).pack(side="left", padx=3)
        tk.Button(action_buttons_frame, text="HARDWARE SCAN", command=self.hardware_scan, 
                 **btn_style).pack(side="left", padx=3)
        tk.Button(action_buttons_frame, text="SALIR", command=self.exit_app, 
                 **btn_style).pack(side="left", padx=3)
        
        # Segunda fila de botones
        action_buttons_frame2 = tk.Frame(proc_frame, bg=THEME["bg_dark"])
        action_buttons_frame2.pack(fill="x", pady=3)
        
        tk.Button(action_buttons_frame2, text="OPT. INTELIGENTE", command=self.optimizacion_inteligente, 
                 bg="#ff6b00", fg=THEME["text_light"], font=("Consolas", 9, "bold"), 
                 padx=15, pady=8).pack(side="left", padx=3)
        tk.Button(action_buttons_frame2, text="CLEAR CLIPBOARD", command=self.clear_clipboard, 
                 **btn_style).pack(side="left", padx=3)

        # --- PANEL CENTRAL: CONSOLA ---
        self.console = tk.Text(self.root, bg=THEME["bg_light"], fg=THEME["accent"], 
                             font=("Consolas", 10), borderwidth=0, state="disabled")
        self.console.pack(fill="both", expand=True, padx=20, pady=10)


    # --- LÓGICA DE OPTIMIZACIÓN ---

    def log(self, text):
        """Agregar mensaje al console con timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.console.config(state="normal")
        self.console.insert(tk.END, f"[{timestamp}] > {text}\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")
        logging.info(text)

    def deep_clean(self):
        """Ejecutar limpieza profunda del sistema."""
        self.log("INICIANDO PROTOCOLO DE LIMPIEZA...")
        
        # Rutas críticas de basura
        targets = {
            "User Temp": os.environ.get('TEMP'),
            "System Temp": r'C:\Windows\Temp',
            "Prefetch": r'C:\Windows\Prefetch',
            "Windows Logs": r'C:\Windows\Logs',
            "CrashDumps": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CrashDumps')
        }
        
        total_freed = 0
        total_files = 0
        
        for name, path in targets.items():
            if not path or not os.path.exists(path):
                self.log(f"⚠ {name}: ruta no encontrada")
                continue
            
            self.log(f"Escaneando {name}...")
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        if os.path.isfile(item_path):
                            total_freed += os.path.getsize(item_path)
                            os.unlink(item_path)
                            total_files += 1
                        elif os.path.isdir(item_path):
                            for root, dirs, files in os.walk(item_path):
                                for file in files:
                                    total_freed += os.path.getsize(os.path.join(root, file))
                            shutil.rmtree(item_path)
                            total_files += 1
                    except (PermissionError, FileNotFoundError) as e:
                        self.log(f"  ⚠ Imposible eliminar {item}: {e}")
                    except Exception as e:
                        logging.error(f"Error procesando {item_path}: {e}")
            except PermissionError:
                self.log(f"  ⚠ Permisos insuficientes para {name}")
        
        freed_mb = total_freed / (1024 * 1024)
        self.log(f"✓ LIMPIEZA FINALIZADA: {total_files} elementos eliminados, {freed_mb:.2f} MB liberados.")

    def optimize_ram(self):
        """Optimizar memoria RAM mediante garbage collection."""
        self.log("EJECUTANDO FLUSH DE MEMORIA VIRTUAL...")
        try:
            collected = gc.collect()
            self.log(f"✓ Recolección de basura completada. {collected} objetos liberados.")
        except Exception as e:
            self.log(f"✗ Error durante optimización de RAM: {e}")

    def kill_process(self):
        """Terminar el proceso seleccionado de la lista."""
        selected = self.proc_tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Selecciona un proceso de la lista primero.")
            return
        
        try:
            pid = self.proc_tree.item(selected)['values'][0]
            process = psutil.Process(pid)
            name = process.name()
            process.terminate()
            self.log(f"✓ PROCESO TERMINADO: {name} (PID: {pid})")
        except psutil.NoSuchProcess:
            self.log(f"✗ Proceso ya no existe (PID: {pid})")
        except psutil.AccessDenied:
            messagebox.showerror("Error", "Permisos insuficientes para terminar este proceso.")
        except Exception as e:
            self.log(f"✗ ERROR AL TERMINAR PROCESO: {e}")

    def clear_clipboard(self):
        """Limpiar historial del portapapeles."""
        try:
            self.root.clipboard_clear()
            self.log("✓ HISTORIAL DE PORTAPAPELES ELIMINADO.")
        except Exception as e:
            self.log(f"✗ Error al acceder al portapapeles: {e}")

    def limpiar_cache(self):
        """Limpia caché de usuario."""
        self.log("LIMPIANDO CACHÉ DEL SISTEMA...")
        rutas = [
            os.path.expanduser(r"~\AppData\Local\Temp"),
            os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\INetCache")
        ]
        
        total = 0
        for ruta in rutas:
            total += eliminar_contenido_directorio(ruta)
        
        self.log(f"✓ CACHÉ LIMPIADA: {total} elementos eliminados.")

    def vaciar_papelera(self):
        """Vacía la papelera de reciclaje usando API oficial de Windows."""
        try:
            self.log("VACIANDO PAPELERA...")
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            self.log("✓ PAPELERA VACIADA CORRECTAMENTE.")
        except Exception as e:
            self.log(f"✗ Error al vaciar papelera: {e}")

    def ejecutar_limpieza_disco(self):
        """Ejecuta herramienta oficial de Windows para limpieza."""
        self.log("INICIANDO HERRAMIENTA DE LIMPIEZA DE DISCO DE WINDOWS...")
        if ejecutar_comando_seguro(["cleanmgr"]):
            self.log("✓ HERRAMIENTA DE LIMPIEZA COMPLETADA.")
        else:
            self.log("⚠ No se pudo ejecutar la herramienta de limpieza.")

    def optimizacion_inteligente(self):
        """Aplica optimización basada en uso real del sistema."""
        self.log("INICIANDO OPTIMIZACIÓN INTELIGENTE DEL SISTEMA...")
        
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage("C:\\").percent
        
        self.log(f"Estado actual - CPU: {cpu}% | RAM: {ram}% | DISCO: {disco}%")
        
        if ram >= 70:
            self.log("⚠ Memoria alta detectada, ejecutando flush de RAM...")
            self.optimize_ram()
        
        if disco >= 80:
            self.log("⚠ Espacio en disco bajo, ejecutando limpieza de caché...")
            self.limpiar_cache()
        
        self.log("EJECUTANDO LIMPIEZA GENERAL...")
        self.deep_clean()
        self.log("✓ OPTIMIZACIÓN INTELIGENTE COMPLETADA.")

    def hardware_scan(self):
        """Generar reporte técnico del sistema."""
        try:
            self.log("--- REPORTE TÉCNICO ---")
            self.log(f"SISTEMA: {platform.node()} | {platform.system()} {platform.release()}")
            self.log(f"PROCESADOR: {platform.processor()}")
            self.log(f"CORES: {psutil.cpu_count()} | RAM: {round(psutil.virtual_memory().total/1e9, 2)} GB")
            
            disk = psutil.disk_usage('/')
            disk_used = round(disk.used / 1e9, 2)
            disk_total = round(disk.total / 1e9, 2)
            self.log(f"DISCO: {disk.percent}% usado ({disk_used}/{disk_total} GB)")
            self.log("--- FIN REPORTE ---")
        except Exception as e:
            self.log(f"✗ Error durante escaneo de hardware: {e}")

    def exit_app(self):
        """Salir de la aplicación."""
        self.on_closing()

    def on_closing(self):
        """Limpiar recursos al cerrar la aplicación."""
        self.log("Cerrando aplicación...")
        self.running = False
        try:
            self.update_thread.join(timeout=2)
        except:
            pass
        self.root.destroy()

    def update_loop(self):
        """Loop principal de actualización de datos en tiempo real."""
        while self.running:
            try:
                # 1. Actualizar Gráfica de CPU
                cpu = psutil.cpu_percent(interval=0.5)
                with self.lock:
                    self.cpu_history.append(cpu)
                    self.cpu_history.pop(0)
                
                self.line.set_ydata(self.cpu_history)
                self.canvas.draw()

                # 2. Actualizar Lista de Procesos
                procs = []
                for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    try:
                        procs.append(p.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                
                procs = sorted(procs, key=lambda x: x.get('memory_percent', 0), reverse=True)[:10]
                
                # Limpiar y rellenar tabla
                for i in self.proc_tree.get_children():
                    self.proc_tree.delete(i)
                
                for p in procs:
                    try:
                        self.proc_tree.insert("", "end", 
                            values=(p['pid'], p['name'], f"{p.get('memory_percent', 0):.2f}"))
                    except Exception as e:
                        logging.error(f"Error insertando proceso en tabla: {e}")
                
                time.sleep(1.5)
            except Exception as e:
                logging.error(f"Error en update_loop: {e}")
                time.sleep(1)


if __name__ == "__main__":
    root = tk.Tk()
    app = NexusUltra(root)
    root.mainloop()
