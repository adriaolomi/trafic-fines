from pathlib import Path
import shutil
import time
import hashlib
import requests
import io

CACHE_DIR = Path.home() / ".my_cache"

class Cache:

    def __init__(self, app_name, obsolescence) -> None:
        """
        Inicializa una caché asociada a una aplicación concreta.

        Args:
            app_name (str): Nombre asociado a la aplicación. Este atributo
                se utilizará para crear una subcarpeta dentro de CACHE_DIR.
            obsolescence (int): Número de días durante los cuales los datos
                de la caché se considerarán válidos.
        """
        self.__app_name = app_name
        self.__cache_dir = CACHE_DIR / app_name
        self.__obsolescence = obsolescence

    
    @property
    def app_name(self) -> str:
        """
        Nombre asociado a la aplicación concreta. Este atributo se usará para
        crear una subcarpeta dentro de la carpeta CACHE_DIR. De esta forma,
        cada aplicación tendrá una carpeta dentro de CACHE_DIR para almacenar
        sus datos.

        Returns:
            str: Nombre de la aplicación.
        """
        return self.__app_name 
        
    @property
    def cache_dir(self) -> Path:
        """
        String con la ruta completa de la subcarpeta que usará la aplicación
        para almacenar sus datos.

        Returns:
            Path: Ruta del directorio de caché.
        """
        return self.__cache_dir

    @property
    def obsolescence(self) -> int:
        """
        Indica el número de días que consideraremos que los datos de la caché
        siguen siendo válidos.

        Returns:
            int: Número de días de obsolescencia.
        """
        return self.__obsolescence 


    def set(self, name: str, data: str) -> None:
        """
        Almacena en cache_dir los datos en data con el nombre name.

        Args:
            name (str): Nombre del fichero donde se almacenarán los datos.
            data (str): Datos que se desean almacenar en el fichero.

        Raises:
            OSError: Si se produce un error al crear el directorio o escribir
                el fichero.
        """
        # Crear los directorios de cache, si no existen previamente
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Escribir en fichero
        with open(self.cache_dir / name, 'w') as f:
            f.write(data)

            
    def exists(self, name: str) -> bool:
        """
        Comprueba si ya existe un fichero con el nombre indicado en el
        directorio de caché.

        Args:
            name (str): Nombre del fichero que se desea comprobar.

        Returns:
            bool: True si el fichero existe, False en caso contrario.
        """
        full_path = self.cache_dir / name
        if full_path.is_file():
            return True
        else:
            return False

        
    def load(self, name: str) -> str:
        """
        Método que recupera los datos almacenados en la caché, con el nombre
        name. Si no hay ningún dato asociado deberá lanzar la excepción
        CacheError.

        Args:
            name (str): Nombre del fichero que se desea recuperar. Debe
                representar únicamente el nombre del fichero, no la ruta
                completa.

        Returns:
            str: Datos almacenados en el fichero.

        Raises:
            CacheError: Si el archivo no existe en la caché.
            OSError: Si se produce un error al leer el fichero.
        """
        if self.exists(name):
            with open(self.cache_dir / name, 'r') as file:
                return file.read()
        else:
            raise CacheError(f"El archivo {name} no existe en la cache {self.app_name} con ruta {self.cache_dir}!")

        
    def how_old(self, name: str) -> float:
        """
        Método que nos dirá la edad en milisegundos del fichero almacenado
        en la caché con el nombre indicado. Esto sirve para comprobar si el
        fichero está caducado según el valor de obsolescence.

        Args:
            name (str): Nombre del fichero cuya antigüedad se desea calcular.

        Returns:
            float: Antigüedad del fichero en milisegundos.

        Raises:
            FileNotFoundError: Si el fichero no existe.
        """
        full_path = self.cache_dir / name
        creation_time = full_path.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - creation_time
        return age_seconds * 1000

    
    def delete(self, name: str) -> None:
        """
        Método que borra de la caché el fichero con nombre name. Si no existe,
        no se lanza ninguna excepción.

        Args:
            name (str): Nombre del fichero que se desea eliminar.

        Raises:
            OSError: Si se produce un error al eliminar el fichero.
        """
        # Si el fichero existe, se elimina
        full_path = self.cache_dir / name
        if full_path.is_file():
            full_path.unlink()
        
    def clear(self) -> None:
        """
        Método que borra todos los elementos de la caché.

        Raises:
            OSError: Si se produce un error al eliminar el directorio de caché.
        """
        # Si el directorio existe, se elimina
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
    
    def __str__(self) -> str:
        """
        Representación de la configuración de la caché.

        Returns:
            str: Cadena con el nombre de la aplicación, la ruta del directorio
                de caché y el periodo de obsolescencia.
        """
        text = "AppName: " + self.app_name + " , CacheDir: " + str(self.cache_dir) + ' , Obsolescence: ' + str(self.obsolescence)
        return text

        
