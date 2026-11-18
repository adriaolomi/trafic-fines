#from .cache import CacheURL
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import requests
import io

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

    try:
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
        cacheurl: CacheURL(app_name, obsolescence)
        data: pd.DataFrame = []
        loaded: tuple = []

    @staticmethod
    def load(year: int, month: int, cacheurl) -> pd.DataFrame: 
        """
        se trata de un método interno y estático que utiliza el objeto cacheurl para acceder a los datos de multas del año year y mes month, a
        partir del cual se crea un dataframe de pandas que se será devuelto por la función.
        """
        url = get_url(year, month)
        print(url)
        
        # Request
        response = requests.get(url)

        # si la petición ha ido bien
        if response.status_code == 200:
            content = io.StringIO(response.text)
            multas_df = pd.read_csv(content, sep =';', encoding = 'latin1',low_memory=False)
            return multas_df
        else:
            return None

    def clean_cache() -> None: 
        """
        método que borra todos los elementos de la caché.
        """
        
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
            multas[columna] = multas[columna].apply(lambda row: row.strip(" "))

        ## PREGUNTA C - FET
        # Renombrar columnas eliminando los espacios en blanco
        multas = multas.rename(str.strip, axis="columns")

        # Se observa que hay caracteres como "\x00", que no se eliminan como espacios. Se eliminan estos caracteres y los espacios.
        columna = multas.columns[-1]
        columna_nueva = multas.columns[-1].replace('\x00', '').strip()
        multas = multas.rename({columna:columna_nueva}, axis="columns")

        ## PREGUNTA D - FET
        columnas = ["VEL_LIMITE", "VEL_CIRCULA"]
        for columna in columnas:
            # Convertir las columnas a tipo numérico
            multas[columna] = pd.to_numeric(multas[columna], errors="coerce")

        ## PREGUNTA E - FET
        columnas = ["COORDENADA-X", "COORDENADA-Y"]
        for columna in columnas:
            # Convertir las columnas a tipo numérico
            multas[columna] = pd.to_numeric(multas[columna], errors="coerce")

        # FET
        # Convertir a numérico
        multas["HORA"] = pd.to_numeric(multas["HORA"], errors="coerce")
        # Crear una columna fecha. Inciso. La hora viene como 20.25 (float). La hora será la parte entera (20) y los minutos serán el número 
        # decimal menos la parte entera de la hora, multiplicado por 100 | Ej: Minutos:(20.25-20)*100
        multas["fecha"] = multas.apply(
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
        multas = multas.set_index("fecha")

    def add(self, year: int, month: int|None = None) -> None: 
        """
        Permite añadir información de multas de un mes y un año concreto al dataset data actual. Evita duplicar meses ya cargados (si el mes
        ya existe, el método no hace nada). En caso contrario, se descargan los datos del año year y mes month usando el método load, se
        realiza la limpieza del dataframe descargado usando el método clean y se añade al dataset actual data. Este método tendrá que
        actualizar correctamente el atributo loaded. En el caso de que el parámetro month sea None, se descargarán los datos del año completo.
        """
    
    def fines_hour(self, fig_name: str)-> None: 
        """
        método que genera un gráfico de líneas que muestra la evolución del número de multas a lo largo de las horas del día. Si hay varios
        meses cargados, dibuja una línea por cada mes. La función guarda el gráfico con nombre fig_name (por ejemplo evolucion_multas.png)
        """
    
    def fines_calification(self)-> pd.DataFrame: 
        """
        analiza la distribución de multas por calificación, mes y año. Devuelve un DataFrame con el número total de multas distinguiendo por
        tipo para cada uno de los meses.
        """
    
    def total_payment(self) -> pd.DataFrame: 
        """
        método que genera un resumen con el importe total (máximo y mínimo) recaudado por mes y año. Una multa puede tener descuento por
        pronto pago del 50%, pero cabe la posibilidad de que el infractor no realice el pago en fecha para acojerse a dicho descuento.
        """


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

    # Anio 2024, mes 11
    url = get_url(year=2024, month=11)
    print(f"La url obtenida por get_url es: {url}")

    m = MadridFines(app_name="Olomi", obsolescence=2)
    print(m.load(year=2024, month=11, cacheurl=None))