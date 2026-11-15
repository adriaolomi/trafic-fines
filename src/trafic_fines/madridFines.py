from .cache import CacheURL
import pandas as pd

RAIZ = "https://datos.madrid.es/"

def get_url(year: int, month: int) -> str
    """
    Función que recibe como argumentos un mes (1–12) y un año (con cuatro cifras, ej. 2024) y devuelva la URL del fichero CSV con los datos de multas correspondiente a ese mes y año, disponible en el portal de datos abiertos del Ayuntamiento de Madrid. Si el mes y año no están en la página se debe producir una excepción. Se recomienda resolver este ejercicio realizando scraping. Usar la librería requests para hacer la petición HTTP y recuperar el HTML de la página.
    """

class MadridFines:

    def __init__(self, app_name, obsolence) -> None:
        cacheurl: CacheURL(app_name, obsolence),
        data: pd.DataFrame = [],
        loaded: tuple = [],

    def load(year: int, month: int, cacheurl) -> pd.DataFrame: 
        """
        se trata de un método interno y estático que utiliza el objeto cacheurl para acceder a los datos de multas del año year y mes month, a
        partir del cual se crea un dataframe de pandas que se será devuelto por la función.
        """

    def clean_cache() -> None: 
        """
        método que borra todos los elementos de la caché.
        """
        
    def clean(df: pd.DataFrame) -> None: 
        """
        método interno y estático que permite limpiar y normalizar los datos del dataframe df. La limpieza y preprocesamiento a realizar es la que se define en la sección ETAPA 1 (elimina espacios en blanco en columnas de texto, convierte columnas numéricas (VEL_CIRCULA, VEL_LIMITE, COORDENADA-X, COORDENADA-Y), crea una columna fecha a partir de ANIO, MES y HORA, etc.). Es posible que no todos los meses tengan las mismas columnas. Por ejemplo, en Mayo de 2019, las columnas son COORDENADA_X, COORDENADA_Y, en lugar de COORDENADA-X, COORDENADA-Y.
        """

    def add(self, year: int, month: int|None = None) -> None: 
        """
        Permite añadir información de multas de un mes y un año concreto al dataset data actual. Evita duplicar meses ya cargados (si el mes ya existe, el método no hace nada). En caso contrario, se descargan los datos del año year y mes month usando el método load, se realiza la limpieza del dataframe descargado usando el método clean y se añade al dataset actual data. Este método tendrá que actualizar correctamente el atributo loaded. En el caso de que el parámetro month sea None, se descargarán los datos del año completo.
        """
    
    def fines_hour(self, fig_name: str)-> None: 
        """
        método que genera un gráfico de líneas que muestra la evolución del número de multas a lo largo de las horas del día. Si hay varios meses cargados, dibuja una línea por cada mes. La función guarda el gráfico con nombre fig_name (por ejemplo evolucion_multas.png)
        """
    
    def fines_calification(self)-> pd.DataFrame: 
        """
        analiza la distribución de multas por calificación, mes y año. Devuelve un DataFrame con el número total de multas distinguiendo por tipo para cada uno de los meses.
        """
    
    def total_payment(self) -> pd.DataFrame 
        """
        método que genera un resumen con el importe total (máximo y mínimo) recaudado por mes y año. Una multa puede tener descuento por pronto pago del 50%, pero cabe la posibilidad de que el infractor no realice el pago en fecha para acojerse a dicho descuento.
        """