class CacheURL(Cache):

    def __init__(self, app_name, obsolescence):
        """
        Inicializa una caché asociada a URLs y hereda la configuración
        de la clase Cache.

        Args:
            app_name (str): Nombre asociado a la aplicación.
            obsolescence (int): Número de días durante los cuales los datos
                de la caché se considerarán válidos.
        """
        super().__init__(app_name, obsolescence)

    
    def get(self, url: str, **kwargs) -> str:
        """
        Este método va a realizar un get a la url indicada. Este método
        consultará si tiene ya un objeto asociado a esta petición, si no lo
        tiene realizará la petición correspondiente, guardará el resultado
        en la caché. Devolverá el objeto correspondiente.

        Args:
            url (str): Dirección URL del recurso que se desea consultar.
            **kwargs: Parámetros adicionales asociados a la petición.

        Returns:
            str: Contenido de la respuesta HTTP.

        Raises:
            CacheError: Si se produce un error HTTP o un error de conexión.
        """
        # Si el objeto existe, lo devuelve
        if self.exists(url):
            return self.load(url)
        
        # Sino, lo descarga de internet
        else:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
                    super().set(name=url_hashed, data=response.text)
                    return self.load(url)
                else:
                    raise CacheError(
                        f"Error HTTP {response.status_code} al consultar {url}"
                    )
            except requests.RequestException as e:
                raise CacheError(f"Error de conexión con {url}: {e}") from e

    # Redefinición de la clase padre  
    def exists(self, url: str, **kwargs) -> bool:
        """
        Comprueba si ya existe un fichero con el nombre indicado en el
        directorio de caché.

        Args:
            url (str): Dirección URL del recurso que se desea comprobar.
            **kwargs: Parámetros adicionales utilizados para identificar
                la petición.

        Returns:
            bool: True si el contenido de la URL existe en caché,
                False en caso contrario.
        """
        url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
        return super().exists(name=url_hashed)

    
    # Redefinición de la clase padre 
    def load(self, url: str, **kwargs) -> str:
        """
        Método que recupera los datos almacenados en la caché, con el nombre
        name. Si no hay ningún dato asociado deberá lanzar la excepción
        CacheError.

        Args:
            url (str): Dirección URL del recurso que se desea recuperar.
            **kwargs: Parámetros adicionales utilizados para identificar
                la petición.

        Returns:
            str: Contenido almacenado en la caché.

        Raises:
            CacheError: Si el contenido de la URL no existe en la caché.
            OSError: Si se produce un error al leer el fichero.
        """
        if self.exists(url):
            url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()   
            with open(self.cache_dir / url_hashed, 'r') as file:
                return file.read()
        else:
            raise CacheError(f"El archivo {url} no existe en la cache {self.app_name} con ruta {self.cache_dir}!")

    
    # Redefinición de la clase padre 
    def how_old(self, url: str, **kwargs) -> float:
        """
        Método que nos dirá la edad en milisegundos del fichero almacenado
        en la caché con el nombre indicado. Esto sirve para comprobar si el
        fichero está caducado según el valor de obsolescence.

        Args:
            url (str): Dirección URL del recurso cuya antigüedad se desea
                calcular.
            **kwargs: Parámetros adicionales utilizados para identificar
                la petición.

        Returns:
            float: Antigüedad del recurso en caché en milisegundos.

        Raises:
            FileNotFoundError: Si el recurso no existe en la caché.
        """
        url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
        return super().how_old(name=url_hashed)
    

    # Redefinición de la clase padre   
    def delete(self, url: str, **kwargs) -> None:
        """
        Método que borra de la caché el fichero con nombre name. Si no existe,
        no se lanza ninguna excepción.

        Args:
            url (str): Dirección URL del recurso que se desea eliminar.
            **kwargs: Parámetros adicionales utilizados para identificar
                la petición.

        Raises:
            OSError: Si se produce un error al eliminar el fichero.
        """
        url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
        return super().delete(name=url_hashed)
    

    def __str__(self) -> str:
        """
        Representación de la configuración de la clase Caché URL.

        Returns:
            str: Representación textual de la configuración de la caché.
        """
        text = super().__str__()
        return text



## EXCEPCIONES ##
class CacheError(Exception):
    """
    Excepción lanzada por errores en la caché.

    Args:
        message (str): Explicación del error.

    Attributes:
        message (str): Mensaje descriptivo del error.
    """

    def __init__(self, message):
        self.message = message

    
#################    MAIN     ####################
# No se incluye en el pytest -> # pragma: no cover
if __name__ == '__main__': # pragma: no cover

    # Crear instancia 
    c = CacheURL("cache_test", 12)
    print(str(c))

    # Request GET
    raiz = "https://datos.madrid.es/"
    url_diciembre_24 = "dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv" 
    url = raiz + url_diciembre_24.lstrip("/")
    c.get(url)

    # Cantidad de ms que lleva en caché un fichero
    print(c.how_old(url))