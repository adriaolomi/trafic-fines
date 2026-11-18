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

        # Se observa que en los <div tracked-resource-item se organizan los periodos con los data-keys {year}-{month}
        data_key = f"{year}-{MAPPING_MES[month]}"
        resources = soup.select(f'div.tracked-resource-item[data-key="{data_key}"]')

        # Se observa que hay datos: 1) agrupados y 2) detalle
        for resource in resources:
            title = resource.select_one("a[title]")
            # Se seleccionan los resutlados detallados y se devuelve la url, contenida en el resource-url-analytics
            if title and title["title"].startswith("Detalle."):
                link = resource.select_one("a.resource-url-analytics")
                if link:
                    return RAIZ + link["href"]
        
    # si la petición ha ido mal 
    else:
        raise MadridError("Error al realizar la petición")
       

class MadridFines:

    def __init__(self, app_name, obsolescence) -> None:
        self.cacheurl = CacheURL(app_name, obsolescence)
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
        Se trata de un método interno y estático que utiliza el objeto cacheurl para acceder a los datos de multas del año year y mes month, a
        partir del cual se crea un dataframe de pandas que se será devuelto por la función.
        """
        url = get_url(year, month)
        content = cacheurl.get(url)
        content = io.StringIO(content)
        df = pd.read_csv(content, sep =';', encoding = 'latin1')
        return df


    def clean_cache(self) -> None: 
        """
        Método que borra todos los elementos de la caché.
        """
        self.cacheurl.clear()
        
    

    @staticmethod
    def clean(df: pd.DataFrame) -> None: 
        """
        Método interno y estático que permite limpiar y normalizar los datos del dataframe df. La limpieza y preprocesamiento a realizar es
        la que se define en la sección ETAPA 1 (elimina espacios en blanco en columnas de texto, convierte columnas numéricas (VEL_CIRCULA,
        VEL_LIMITE, COORDENADA-X, COORDENADA-Y), crea una columna fecha a partir de ANIO, MES y HORA, etc.). Es posible que no todos los
        meses tengan las mismas columnas. Por ejemplo, en Mayo de 2019, las columnas son COORDENADA_X, COORDENADA_Y, en lugar de COORDENADA
        X, COORDENADA-Y.
        """

        print("Entrando al método clean...")

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
        # df = df.rename(str.strip, axis="columns")
        df.columns = df.columns.str.strip()

        # Se observa que hay caracteres como "\x00", que no se eliminan como espacios. Se eliminan estos caracteres y los espacios.
        #columna = df.columns[-1]
        #columna_nueva = df.columns[-1].replace('\x00', '').strip()
        #df = df.rename({columna:columna_nueva}, axis="columns")

        df.columns = [
            col.replace("\x00", "") for col in df.columns
        ]

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
        #df = df.set_index("FECHA")
        df.index = df["FECHA"]
        
        # Devuelve None
        return None

    # REVISAR
    def add(self, year: int, month: int|None = None) -> None: 
        """
        Permite añadir información de multas de un mes y un año concreto al dataset data actual. Evita duplicar meses ya cargados (si el mes
        ya existe, el método no hace nada). En caso contrario, se descargan los datos del año year y mes month usando el método load, se
        realiza la limpieza del dataframe descargado usando el método clean y se añade al dataset actual data. Este método tendrá que
        actualizar correctamente el atributo loaded. En el caso de que el parámetro month sea None, se descargarán los datos del año completo.
        """
        # Comprobar si el mes y año, ya estaban cargados
        for tup in self.loaded:
            if month==tup[0] and year==tup[1]:
                return print("El dataset ya estaba previamente importado")
        
        # Sino, importarlo
        df = MadridFines.load(year=year, month=month, cacheurl=self.cacheurl)   # static method
        # Limpieza de datos
        self.clean(df)
        # Añadir dataset a data
        self.data = pd.concat([self.data, df])
        # Actualizar loaded indicando que se ha añadido un nuevo dataset (year, month)
        new_set = (month, year)
        self.loaded.append(new_set)

    
    def fines_hour(self, fig_name: str)-> None: 
        """
        Método que genera un gráfico de líneas que muestra la evolución del número de multas a lo largo de las horas del día. Si hay varios
        meses cargados, dibuja una línea por cada mes. La función guarda el gráfico con nombre fig_name (por ejemplo evolucion_multas.png)
        """

        # Agrupar for mes, año y hora. Entonces, contar las multas.
        fines = (
            self.data
            .groupby([self.data.index.month, self.data.index.year, self.data.index.hour])
            .size()
            .rename_axis(["MES", "ANIO", "HORA"])
            .reset_index(name="MULTAS")
        )

        # Cada linea dibujada corresponde a un mes y año diferentes
        for (year, month), month_data in fines.groupby(["ANIO", "MES"]):

            plt.plot(
                month_data["HORA"],
                month_data["MULTAS"],
                marker="o",
                label=f"{year}-{month}"
            )

        # Mostrar ejes, titulos y leyenda
        plt.xlabel("Hora del día")
        plt.ylabel("Número de multas")
        plt.title("Evolución del número de multas por hora")
        plt.legend()

        # Guardar y cerrar
        plt.savefig(fig_name)
        plt.close()


    def fines_calification(self) -> pd.DataFrame: 
        """
        Analiza la distribución de multas por calificación, mes y año. Devuelve un DataFrame con el número total de multas distinguiendo por
        tipo para cada uno de los meses.
        """

        # Agrupar por mes y año y contar las ocurrencias de cada tipo de CALIFICACION. Los valores faltantes se interpretan como 0.
        fines = self.data.pivot_table(
            index=["MES", "ANIO"],
            columns="CALIFICACION",
            aggfunc="size",
            fill_value=0
        )

        return fines


    def total_payment(self) -> pd.DataFrame: 
        """
        Método que genera un resumen con el importe total (máximo y mínimo) recaudado por mes y año. Una multa puede tener descuento por
        pronto pago del 50%, pero cabe la posibilidad de que el infractor no realice el pago en fecha para acojerse a dicho descuento.
        """
        
        # El máximo = Suma del importe de todas las multas del mes y año.
        # 1) Agrupar por mes y año; 2) Seleccionar la columna IMP_BOL; 3) Suma de los elementos de dicha columna
        payment_max = (
            self.data.groupby(["MES","ANIO"])["IMP_BOL"]
            .agg(PRECIO_MAX="sum")
        )
        
        # El mínimo será dependerá de si la multa tiene descuento o no. 
        # Por tanto, se calculará como: importe de las multas sin descuento + (importe de las multas con descuento)/2)
        # 1) Agrupar por mes y año; 2) Seleccionar la columna IMP_BOL; 
        # 3) Multiplicar el valor de IMP_BOL por 0.5 si en la columna DESCUENTO hay "SI", sino se queda el mismo importe.
        payment_min = (
            self.data.groupby(["MES", "ANIO"])
            .apply(
                lambda group: (
                    group["IMP_BOL"]
                    .where(
                        group["DESCUENTO"] != "SI",
                        group["IMP_BOL"] * 0.5
                    )
                    .sum()
                )
            )
            .rename("PRECIO_MIN")
        )

        payment = pd.concat([payment_min, payment_max], axis=1)

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

    # Crear objeto de la classe MadridFines
    m = MadridFines(app_name="Olomi", obsolescence=2)

    # Cargar varios datasets
    #df = MadridFines.load(year=2024, month=9, cacheurl=m.cacheurl)    # static method
    #df = MadridFines.load(year=2024, month=10, cacheurl=m.cacheurl)   # static method
    #df = MadridFines.load(year=2024, month=11, cacheurl=m.cacheurl)   # static method
    #MadridFines.clean(df)                                       # static method

    # Limpiar cache
    #m.clean_cache()

    # Cargar varios datasets
    m.add(year=2024, month=9)
    m.add(year=2024, month=10)
    m.add(year=2024, month=11)
    #print(m)

    #print(m.data.columns)

    m.fines_hour(fig_name="test")
    #print("FINES CALIFICATION")
    #print(m.fines_calification())
    #print(m.total_payment())
