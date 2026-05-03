import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import pandas as pd
from database import get_db_connection
from kardex_engine import calcular_kardex_almacen_articulo, generar_kardex_consolidado
import os
from datetime import datetime

# Configuracion global de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Sistema Integral de Gestión de Almacenes e Inventarios (SUNAT) - Empresa SERCOPLUS")
        self.geometry("1200x800")
        
        # Grid layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Gestión Almacén\nSERCOPLUS", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_kardex = ctk.CTkButton(self.sidebar_frame, text="Kardex Valorizado", command=self.show_kardex)
        self.btn_kardex.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_consolidado = ctk.CTkButton(self.sidebar_frame, text="Validador & Consolidado", command=self.show_consolidado)
        self.btn_consolidado.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_movimiento = ctk.CTkButton(self.sidebar_frame, text="Registrar Movimiento", command=self.show_movimiento)
        self.btn_movimiento.grid(row=4, column=0, padx=20, pady=10)
        
        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Load initial data
        self.load_metadata()
        
        # Show Dashboard
        self.current_view = None
        self.show_dashboard()

    def load_metadata(self):
        conn = get_db_connection()
        self.df_almacenes = pd.read_sql_query("SELECT id, nombre FROM Almacen", conn)
        self.df_articulos = pd.read_sql_query("SELECT id, codigo_sunat, descripcion FROM Articulo", conn)
        self.df_tipos_op = pd.read_sql_query("SELECT id, codigo_sunat, descripcion FROM TipoOperacion", conn)
        conn.close()
        
        self.almacenes_dict = {row['nombre']: row['id'] for _, row in self.df_almacenes.iterrows()}
        self.articulos_dict = {f"{row['codigo_sunat']} - {row['descripcion']}": row['id'] for _, row in self.df_articulos.iterrows()}

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        lbl_title = ctk.CTkLabel(self.main_frame, text="Dashboard Principal", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Consolidate and get total value
        df_cons, _ = generar_kardex_consolidado()
        valor_total = df_cons['Valor_Total_Consolidado'].sum() if not df_cons.empty else 0.0
        
        card = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color="#1f538d")
        card.grid(row=1, column=0, padx=20, pady=20, sticky="nw")
        
        lbl_card_title = ctk.CTkLabel(card, text="Valorización Total de Inventario", font=ctk.CTkFont(size=16))
        lbl_card_title.pack(padx=20, pady=(20, 5))
        
        lbl_card_value = ctk.CTkLabel(card, text=f"S/. {valor_total:,.2f}", font=ctk.CTkFont(size=32, weight="bold"))
        lbl_card_value.pack(padx=20, pady=(0, 20))

    def show_kardex(self):
        self.clear_main_frame()
        lbl_title = ctk.CTkLabel(self.main_frame, text="Kardex Valorizado por Almacén (Método Promedio)", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        filters_frame = ctk.CTkFrame(self.main_frame)
        filters_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(filters_frame, text="Almacén:").pack(side="left", padx=10)
        cmb_almacen = ctk.CTkComboBox(filters_frame, values=list(self.almacenes_dict.keys()), width=200)
        cmb_almacen.pack(side="left", padx=10)
        
        ctk.CTkLabel(filters_frame, text="Artículo:").pack(side="left", padx=10)
        cmb_articulo = ctk.CTkComboBox(filters_frame, values=list(self.articulos_dict.keys()), width=300)
        cmb_articulo.pack(side="left", padx=10)
        
        btn_generar = ctk.CTkButton(filters_frame, text="Generar Kardex", command=lambda: self.render_kardex_table(cmb_almacen.get(), cmb_articulo.get()))
        btn_generar.pack(side="left", padx=10)
        
        btn_exportar = ctk.CTkButton(filters_frame, text="Exportar Excel", fg_color="green", hover_color="darkgreen", command=lambda: self.export_kardex(cmb_almacen.get(), cmb_articulo.get()))
        btn_exportar.pack(side="left", padx=10)
        
        self.table_frame = ctk.CTkFrame(self.main_frame)
        self.table_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)

    def render_kardex_table(self, almacen_name, articulo_name):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
            
        alm_id = self.almacenes_dict.get(almacen_name)
        art_id = self.articulos_dict.get(articulo_name)
        
        if not alm_id or not art_id:
            return
            
        df_kardex = calcular_kardex_almacen_articulo(alm_id, art_id)
        
        if df_kardex.empty:
            ctk.CTkLabel(self.table_frame, text="No hay movimientos registrados para este artículo.").pack(pady=20)
            return

        # Use ttk.Treeview for complex tables
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=25, fieldbackground="#2b2b2b")
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Helvetica', 10, 'bold'))

        cols = list(df_kardex.columns)
        tree = ttk.Treeview(self.table_frame, columns=cols, show='headings')
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
            
        tree.column("Operacion", width=250, anchor="w")
        tree.column("Fecha", width=150)
            
        for _, row in df_kardex.iterrows():
            tree.insert("", "end", values=list(row))
            
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

    def export_kardex(self, almacen_name, articulo_name):
        alm_id = self.almacenes_dict.get(almacen_name)
        art_id = self.articulos_dict.get(articulo_name)
        if not alm_id or not art_id:
            return
            
        df_kardex = calcular_kardex_almacen_articulo(alm_id, art_id)
        if not df_kardex.empty:
            filename = f"Kardex_{almacen_name}_{articulo_name.split(' - ')[0]}.xlsx"
            filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='.' or c=='_']).rstrip()
            df_kardex.to_excel(filename, index=False)
            import tkinter.messagebox
            tkinter.messagebox.showinfo("Exportación Exitosa", f"Kardex exportado a {filename}")

    def show_consolidado(self):
        self.clear_main_frame()
        lbl_title = ctk.CTkLabel(self.main_frame, text="Kardex Consolidado Mensual & Validador", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        filters_frame = ctk.CTkFrame(self.main_frame)
        filters_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(filters_frame, text="Año:").pack(side="left", padx=5)
        cmb_year = ctk.CTkComboBox(filters_frame, values=["2025", "2026", "2027"], width=100)
        cmb_year.set("2026")
        cmb_year.pack(side="left", padx=5)
        
        ctk.CTkLabel(filters_frame, text="Mes:").pack(side="left", padx=5)
        cmb_month = ctk.CTkComboBox(filters_frame, values=[f"{i:02d}" for i in range(1, 13)], width=100)
        cmb_month.set("05")
        cmb_month.pack(side="left", padx=5)
        
        btn_generar = ctk.CTkButton(filters_frame, text="Generar", command=lambda: self.render_consolidado_table(cmb_year.get(), cmb_month.get()))
        btn_generar.pack(side="left", padx=10)
        
        btn_exportar = ctk.CTkButton(filters_frame, text="Exportar a Excel", fg_color="green", hover_color="darkgreen", command=lambda: self.export_consolidado(cmb_year.get(), cmb_month.get()))
        btn_exportar.pack(side="left", padx=10)
        
        self.cons_table_frame = ctk.CTkFrame(self.main_frame)
        self.cons_table_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        self.render_consolidado_table("2026", "05")

    def render_consolidado_table(self, year, month):
        for widget in self.cons_table_frame.winfo_children():
            widget.destroy()
            
        df_cons, inconsistencias = generar_kardex_consolidado(year, month)
        
        if df_cons.empty:
            ctk.CTkLabel(self.cons_table_frame, text="No hay datos consolidados para este periodo.").pack(pady=20)
            return

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=25, fieldbackground="#2b2b2b")
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Helvetica', 10, 'bold'))

        cols = list(df_cons.columns)
        tree = ttk.Treeview(self.cons_table_frame, columns=cols, show='headings')
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
            
        tree.column("Articulo", width=300, anchor="w")
            
        for _, row in df_cons.iterrows():
            tree.insert("", "end", values=list(row))
            
        scrollbar = ttk.Scrollbar(self.cons_table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

    def export_consolidado(self, year, month):
        df_cons, _ = generar_kardex_consolidado(year, month)
        if not df_cons.empty:
            filename = f"Kardex_Consolidado_{year}_{month}.xlsx"
            df_cons.to_excel(filename, index=False)
            import tkinter.messagebox
            tkinter.messagebox.showinfo("Exportación Exitosa", f"Consolidado exportado a {filename}")

    def show_movimiento(self):
        self.clear_main_frame()
        lbl_title = ctk.CTkLabel(self.main_frame, text="Registrar Nuevo Movimiento", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        form_frame = ctk.CTkFrame(self.main_frame)
        form_frame.grid(row=1, column=0, padx=20, sticky="nw")
        
        # Fecha
        ctk.CTkLabel(form_frame, text="Fecha (YYYY-MM-DD HH:MM:SS):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ent_fecha = ctk.CTkEntry(form_frame, width=200)
        ent_fecha.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ent_fecha.grid(row=0, column=1, padx=10, pady=10)
        
        # Articulo
        ctk.CTkLabel(form_frame, text="Artículo:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        cmb_articulo = ctk.CTkComboBox(form_frame, values=list(self.articulos_dict.keys()), width=300)
        cmb_articulo.grid(row=1, column=1, padx=10, pady=10)
        
        # Almacen
        ctk.CTkLabel(form_frame, text="Almacén:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cmb_almacen = ctk.CTkComboBox(form_frame, values=list(self.almacenes_dict.keys()), width=300)
        cmb_almacen.grid(row=2, column=1, padx=10, pady=10)
        
        # Tipo Operacion
        ops = [f"{row['codigo_sunat']} - {row['descripcion']}" for _, row in self.df_tipos_op.iterrows()]
        ops_dict = {f"{row['codigo_sunat']} - {row['descripcion']}": row['id'] for _, row in self.df_tipos_op.iterrows()}
        ctk.CTkLabel(form_frame, text="Tipo de Operación (Tabla 12):").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        cmb_operacion = ctk.CTkComboBox(form_frame, values=ops, width=300)
        cmb_operacion.grid(row=3, column=1, padx=10, pady=10)
        
        # Cantidad
        ctk.CTkLabel(form_frame, text="Cantidad:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        ent_cantidad = ctk.CTkEntry(form_frame, width=200)
        ent_cantidad.grid(row=4, column=1, padx=10, pady=10)
        
        # Costo Total (solo si es ingreso que afecta costo, de lo contrario se ignorará o validará)
        ctk.CTkLabel(form_frame, text="Costo Total Documento (S/.):").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        ent_costo = ctk.CTkEntry(form_frame, width=200)
        ent_costo.insert(0, "0.0")
        ent_costo.grid(row=5, column=1, padx=10, pady=10)
        
        def save_movement():
            try:
                art_id = self.articulos_dict[cmb_articulo.get()]
                alm_id = self.almacenes_dict[cmb_almacen.get()]
                op_id = ops_dict[cmb_operacion.get()]
                cant = float(ent_cantidad.get())
                costo_tot = float(ent_costo.get())
                costo_u = costo_tot / cant if cant > 0 else 0.0
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, cantidad, costo_unitario, costo_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ent_fecha.get(), art_id, alm_id, op_id, cant, costo_u, costo_tot))
                conn.commit()
                conn.close()
                
                import tkinter.messagebox
                tkinter.messagebox.showinfo("Éxito", "Movimiento registrado exitosamente")
                ent_cantidad.delete(0, 'end')
                ent_costo.delete(0, 'end')
                ent_costo.insert(0, "0.0")
                
            except Exception as e:
                import tkinter.messagebox
                tkinter.messagebox.showerror("Error", f"Error al guardar: {str(e)}")
                
        btn_save = ctk.CTkButton(form_frame, text="Guardar Movimiento", command=save_movement)
        btn_save.grid(row=6, column=0, columnspan=2, pady=20)

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
