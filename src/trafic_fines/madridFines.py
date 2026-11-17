from .cache import CacheURL
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import requests
import io
import matplotlib.pyplot as plt


RAIZ = "https://datos.madrid.es/"
MAPPING_MES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

def get_url(year: int, month: int) -> str:
    """
    Función que recibe como argumentos un mes (1–12) y un año (con cuatro cifras, ej. 2024) y devuelva la URL del fichero CSV con los datos
    de multas correspondiente a ese mes y año, disponible en el portal de datos abiertos del Ayuntamiento de Madrid. Si el mes y año no están
    en la página se debe producir una excepción. 
    """

    # Realizamos la petición a la web
    extension = "dataset/210104-0-multas-circulacion-detalle/downloads"
    url = RAIZ + extension.lstrip("/")
    
    # Request
    response = requests.get(url)
    
    # si la petición ha ido bien
    if response.status_code == 200:   
            
        # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
        soup = BeautifulSoup(response.text,"html.parser")
        data_key = f"{year}-{MAPPING_MES[month]}"
        resources = soup.select(f'div.tracked-resource-item[data-key="{data_key}"]')
        for resource in resources:
            link = resource.select_one('a.resource-url-analytics')
            if link:
                return RAIZ+link["href"]
        
    # si la petición ha ido mal 
    else:
        raise MadridError("Error al realizar la petición")
       

