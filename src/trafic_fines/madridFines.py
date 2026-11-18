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
    Función que recibe como argumentos un mes (1–12) y un año
    y devuelve la URL del fichero CSV con los datos de multas.

    Args:
        year (int): Año de los datos que se quieren descargar.
        month (int): Mes de los datos que se quieren descargar (1-12).

    Returns:
        str: URL del fichero CSV correspondiente al mes y año indicados.

    Raises:
        MadridError: Si se produce un error al realizar la petición HTTP
            o si no se encuentra el recurso correspondiente.
        KeyError: Si el mes indicado no existe en MAPPING_MES.
    """

    # Realizamos la petición a la web
    extension = "dataset/210104-0-multas-circulacion-detalle/downloads"
    url = RAIZ + extension.lstrip("/")

    # Request
    response = requests.get(url)

    # Si la petición ha ido bien
    if response.status_code == 200:

        # Pasamos el contenido HTML a BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Buscamos el periodo correspondiente
        data_key = f"{year}-{MAPPING_MES[month]}"
        resources = soup.select(
            f'div.tracked-resource-item[data-key="{data_key}"]'
        )

        # Buscamos los resultados detallados
        for resource in resources:
            title = resource.select_one("a[title]")

            if title:
                title_text = title.get("title")

                if isinstance(title_text, str) and title_text.startswith("Detalle."):
                    link = resource.select_one("a.resource-url-analytics")

                    if link:
                        href = link.get("href")

                        if isinstance(href, str):
                            return RAIZ + href

    else:
        raise MadridError("Error al realizar la petición")

    # Si no se encuentra el recurso correspondiente
    raise MadridError(
        f"No se han encontrado datos para {month}/{year}"
    )
       

class MadridFines:

    def __init__(self, app_name, obsolescence) -> None:
        """
        Inicializa una instancia de MadridFines.

        Args:
            app_name (str): Nombre de la aplicación utilizado para identificar
                el espacio de almacenamiento de la caché.
            obsolescence (int): Tiempo de obsolescencia de los elementos
                almacenados en caché.

        Attributes:
            cacheurl (CacheURL): Objeto encargado de gestionar la caché de URLs.
            data (pd.DataFrame): DataFrame que contiene los datos de multas.
            loaded (list): Lista de tuplas (mes, año) de los datasets cargados.
        """
        self.cacheurl = CacheURL(app_name, obsolescence)
        self.__data: pd.DataFrame = pd.DataFrame()
        self.__loaded: list = []


    @property
    def data(self) -> pd.DataFrame:
        """
        Devuelve el DataFrame que contiene los datos de multas.

        Returns:
            pd.DataFrame: DataFrame con los datos cargados y procesados.
        """
        return self.__data

    @data.setter
    def data(self, df: pd.DataFrame) -> None:
        """
        Establece el DataFrame que contiene los datos de multas.

        Args:
            df (pd.DataFrame): DataFrame que se asignará al atributo data.
        """
        self.__data = df


    @property
    def loaded(self) -> list:
        """
        Devuelve la lista de datasets cargados.

        Returns:
            list: Lista de tuplas (mes, año) correspondientes a los datasets
                importados.
        """
        return self.__loaded

    @loaded.setter
    def loaded(self, loaded: list) -> None:
        """
        Establece la lista de datasets cargados.

        Args:
            loaded (list): Lista de tuplas (mes, año).
        """
        self.__loaded = loaded


    @staticmethod
    def load(year: int, month: int, cacheurl) -> pd.DataFrame:
        """
        Se trata de un método interno y estático que utiliza el objeto cacheurl para acceder a los datos de multas del año year y mes month, a
        partir del cual se crea un dataframe de pandas que se será devuelto por la función.

        Args:
            year (int): Año de los datos que se quieren cargar.
            month (int): Mes de los datos que se quieren cargar (1-12).
            cacheurl (CacheURL): Objeto encargado de descargar y almacenar
                el contenido de la URL en caché.

        Returns:
            pd.DataFrame: DataFrame con los datos del fichero CSV.

        Raises:
            MadridError: Si no se encuentra la URL correspondiente.
            Exception: Si se produce un error durante la descarga o lectura
                de los datos.
        """
        url = get_url(year, month)
        content = cacheurl.get(url)
        content = io.StringIO(content)
        df = pd.read_csv(content, sep =';', encoding = 'latin1', low_memory=False)
        return df


    def clean_cache(self) -> None:
        """
        Método que borra todos los elementos de la caché.

        Raises:
            Exception: Si se produce un error durante la eliminación
                de los elementos de la caché.
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

        Args:
            df (pd.DataFrame): DataFrame original que se desea limpiar.
                Se modifica directamente, sin generar una copia.

        Returns:
            None

        Raises:
            KeyError: Si falta alguna de las columnas necesarias para el
                procesamiento, como CALIFICACION, ANIO, MES o HORA.
            ValueError: Si algún valor no puede convertirse al formato
                de fecha esperado.
        """

        ## PREGUNTA A
        columna = "CALIFICACION"
        # Eliminar los espacios en blanco de la columna
        df[columna] = df[columna].apply(lambda row: row.strip(" "))
        
        ## PREGUNTA B
        columnas = ["DESCUENTO", "HECHO-BOL", "DENUNCIANTE"]
        for columna in columnas:
            # Eliminar los espacios en blanco de la columna
            df[columna] = df[columna].apply(lambda row: row.strip(" "))

        ## PREGUNTA C
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

        ## PREGUNTA D
        columnas = ["VEL_LIMITE", "VEL_CIRCULA"]
        for columna in columnas:
            # Convertir las columnas a tipo numérico
            df[columna] = pd.to_numeric(df[columna], errors="coerce")

        ## PREGUNTA E
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


    def add(self, year: int, month: int | None = None) -> None:
        """
        Permite añadir información de multas de un mes y un año concreto al dataset data actual. Evita duplicar meses ya cargados (si el mes
        ya existe, el método no hace nada). En caso contrario, se descargan los datos del año year y mes month usando el método load, se
        realiza la limpieza del dataframe descargado usando el método clean y se añade al dataset actual data. Este método tendrá que
        actualizar correctamente el atributo loaded. En el caso de que el parámetro month sea None, se descargarán los datos del año completo.

        Args:
            year (int): Año de los datos que se quieren añadir.
            month (int | None): Mes que se quiere añadir (1-12).
                Si es None, se solicita la descarga del año completo.

        Returns:
            None

        Raises:
            NotImplementedError: Si month es None, ya que la descarga
                del año completo todavía no está implementada.
            MadridError: Si no se encuentra el recurso correspondiente.
            KeyError: Si el mes indicado no es válido.
        """

        # Comprobar si el mes y año, ya estaban cargados
        for tup in self.loaded:
            if month==tup[0] and year==tup[1]:
                return print("El dataset ya estaba previamente importado")
        
        # Sino, importarlo
        if month is None:
            raise NotImplementedError(
                "La descarga del año no está implementada"
            )
        
        df = MadridFines.load(year=year, month=month, cacheurl=self.cacheurl)   # static method
        # Limpieza de datos
        self.clean(df)
        # Añadir dataset a data
        self.data = pd.concat([self.data, df])
        # Actualizar loaded indicando que se ha añadido un nuevo dataset (year, month)
        new_set = (month, year)
        self.loaded.append(new_set)

    
    def fines_hour(self, fig_name: str) -> None:
        """
        Método que genera un gráfico de líneas que muestra la evolución del número de multas a lo largo de las horas del día. Si hay varios
        meses cargados, dibuja una línea por cada mes. La función guarda el gráfico con nombre fig_name (por ejemplo evolucion_multas.png).

        Args:
            fig_name (str): Nombre o ruta del fichero donde se guardará
                el gráfico generado.

        Returns:
            None

        Raises:
            ValueError: Si el índice del DataFrame no puede interpretarse
                como fechas.
        """

        # Asegurar que el índice es un DatetimeIndex
        index = pd.DatetimeIndex(self.data.index)
        
        # Agrupar for mes, año y hora. Entonces, contar las multas.
        fines = (
            self.data
            .groupby([index.month, index.year, index.hour])
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

        Returns:
            pd.DataFrame: Tabla con los recuentos de multas por calificación,
                agrupados por mes y año.
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

        Returns:
            pd.DataFrame: DataFrame con dos columnas:
                - PRECIO_MAX: Importe total sin aplicar descuentos.
                - PRECIO_MIN: Importe total aplicando el descuento del 50%
                a las multas que corresponda.
            El índice contiene el mes y el año.
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
        Devuelve una representación textual del objeto MadridFines.

        Returns:
            str: Representación del DataFrame de multas y de los datasets
                que se han cargado.
        """
        text = " , Data: " + str(self.data) + ' , Loaded: ' + str(self.loaded)
        return text


## EXCEPCIONES ##
class MadridError(Exception):
    """
    Excepción lanzada cuando se producen errores relacionados con
    la descarga o localización de los datos de multas de Madrid.

    Args:
        message (str): Descripción del error producido.

    Attributes:
        message (str): Mensaje explicativo del error.
    """

    def __init__(self, message):
        self.message = message


#################    MAIN     ####################
# No se incluye en el pytest -> # pragma: no cover
if __name__ == '__main__': # pragma: no cover

    # Crear objeto de la classe MadridFines
    m = MadridFines(app_name="madridfines_test", obsolescence=2)

    # Borrar datos de caché
    #MadridFines.clean(df)                                       # static method

    # Limpiar cache
    #m.clean_cache()

    # Cargar varios datasets
    m.add(year=2024, month=9)
    m.add(year=2024, month=10)
    m.add(year=2024, month=11)

    # Varios métodos
    m.fines_hour(fig_name="test")
    print("FINES CALIFICATION")
    print(m.fines_calification())
    print(m.total_payment())