class MadridFines:

    def __init__(self, app_name, obsolescence) -> None:
        self.cacheurl: CacheURL(app_name, obsolescence)
        self.__data: pd.DataFrame = pd.DataFrame()
        self.__loaded: list = []


    @property
    def data(self) -> pd.DataFrame:
        return self.__data

    @data.setter
    def data(self, df: pd.DataFrame) -> None:
        self.__data = df


    @property
    def loaded(self) -> list:
        return self.__loaded

    @loaded.setter
    def loaded(self, loaded: list) -> None:
        self.__loaded = loaded


    @staticmethod
    def load(year: int, month: int, cacheurl) -> pd.DataFrame: 
        """
        se trata de un método interno y estático que utiliza el objeto cacheurl para acceder a los datos de multas del año year y mes month, a
        partir del cual se crea un dataframe de pandas que se será devuelto por la función.
        """
        url = get_url(year, month)
        
        # Request
        response = requests.get(url)

        # si la petición ha ido bien
        if response.status_code == 200:
            content = io.StringIO(response.text)
            df = pd.read_csv(content, sep =';', encoding = 'latin1')
            return df
        else:
            return None


    def clean_cache(self) -> None: 
        """
        método que borra todos los elementos de la caché.
        """
        self.cacheurl.clear()
        
    

    @staticmethod
    def clean(df: pd.DataFrame) -> None: 
        """
        método interno y estático que permite limpiar y normalizar los datos del dataframe df. La limpieza y preprocesamiento a realizar es
        la que se define en la sección ETAPA 1 (elimina espacios en blanco en columnas de texto, convierte columnas numéricas (VEL_CIRCULA,
        VEL_LIMITE, COORDENADA-X, COORDENADA-Y), crea una columna fecha a partir de ANIO, MES y HORA, etc.). Es posible que no todos los
        meses tengan las mismas columnas. Por ejemplo, en Mayo de 2019, las columnas son COORDENADA_X, COORDENADA_Y, en lugar de COORDENADA
        X, COORDENADA-Y.
        """
        ## PREGUNTA A - FET

        columna = "CALIFICACION"
        # Eliminar los espacios en blanco de la columna
        df[columna] = df[columna].apply(lambda row: row.strip(" "))
        
        ## PREGUNTA B - FET
        columnas = ["DESCUENTO", "HECHO-BOL", "DENUNCIANTE"]
        for columna in columnas:
            # Eliminar los espacios en blanco de la columna
            df[columna] = df[columna].apply(lambda row: row.strip(" "))

        ## PREGUNTA C - FET
        # Renombrar columnas eliminando los espacios en blanco
        df = df.rename(str.strip, axis="columns")

        # Se observa que hay caracteres como "\x00", que no se eliminan como espacios. Se eliminan estos caracteres y los espacios.
        columna = df.columns[-1]
        columna_nueva = df.columns[-1].replace('\x00', '').strip()
        df = df.rename({columna:columna_nueva}, axis="columns")

        ## PREGUNTA D - FET
        columnas = ["VEL_LIMITE", "VEL_CIRCULA"]
        for columna in columnas:
            # Convertir las columnas a tipo numérico
            df[columna] = pd.to_numeric(df[columna], errors="coerce")

        ## PREGUNTA E - FET
        columnas = ["COORDENADA-X", "COORDENADA-Y", "COORDENADA_X", "COORDENADA_Y"]
        for columna in columnas:
            # Solo cambia las columnas que están en el df
            if columna in df.columns:
                # Convertir las columnas a tipo numérico
                df[columna] = pd.to_numeric(df[columna], errors="coerce")

        # FET
        # Convertir a numérico
        df["HORA"] = pd.to_numeric(df["HORA"], errors="coerce")
        # Crear una columna fecha. Inciso. La hora viene como 20.25 (float). La hora será la parte entera (20) y los minutos serán el número 
        # decimal menos la parte entera de la hora, multiplicado por 100 | Ej: Minutos:(20.25-20)*100
        df["FECHA"] = df.apply(
            lambda row: datetime.datetime(
                year=int(row["ANIO"]),
                month=int(row["MES"]),
                day=1,
                hour=int(row["HORA"]),
                minute=int(round((row["HORA"] - int(row["HORA"])) * 100))
            ),
            axis=1
        )
        # Modificar el dataframe de forma que el índice sea el valor de la columna creada anteriormente
        df = df.set_index("FECHA")
        
        # Devuelve el dataframe
        return None


    def add(self, year: int, month: int|None = None) -> None: 
        """
        Permite añadir información de multas de un mes y un año concreto al dataset data actual. Evita duplicar meses ya cargados (si el mes
        ya existe, el método no hace nada). En caso contrario, se descargan los datos del año year y mes month usando el método load, se
        realiza la limpieza del dataframe descargado usando el método clean y se añade al dataset actual data. Este método tendrá que
        actualizar correctamente el atributo loaded. En el caso de que el parámetro month sea None, se descargarán los datos del año completo.
        """
        # to-do (cacheurl=None?)
        df = MadridFines.load(year=year, month=month, cacheurl=None)   # static method
        # Limpieza de datos
        self.clean(df)
        # Añadir dataset a data
        self.data = pd.concat([self.data, df], ignore_index=True)
        # Actualizar loaded indicando que se ha añadido un nuevo dataset (year, month)
        new_set = (year, month)
        self.loaded.append(new_set)

    
    # REVISAR CHAT
    def fines_hour(self, fig_name: str)-> None: 
        """
        método que genera un gráfico de líneas que muestra la evolución del número de multas a lo largo de las horas del día. Si hay varios
        meses cargados, dibuja una línea por cada mes. La función guarda el gráfico con nombre fig_name (por ejemplo evolucion_multas.png)
        """

        # Crear una columna con el mes y año
        self.data["MES"] = self.data["FECHA"].dt.to_period("M")

        # Contar el num. de multas por mes y hora
        fines = self.data.groupby(["MES", "HORA"]).size().reset_index(name="MULTAS")

        # Crear el grafico
        plt.figure(figsize=(12, 6))

        for month in fines["MES"].unique():
            month_data = fines[fines["MES"] == month]
            plt.plot(month_data["HORA"], month_data["MULTES"], marker="o", label=str(month))

        plt.title(fig_name)
        plt.xlabel("Hora")
        plt.ylabel("Número de multas")
        #plt.xticks(range(24))
        plt.legend(title="Mes")
        plt.grid(True, alpha=0.3)

        # Guardar el grafico
        plt.savefig(fig_name)
        plt.close()


    # REVISAR CHAT
    def fines_calification(self) -> pd.DataFrame: 
        """
        analiza la distribución de multas por calificación, mes y año. Devuelve un DataFrame con el número total de multas distinguiendo por
        tipo para cada uno de los meses.
        """

        # Crear una columna con el mes y el año
        self["MES"] = self["FECHA"].dt.to_period("M")

        # Contar las multas por mes y calificación
        fines = (
            self.groupby(["MES", "CALIFICACION"])
            .size()
            .unstack(fill_value=0)
        )

        return fines

    # REVISAR CHAT
    def total_payment(self) -> pd.DataFrame: 
        """
        método que genera un resumen con el importe total (máximo y mínimo) recaudado por mes y año. Una multa puede tener descuento por
        pronto pago del 50%, pero cabe la posibilidad de que el infractor no realice el pago en fecha para acojerse a dicho descuento.
        """

        # Crear una columna con el mes y el año
        self["MES"] = self["FECHA"].dt.to_period("M")

        # Calcular el importe total, máximo y mínimo por mes
        payment = (
            self.groupby("MES")["IMPORTE"]
            .agg(
                IMPORTE_TOTAL="sum",
                IMPORTE_MAXIMO="max",
                IMPORTE_MINIMO="min"
            )
            .reset_index()
        )

        # Calcular el importe con el descuento del 50%
        payment["TOTAL_CON_DESCUENTO"] = payment["IMPORTE_TOTAL"] * 0.5

        return payment
    
    def __str__(self):
        """
        """
        text = " , Data: " + str(self.data) + ' , Loaded: ' + str(self.loaded)
        return text


## EXCEPCIONES ##
class MadridError(Exception):
    """Excepción lanzada por errores en la caché.

    Atributos:        
        message -- explicación del error
    """

    def __init__(self, message):
        self.message = message
    

######## MAIN ########
if __name__ == '__main__':

    # Anio 2024, mes 9
    url = get_url(year=2024, month=9)
    print(f"La url obtenida por get_url es: {url}")

    m = MadridFines(app_name="Olomi", obsolescence=2)
    # to-do (cacheurl=None?)
    df = MadridFines.load(year=2024, month=9, cacheurl=None)   # static method
    MadridFines.clean(df)                                       # static method

    m.add(year=2024, month=9)
    print(m)

    #m.fines_hour(fig_name="test")
    print(m.total_payment())
